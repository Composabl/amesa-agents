# Creating and Publishing Orchestrators

This guide walks you through everything you need to build an orchestrator from scratch and publish it to the AMESA platform, using the `amesa` CLI or the AMESA MCP tools. By the end, you will have a working orchestrator packaged as an artifact and registered in your use case.

For the exact interface, call order and edge cases, see [`agent-context/orchestrators/`](../../agent-context/orchestrators/).

---

## What Is an Orchestrator?

An **orchestrator** is a meta-agent that decides which child skill acts at each timestep. When your orchestration has several skills, the orchestrator receives sensor observations and outputs an integer index that selects the child skill that runs. The selected child's action reaches the simulator; the orchestrator's index never does.

Orchestrators let you decompose complex behavior into specialized skills and switch between them dynamically.

```
Orchestration
└── AgentOrchestrator ("my-orchestrator")   ← chooses which skill runs
    ├── Skill-A  ("stabilize")              ← index 0
    ├── Skill-B  ("accelerate")             ← index 1
    └── Skill-C  ("recover")                ← index 2
```

The orchestrator outputs `0` → Skill-A runs. `1` → Skill-B runs. `2` → Skill-C runs.

### Two Types of Orchestrator

| Type                        | When to use                                                                                                                                  |
| --------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| **Controller** (rule-based) | The selection logic is deterministic: you can write an explicit rule for which skill to choose given current sensor values.                  |
| **Teacher** (RL-trained)    | You want the orchestrator to _learn_ when to switch skills. It trains as an RL policy with its own reward signal and success criteria.        |

There is no separate orchestrator base class. A rule-based orchestrator subclasses `AgentController` and a learned one subclasses `AgentTeacher`, exactly like a skill. The key difference is what the action means: **for an orchestrator, the action is the index of a child skill**, not a command to the simulator. (`AgentOrchestratorController` is only a type label in the SDK, not a class you can import.)

---

## Step 1: Understand the Orchestrator Interface

### Controller Orchestrator

Subclass `AgentController` and return a child index from `compute_action`:

```python
from typing import Dict, List
from amesa_core import AgentController

class MyOrchestrator(AgentController):

    async def filtered_sensor_space(self) -> List[str]:
        # Which sensors does the selection logic need to read?
        ...

    async def compute_action(self, transformed_sensors: Dict, action):
        # Return the index of the child skill to run: an int, or a one-element list.
        # 0 → first child, 1 → second, etc. `action` is the index chosen last step (None on the first step).
        ...

    async def compute_success_criteria(self, transformed_sensors: Dict, action) -> bool:
        ...

    async def compute_termination(self, transformed_sensors: Dict, action) -> bool:
        ...
```

> **`compute_action` receives the raw sensors.** The runtime never calls `transform_sensors` on a controller orchestrator; `compute_action` gets every sim sensor and perceptor output, each as a one-element array.

> **A controller orchestrator's own success and termination don't end episodes in training.** The step's success and termination come from the selected child. The two methods are still required and must return a `bool`.

### Teacher Orchestrator

Subclass `AgentTeacher`; `compute_reward` drives the selection policy:

```python
from typing import Dict, List
from amesa_core import AgentTeacher

class MyOrchestrator(AgentTeacher):

    async def filtered_sensor_space(self) -> List[str]:
        ...

    async def compute_reward(self, transformed_sensors: Dict, action, sim_reward: float) -> float:
        # Reward signal that teaches the orchestrator when to switch skills
        ...

    async def compute_success_criteria(self, transformed_sensors: Dict, action) -> bool:
        ...

    async def transform_action(self, transformed_sensors: Dict, action):
        # The policy samples a child index; return it unchanged
        return action

    async def compute_termination(self, transformed_sensors: Dict, action) -> bool:
        return False
```

> **All methods are async.** Declare every method with `async def`.

> **`__init__` must accept zero required arguments.** The runtime re-creates the orchestrator at the start of every episode, so state does not survive between episodes. You don't need an `__init__` at all unless you set up state.

> **A teacher orchestrator runs its children in fixed order by default.** On the first step only child 0 can act; after that it can stay on the current child or move to the next one. Deploy it with `sequenceType: "variable"` (or `fixed_order=False` in SDK code) to let it switch freely. You can narrow the choice further with an optional `compute_action_mask` that returns one entry per child (`1` = allowed).

---

## Step 2: Write Your Orchestrator

Sensor values arrive as one-element arrays. Both examples use a small `_scalar` helper to read them as plain numbers.

---

### Option A: Controller Orchestrator (Rule-Based)

The example below selects between three process control skills based on a `process_state` sensor: a startup skill, a steady-state skill, and a recovery skill.

```python
# process_orchestrator/controller.py

from typing import Dict, List

import numpy as np
from amesa_core import AgentController

# Child index = position of the skill in the orchestrator's children list
SKILL_STARTUP = 0
SKILL_STEADY_STATE = 1
SKILL_RECOVERY = 2

# process_state thresholds
WARMUP_THRESHOLD = 0.2     # below this → still starting up
FAULT_THRESHOLD = 0.05     # below this → fault recovery needed


def _scalar(value) -> float:
    """Sensor values arrive as one-element arrays; read them as a float."""
    return float(np.asarray(value, dtype=float).reshape(-1)[0])


class ProcessOrchestrator(AgentController):
    """
    Rule-based orchestrator for a three-skill process control orchestration.
    Chooses startup, steady-state, or recovery based on process_state.
    """

    async def filtered_sensor_space(self) -> List[str]:
        return ["process_state", "temperature", "pressure"]

    async def compute_action(self, transformed_sensors: Dict, action):
        state = _scalar(transformed_sensors["process_state"])

        if state < FAULT_THRESHOLD:
            return SKILL_RECOVERY
        elif state < WARMUP_THRESHOLD:
            return SKILL_STARTUP
        else:
            return SKILL_STEADY_STATE

    async def compute_success_criteria(self, transformed_sensors: Dict, action) -> bool:
        return bool(_scalar(transformed_sensors["process_state"]) >= 0.9)

    async def compute_termination(self, transformed_sensors: Dict, action) -> bool:
        return False
```

---

### Option B: Teacher Orchestrator (RL-Trained)

The example below trains the orchestrator with reinforcement learning. The reward encourages it to keep `process_state` high, and the RL policy learns which skill to use when.

```python
# process_orchestrator/teacher.py

from typing import Dict, List

import numpy as np
from amesa_core import AgentTeacher


def _scalar(value) -> float:
    """Sensor values arrive as one-element arrays; read them as a float."""
    return float(np.asarray(value, dtype=float).reshape(-1)[0])


class ProcessOrchestrator(AgentTeacher):
    """
    RL-trained orchestrator for a three-skill process control orchestration.
    Reward drives the policy to maintain high process_state.
    """

    SUCCESS_THRESHOLD = 0.9
    FAIL_THRESHOLD = 0.05

    async def filtered_sensor_space(self) -> List[str]:
        return ["process_state", "temperature", "pressure"]

    async def compute_reward(self, transformed_sensors: Dict, action, sim_reward: float) -> float:
        # Reward the orchestrator for keeping process_state high
        return _scalar(transformed_sensors["process_state"])

    async def compute_success_criteria(self, transformed_sensors: Dict, action) -> bool:
        return bool(_scalar(transformed_sensors["process_state"]) >= self.SUCCESS_THRESHOLD)

    async def compute_termination(self, transformed_sensors: Dict, action) -> bool:
        return bool(_scalar(transformed_sensors["process_state"]) < self.FAIL_THRESHOLD)

    async def transform_action(self, transformed_sensors: Dict, action):
        # The orchestrator's action is a child index; return it unchanged
        return action
```

> **Child skills that are teachers must be trained first.** While a teacher orchestrator trains, its children run frozen, using their trained policies.

---

## Step 3: Create the Artifact Directory

### Using the CLI Scaffold (Recommended)

For a **controller** orchestrator:

```bash
amesa orchestrator new \
  --name process-orchestrator \
  --type controller \
  --description "Rule-based orchestrator for three-skill process control orchestration" \
  --location ./
```

For a **teacher** orchestrator:

```bash
amesa orchestrator new \
  --name process-orchestrator \
  --type teacher \
  --description "RL-trained orchestrator for three-skill process control orchestration" \
  --location ./
```

Both create:

```text
process-orchestrator/
  process_orchestrator/
    __init__.py        ← required
    controller.py      ← or teacher.py, depending on type
  pyproject.toml
```

> **Review the scaffold before you publish.** The generated controller returns `[3]` for three children, which is out of range, and declares `transform_sensors` / `transform_action` methods that aren't part of the controller interface. Replace its methods with your own, as in Step 2.

You can also get a scaffold through the AMESA MCP tools with `get_artifact_scaffold` (`artifactType: "orchestrator"`, `orchestratorType: "controller"` or `"teacher"`).

### Creating Manually

```bash
mkdir -p process-orchestrator/process_orchestrator
touch process-orchestrator/process_orchestrator/__init__.py
touch process-orchestrator/process_orchestrator/controller.py   # or teacher.py
touch process-orchestrator/pyproject.toml
```

### Naming Rules

| Layer               | Convention    | Example                         |
| ------------------- | ------------- | ------------------------------- |
| Outer directory     | kebab-case    | `process-orchestrator`          |
| Inner Python module | snake_case    | `process_orchestrator`          |
| Source file         | by convention | `controller.py` or `teacher.py` |
| `__init__.py`       | required      | usually empty                   |

---

## Step 4: Configure `pyproject.toml`

### Controller Orchestrator

```toml
[project]
name = "process-orchestrator"
version = "0.1.0"
description = "Rule-based orchestrator for three-skill process control orchestration"
dependencies = [
    "amesa-core",
    "numpy",
]

[amesa]
type = "orchestrator-controller"
entrypoint = "process_orchestrator.controller:ProcessOrchestrator"
```

### Teacher Orchestrator

```toml
[project]
name = "process-orchestrator"
version = "0.1.0"
description = "RL-trained orchestrator for three-skill process control orchestration"
dependencies = [
    "amesa-core",
    "numpy",
]

[amesa]
type = "orchestrator-teacher"
entrypoint = "process_orchestrator.teacher:ProcessOrchestrator"
```

`[project]` must have `name` and `version`. `[amesa]` must have `type` and `entrypoint`, and must be the top-level `[amesa]` table: the SDK does not read `[tool.amesa]`.

### `type` Values

| Orchestrator type       | `[amesa] type` value        |
| ----------------------- | --------------------------- |
| Rule-based (controller) | `"orchestrator-controller"` |
| RL-trained (teacher)    | `"orchestrator-teacher"`    |

The legacy values `"selector-controller"` and `"selector-teacher"` are still accepted and mapped to these.

> **Do not add a `variables` field.** The `variables` field is for perceptors only.

### Entrypoint Format

| Part           | Value (controller example)  |
| -------------- | --------------------------- |
| `inner_module` | `process_orchestrator`      |
| `filename`     | `controller` (or `teacher`) |
| `ClassName`    | `ProcessOrchestrator`       |

**Full entrypoint:** `process_orchestrator.controller:ProcessOrchestrator`

---

## Step 5: Verify and Validate Your Package

```text
process-orchestrator/
├── process_orchestrator/
│   ├── __init__.py        ← must exist
│   └── controller.py      ← (or teacher.py) contains ProcessOrchestrator class
└── pyproject.toml         ← [amesa] type is "orchestrator-controller" or "orchestrator-teacher"
```

Checklist:

- [ ] `__init__.py` exists
- [ ] `pyproject.toml` is in the outer directory and has `[project]` `name` and `version`
- [ ] `type` in `[amesa]` is `"orchestrator-controller"` or `"orchestrator-teacher"`
- [ ] `entrypoint` uses the inner snake_case module name
- [ ] `compute_action` returns one child index (an int or a one-element list) in `0..number of children − 1`
- [ ] Index values match the order of the orchestrator's children
- [ ] All methods are declared `async def`
- [ ] `__init__` takes no required arguments
- [ ] No `variables` field in `[amesa]`
- [ ] All imports use `from amesa_core import ...`

Then validate the package locally:

```bash
amesa orchestrator validate ./process-orchestrator/
```

`validate` checks the `pyproject.toml`, installs the dependencies, imports the entrypoint, and checks the base class and the async methods. It does **not** run the orchestrator against a simulator, so an out-of-range index is only caught at runtime.

---

## Step 6: Publish

Sign in once with `amesa login`, then:

```bash
amesa orchestrator publish ./process-orchestrator/
```

Or using the flag form:

```bash
amesa orchestrator publish --path ./process-orchestrator/
```

`publish` asks for the project (use case). If an orchestrator with the same name as `[project].name` already exists, it adds a new version to it; otherwise it creates the orchestrator.

### Publishing with the AMESA MCP tools

An assistant connected to the AMESA MCP server can publish the same package:

1. `organization_list` and `use_case_list` to find the `organizationId` and `projectId`.
2. `orchestrator_create` (`projectId`, `name`, `type: "controller"` or `"teacher"`) for a new orchestrator, or `orchestrator_implementation_publish` (`projectId`, `orchestratorId`) for a new version. Both return a short-lived upload URL.
3. Upload the packaged `.tar.gz` to that URL, then call `orchestrator_confirm_upload` (`projectId`, `implementationId`). For an existing orchestrator, `submit_code_file` publishes the files as a new version in one call instead.
4. `amesa_orchestrator_validate`, then poll the returned job with `component_validation_status`.

See [`agent-context/orchestrators/publishing.md`](../../agent-context/orchestrators/publishing.md) for every parameter.

---

## Step 7: Confirm the Publish

```bash
amesa orchestrator list
```

| Name                 | Type       | Version | Description                | UUID |
| -------------------- | ---------- | ------- | -------------------------- | ---- |
| process-orchestrator | controller | 1       | Rule-based orchestrator... | ...  |

---

## Using an Orchestrator in an Orchestration

On the platform, add the orchestrator to an orchestration with `orchestration_workflow_deploy` (or in the AMESA app). The order of its `skills` is the child index: the first skill is index `0`. Set `sequenceType` to `"variable"` (the default there) to let the orchestrator switch freely, or `"fixed"` to run the children in order.

In local SDK code, wrap the orchestrator class and its children in an `AgentOrchestrator`. Pass the children with the `children=` keyword:

```python
from amesa_core import Orchestration, Agent, Sensor, AgentOrchestrator
from startup_agent.teacher import StartupTeacher
from steady_state_agent.teacher import SteadyStateTeacher
from recovery_agent.teacher import RecoveryTeacher
from process_orchestrator.controller import ProcessOrchestrator

orchestration = Orchestration()
orchestration.add_sensors([
    Sensor("process_state", "Overall process health [0..1]"),
    Sensor("temperature",   "Process temperature"),
    Sensor("pressure",      "Process pressure"),
])

# Define child skills — their order in `children` is the index the orchestrator uses
skill_a = Agent("startup",      StartupTeacher)       # index 0
skill_b = Agent("steady-state", SteadyStateTeacher)   # index 1
skill_c = Agent("recovery",     RecoveryTeacher)      # index 2

# Define the orchestrator with its child skills
orchestrator = AgentOrchestrator(
    "process-orchestrator",
    ProcessOrchestrator,                     # the class, not an instance
    children=[skill_a, skill_b, skill_c],    # keyword-only
    fixed_order=False,                       # optional; the default is fixed order
)

orchestration.add_agent(orchestrator)
```

> **Index order matters.** `compute_action` returning `0` runs `skill_a`, `1` runs `skill_b`. The index is the zero-based position in the `children` list.

---

## Updating a Published Orchestrator

Republish; each publish adds a new version. You don't need to change `version` in `pyproject.toml`:

```bash
amesa orchestrator publish ./process-orchestrator/
```

## Deleting an Orchestrator

```bash
amesa orchestrator delete
```

The CLI asks you to pick the orchestrator to delete.

---

## Troubleshooting

### Wrong skill selected at runtime

Check that the indices returned by `compute_action` match the order of the orchestrator's children. The first child is index `0`, the second is `1`, and so on.

### `ValueError` at runtime about the child index

The orchestrator returned an index outside `0..number of children − 1`, or a list with more than one element. Return a single index. `amesa orchestrator validate` doesn't catch this, because it doesn't run the orchestrator.

### `AttributeError: 'list' object has no attribute 'config'` when building `AgentOrchestrator`

The children were passed as a positional argument, so the list was read as the orchestrator's configuration. Use the keyword: `AgentOrchestrator("name", MyOrchestrator, children=[...])`.

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

### Training fails with "missing checkpoint_uri"

A child skill that is a teacher hasn't been trained. Train each teacher child before training the orchestrator.

### `ModuleNotFoundError` on publish

The entrypoint is using the kebab-case outer directory name instead of the inner snake_case module name:

```toml
# WRONG
entrypoint = "process-orchestrator.controller:ProcessOrchestrator"

# CORRECT
entrypoint = "process_orchestrator.controller:ProcessOrchestrator"
```

### Wrong `[amesa] type`

Orchestrator types are different from skill types. Use `"orchestrator-controller"` or `"orchestrator-teacher"`, not `"agent-controller"` or `"agent-teacher"`.

```toml
# WRONG
type = "agent-controller"

# CORRECT
type = "orchestrator-controller"
```
