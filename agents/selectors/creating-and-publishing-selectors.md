# Creating and Publishing Selectors

This guide walks you through everything you need to build a Selector from scratch and publish it to Amesa Orchestration Studio using the `amesa` CLI. By the end, you will have a working selector packaged as an artifact and registered in the AMESA registry.

---

## What Is a Selector?

A **Selector** is a meta-skill that decides which child skill executes at each timestep. When your agent has multiple skills, the selector receives sensor observations and outputs an integer index that determines which child skill runs next. The selected child's action reaches the simulator — the selector's index never does.

Selectors enable **orchestrated agents**: agents that decompose complex behavior into specialized sub-skills and switch between them dynamically.

```
Agent
└── SkillSelector ("my-selector")      ← chooses which skill runs
    ├── Skill-A  ("stabilize")          ← leaf skill
    ├── Skill-B  ("accelerate")         ← leaf skill
    └── Skill-C  ("recover")            ← leaf skill
```

The selector outputs `0` → Skill-A runs. `1` → Skill-B runs. `2` → Skill-C runs.

### Two Types of Selector

| Type                        | When to use                                                                                                                               |
| --------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| **Controller** (rule-based) | The selection logic is deterministic — you can write an explicit rule for which skill to choose given current sensor values.              |
| **Teacher** (RL-trained)    | You want the agent to _learn_ when to switch skills. The selector trains as an RL policy with its own reward signal and success criteria. |

Selectors use the same `SkillController` and `SkillTeacher` interfaces as regular skills. The key difference is what the action means: **for a selector, the action is an integer index**, not a command to the simulator.

---

## Step 1: Understand the Selector Interface

### Controller Selector

Implement `SkillController` with `compute_action` returning an integer index:

```python
from typing import Dict, List
from amesa_core import SkillController

class MySelector(SkillController):

    def __init__(self):
        pass

    async def filtered_sensor_space(self, obs_spec) -> List[str]:
        # Which sensors does the selection logic need to read?
        ...

    async def compute_action(self, obs_spec: Dict, action) -> List[int]:
        # Return [index] where index selects the child skill to run
        # 0 → first registered child, 1 → second, etc.
        ...

    async def compute_success_criteria(self, obs_spec: Dict, action) -> bool:
        ...

    async def compute_termination(self, obs_spec: Dict, action) -> bool:
        ...
```

### Teacher Selector

Implement `SkillTeacher` with `compute_reward` driving the selection policy:

```python
from typing import Dict, List
from amesa_core import SkillTeacher

class MySelector(SkillTeacher):

    def __init__(self):
        pass

    async def filtered_sensor_space(self) -> List[str]:
        ...

    async def compute_reward(self, transformed_sensors: Dict, action, sim_reward: float) -> float:
        # Reward signal that teaches the selector when to switch skills
        ...

    async def compute_success_criteria(self, transformed_sensors: Dict, action) -> bool:
        ...

    async def transform_action(self, transformed_sensors: Dict, action):
        # Return the action unchanged — the selector's action is an index
        return action

    async def compute_termination(self, transformed_sensors: Dict, action) -> bool:
        return False
```

> **All methods are async.** Declare every method with `async def`.

> **`__init__` must accept zero required arguments.** The framework re-creates the selector at the start of every episode.

---

## Step 2: Write Your Selector

---

### Option A: Controller Selector (Rule-Based)

The example below selects between three process control skills based on a `process_state` sensor: a startup skill, a steady-state skill, and a recovery skill.

```python
# process_selector/controller.py

from typing import Dict, List
from amesa_core import SkillController

# Skill index mapping (matches registration order in the agent)
SKILL_STARTUP = 0
SKILL_STEADY_STATE = 1
SKILL_RECOVERY = 2

# process_state thresholds
WARMUP_THRESHOLD = 0.2     # below this → still starting up
FAULT_THRESHOLD = 0.05     # below this → fault recovery needed


class ProcessSelector(SkillController):
    """
    Rule-based selector for a three-skill process control agent.
    Chooses startup, steady-state, or recovery based on process_state.
    """

    def __init__(self):
        pass

    async def filtered_sensor_space(self, obs_spec) -> List[str]:
        return ["process_state", "temperature", "pressure"]

    async def compute_action(self, obs_spec: Dict, action) -> List[int]:
        state = obs_spec["process_state"]

        if state < FAULT_THRESHOLD:
            return [SKILL_RECOVERY]
        elif state < WARMUP_THRESHOLD:
            return [SKILL_STARTUP]
        else:
            return [SKILL_STEADY_STATE]

    async def compute_success_criteria(self, obs_spec: Dict, action) -> bool:
        return obs_spec["process_state"] >= 0.9

    async def compute_termination(self, obs_spec: Dict, action) -> bool:
        return False
```

---

### Option B: Teacher Selector (RL-Trained)

The example below trains the selector with reinforcement learning. The reward encourages it to keep `process_state` high, and the RL policy learns which skill combinations achieve that over time.

```python
# process_selector/teacher.py

from typing import Dict, List
from amesa_core import SkillTeacher


class ProcessSelector(SkillTeacher):
    """
    RL-trained selector for a three-skill process control agent.
    Reward drives the policy to maintain high process_state.
    """

    SUCCESS_THRESHOLD = 0.9
    FAIL_THRESHOLD = 0.05

    def __init__(self):
        pass

    async def filtered_sensor_space(self) -> List[str]:
        return ["process_state", "temperature", "pressure"]

    async def compute_reward(self, transformed_sensors: Dict, action, sim_reward: float) -> float:
        # Reward the selector for keeping process_state high
        return float(transformed_sensors["process_state"])

    async def compute_success_criteria(self, transformed_sensors: Dict, action) -> bool:
        return transformed_sensors["process_state"] >= self.SUCCESS_THRESHOLD

    async def compute_termination(self, transformed_sensors: Dict, action) -> bool:
        return transformed_sensors["process_state"] < self.FAIL_THRESHOLD

    async def transform_action(self, transformed_sensors: Dict, action):
        # The selector's action is a skill index — return it unchanged
        return action
```

---

## Step 3: Create the Artifact Directory

### Using the CLI Scaffold (Recommended)

For a **controller** selector:

```bash
amesa selector new \
  --name process-selector \
  --type controller \
  --description "Rule-based selector for three-skill process control agent" \
  --location ./
```

For a **teacher** selector:

```bash
amesa selector new \
  --name process-selector \
  --type teacher \
  --description "RL-trained selector for three-skill process control agent" \
  --location ./
```

Both create:

```text
process-selector/
  process_selector/
    __init__.py        ← empty; required
    controller.py      ← or teacher.py, depending on type
  pyproject.toml
```

### Creating Manually

```bash
mkdir -p process-selector/process_selector
touch process-selector/process_selector/__init__.py
touch process-selector/process_selector/controller.py   # or teacher.py
touch process-selector/pyproject.toml
```

### Naming Rules

| Layer               | Convention    | Example                         |
| ------------------- | ------------- | ------------------------------- |
| Outer directory     | kebab-case    | `process-selector`              |
| Inner Python module | snake_case    | `process_selector`              |
| Source file         | by convention | `controller.py` or `teacher.py` |
| `__init__.py`       | always empty  | _(no content)_                  |

---

## Step 4: Configure `pyproject.toml`

### Controller Selector

```toml
[build-system]
requires = ["setuptools"]
build-backend = "setuptools.backends.legacy:build"

[project]
name = "process-selector"
version = "0.1.0"
description = "Rule-based selector for three-skill process control agent"
dependencies = [
    "amesa-core",
]

[amesa]
type = "selector-controller"
entrypoint = "process_selector.controller:ProcessSelector"
```

### Teacher Selector

```toml
[build-system]
requires = ["setuptools"]
build-backend = "setuptools.backends.legacy:build"

[project]
name = "process-selector"
version = "0.1.0"
description = "RL-trained selector for three-skill process control agent"
dependencies = [
    "amesa-core",
]

[amesa]
type = "selector-teacher"
entrypoint = "process_selector.teacher:ProcessSelector"
```

### `type` Values

| Selector type           | `[amesa] type` value    |
| ----------------------- | ----------------------- |
| Rule-based (controller) | `"selector-controller"` |
| RL-trained (teacher)    | `"selector-teacher"`    |

> **Do not add a `variables` field.** The `variables` field is for perceptors only.

### Entrypoint Format

| Part           | Value (controller example)  |
| -------------- | --------------------------- |
| `inner_module` | `process_selector`          |
| `filename`     | `controller` (or `teacher`) |
| `ClassName`    | `ProcessSelector`           |

**Full entrypoint:** `process_selector.controller:ProcessSelector`

---

## Step 5: Verify Your Directory

```text
process-selector/
├── process_selector/
│   ├── __init__.py        ← must exist; must be empty
│   └── controller.py      ← (or teacher.py) contains ProcessSelector class
└── pyproject.toml         ← [amesa] type is "selector-controller" or "selector-teacher"
```

Checklist:

- [ ] `__init__.py` exists and is empty
- [ ] `pyproject.toml` is in the outer directory
- [ ] `type` in `[amesa]` is `"selector-controller"` or `"selector-teacher"`
- [ ] `entrypoint` uses the inner snake_case module name
- [ ] `compute_action` returns `[index]` — a list with a single integer
- [ ] Index values match the registration order of child skills in the agent
- [ ] All methods are declared `async def`
- [ ] `__init__` takes no required arguments
- [ ] No `variables` field in `[amesa]`
- [ ] All imports use `from amesa_core import ...`

---

## Step 6: Publish

```bash
amesa selector publish ./process-selector/
```

Or using the flag form:

```bash
amesa selector publish --path ./process-selector/
```

---

## Step 7: Confirm the Publish

```bash
amesa selector list
```

| Name             | Type       | Version | Description            | UUID |
| ---------------- | ---------- | ------- | ---------------------- | ---- |
| process-selector | controller | 1       | Rule-based selector... | ...  |

---

## Using a Selector in an Agent

Register the selector and its child skills in the agent. The child skills must be registered **before** the selector, and the integer indices in `compute_action` must match registration order.

```python
from amesa_core import Agent, Skill, Sensor, SkillSelector
from startup_skill.teacher import StartupTeacher
from steady_state_skill.teacher import SteadyStateTeacher
from recovery_skill.teacher import RecoveryTeacher
from process_selector.controller import ProcessSelector

agent = Agent()
agent.add_sensors([
    Sensor("process_state", "Overall process health [0..1]"),
    Sensor("temperature",   "Process temperature"),
    Sensor("pressure",      "Process pressure"),
])

# Define child skills — order determines the index the selector uses
skill_a = Skill("startup",      StartupTeacher)       # index 0
skill_b = Skill("steady-state", SteadyStateTeacher)   # index 1
skill_c = Skill("recovery",     RecoveryTeacher)      # index 2

# Define the selector with its child skills
selector = SkillSelector("process-selector", ProcessSelector, [skill_a, skill_b, skill_c])

agent.add_skill(selector)
```

> **Index order matters.** `compute_action` returning `[0]` runs `skill_a`. Returning `[1]` runs `skill_b`. The index is a zero-based position in the child skills list passed to `SkillSelector`.

---

## Updating a Published Selector

Increment `version` in `pyproject.toml` and republish:

```bash
amesa selector publish ./process-selector/
```

## Deleting a Selector

```bash
amesa selector delete
```

---

## Troubleshooting

### Wrong skill selected at runtime

Check that the integer indices returned by `compute_action` match the order in which child skills are passed to `SkillSelector(...)`. The first child is index `0`, the second is `1`, and so on. Returning an out-of-range index causes a runtime error.

### `TypeError` during episode reset

`__init__` has a required argument. Provide a default value for every parameter:

```python
# WRONG
def __init__(self, threshold: float):
    ...

# CORRECT
def __init__(self, threshold: float = 0.2):
    ...
```

### `ModuleNotFoundError` on publish

The entrypoint is using the kebab-case outer directory name instead of the inner snake_case module name:

```toml
# WRONG
entrypoint = "process-selector.controller:ProcessSelector"

# CORRECT
entrypoint = "process_selector.controller:ProcessSelector"
```

### Wrong `[amesa] type`

Selector types are different from skill types. Use `"selector-controller"` or `"selector-teacher"`, not `"skill-controller"` or `"skill-teacher"`.

```toml
# WRONG
type = "skill-controller"

# CORRECT
type = "selector-controller"
```
