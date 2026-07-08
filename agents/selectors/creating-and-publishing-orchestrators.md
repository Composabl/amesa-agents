# Creating and Publishing Orchestrators

This guide walks you through everything you need to build a Orchestrator from scratch and publish it to Amesa Orchestration Studio using the `amesa` CLI. By the end, you will have a working orchestrator packaged as an artifact and registered in the AMESA registry.

---

## What Is a Orchestrator?

A **Orchestrator** is a meta-agent that decides which child agent executes at each timestep. When your orchestration has multiple agents, the orchestrator receives sensor observations and outputs an integer index that determines which child agent runs next. The selected child's action reaches the simulator — the orchestrator's index never does.

Orchestrators enable agent **orchestrations** that decompose complex behavior into specialized sub-agents and switch between them dynamically.

```
Orchestration
└── AgentOrchestrator ("my-orchestrator")      ← chooses which agent runs
    ├── Agent-A  ("stabilize")          ← leaf agent
    ├── Agent-B  ("accelerate")         ← leaf agent
    └── Agent-C  ("recover")            ← leaf agent
```

The orchestrator outputs `0` → Agent-A runs. `1` → Agent-B runs. `2` → Agent-C runs.

### Two Types of Orchestrator

| Type                        | When to use                                                                                                                               |
| --------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| **Controller** (rule-based) | The selection logic is deterministic — you can write an explicit rule for which agent to choose given current sensor values.              |
| **Teacher** (RL-trained)    | You want the agent to _learn_ when to switch agents. The orchestrator trains as an RL policy with its own reward signal and success criteria. |

Orchestrators use the same `AgentController` and `AgentTeacher` interfaces as regular agents. The key difference is what the action means: **for a orchestrator, the action is an integer index**, not a command to the simulator.

---

## Step 1: Understand the Orchestrator Interface

### Controller Orchestrator

Implement `AgentController` with `compute_action` returning an integer index:

```python
from typing import Dict, List
from amesa_core import AgentController

class MyOrchestrator(AgentController):

    def __init__(self):
        pass

    async def filtered_sensor_space(self, obs_spec) -> List[str]:
        # Which sensors does the selection logic need to read?
        ...

    async def compute_action(self, obs_spec: Dict, action) -> List[int]:
        # Return [index] where index selects the child agent to run
        # 0 → first registered child, 1 → second, etc.
        ...

    async def compute_success_criteria(self, obs_spec: Dict, action) -> bool:
        ...

    async def compute_termination(self, obs_spec: Dict, action) -> bool:
        ...
```

### Teacher Orchestrator

Implement `AgentTeacher` with `compute_reward` driving the selection policy:

```python
from typing import Dict, List
from amesa_core import AgentTeacher

class MyOrchestrator(AgentTeacher):

    def __init__(self):
        pass

    async def filtered_sensor_space(self) -> List[str]:
        ...

    async def compute_reward(self, transformed_sensors: Dict, action, sim_reward: float) -> float:
        # Reward signal that teaches the orchestrator when to switch agents
        ...

    async def compute_success_criteria(self, transformed_sensors: Dict, action) -> bool:
        ...

    async def transform_action(self, transformed_sensors: Dict, action):
        # Return the action unchanged — the orchestrator's action is an index
        return action

    async def compute_termination(self, transformed_sensors: Dict, action) -> bool:
        return False
```

> **All methods are async.** Declare every method with `async def`.

> **`__init__` must accept zero required arguments.** The framework re-creates the orchestrator at the start of every episode.

---

## Step 2: Write Your Orchestrator

---

### Option A: Controller Orchestrator (Rule-Based)

The example below selects between three process control agents based on a `process_state` sensor: a startup agent, a steady-state agent, and a recovery agent.

```python
# process_orchestrator/controller.py

from typing import Dict, List
from amesa_core import AgentController

# Agent index mapping (matches registration order in the orchestration)
SKILL_STARTUP = 0
SKILL_STEADY_STATE = 1
SKILL_RECOVERY = 2

# process_state thresholds
WARMUP_THRESHOLD = 0.2     # below this → still starting up
FAULT_THRESHOLD = 0.05     # below this → fault recovery needed


class ProcessOrchestrator(AgentController):
    """
    Rule-based orchestrator for a three-agent process control orchestration.
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

### Option B: Teacher Orchestrator (RL-Trained)

The example below trains the orchestrator with reinforcement learning. The reward encourages it to keep `process_state` high, and the RL policy learns which agent combinations achieve that over time.

```python
# process_orchestrator/teacher.py

from typing import Dict, List
from amesa_core import AgentTeacher


class ProcessOrchestrator(AgentTeacher):
    """
    RL-trained orchestrator for a three-agent process control orchestration.
    Reward drives the policy to maintain high process_state.
    """

    SUCCESS_THRESHOLD = 0.9
    FAIL_THRESHOLD = 0.05

    def __init__(self):
        pass

    async def filtered_sensor_space(self) -> List[str]:
        return ["process_state", "temperature", "pressure"]

    async def compute_reward(self, transformed_sensors: Dict, action, sim_reward: float) -> float:
        # Reward the orchestrator for keeping process_state high
        return float(transformed_sensors["process_state"])

    async def compute_success_criteria(self, transformed_sensors: Dict, action) -> bool:
        return transformed_sensors["process_state"] >= self.SUCCESS_THRESHOLD

    async def compute_termination(self, transformed_sensors: Dict, action) -> bool:
        return transformed_sensors["process_state"] < self.FAIL_THRESHOLD

    async def transform_action(self, transformed_sensors: Dict, action):
        # The orchestrator's action is a agent index — return it unchanged
        return action
```

---

## Step 3: Create the Artifact Directory

### Using the CLI Scaffold (Recommended)

For a **controller** orchestrator:

```bash
amesa orchestrator new \
  --name process-orchestrator \
  --type controller \
  --description "Rule-based orchestrator for three-agent process control orchestration" \
  --location ./
```

For a **teacher** orchestrator:

```bash
amesa orchestrator new \
  --name process-orchestrator \
  --type teacher \
  --description "RL-trained orchestrator for three-agent process control orchestration" \
  --location ./
```

Both create:

```text
process-orchestrator/
  process_orchestrator/
    __init__.py        ← empty; required
    controller.py      ← or teacher.py, depending on type
  pyproject.toml
```

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
| Outer directory     | kebab-case    | `process-orchestrator`              |
| Inner Python module | snake_case    | `process_orchestrator`              |
| Source file         | by convention | `controller.py` or `teacher.py` |
| `__init__.py`       | always empty  | _(no content)_                  |

---

## Step 4: Configure `pyproject.toml`

### Controller Orchestrator

```toml
[build-system]
requires = ["setuptools"]
build-backend = "setuptools.backends.legacy:build"

[project]
name = "process-orchestrator"
version = "0.1.0"
description = "Rule-based orchestrator for three-agent process control orchestration"
dependencies = [
    "amesa-core",
]

[amesa]
type = "orchestrator-controller"
entrypoint = "process_orchestrator.controller:ProcessOrchestrator"
```

### Teacher Orchestrator

```toml
[build-system]
requires = ["setuptools"]
build-backend = "setuptools.backends.legacy:build"

[project]
name = "process-orchestrator"
version = "0.1.0"
description = "RL-trained orchestrator for three-agent process control orchestration"
dependencies = [
    "amesa-core",
]

[amesa]
type = "orchestrator-teacher"
entrypoint = "process_orchestrator.teacher:ProcessOrchestrator"
```

### `type` Values

| Orchestrator type           | `[amesa] type` value    |
| ----------------------- | ----------------------- |
| Rule-based (controller) | `"orchestrator-controller"` |
| RL-trained (teacher)    | `"orchestrator-teacher"`    |

> **Do not add a `variables` field.** The `variables` field is for perceptors only.

### Entrypoint Format

| Part           | Value (controller example)  |
| -------------- | --------------------------- |
| `inner_module` | `process_orchestrator`          |
| `filename`     | `controller` (or `teacher`) |
| `ClassName`    | `ProcessOrchestrator`           |

**Full entrypoint:** `process_orchestrator.controller:ProcessOrchestrator`

---

## Step 5: Verify Your Directory

```text
process-orchestrator/
├── process_orchestrator/
│   ├── __init__.py        ← must exist; must be empty
│   └── controller.py      ← (or teacher.py) contains ProcessOrchestrator class
└── pyproject.toml         ← [amesa] type is "orchestrator-controller" or "orchestrator-teacher"
```

Checklist:

- [ ] `__init__.py` exists and is empty
- [ ] `pyproject.toml` is in the outer directory
- [ ] `type` in `[amesa]` is `"orchestrator-controller"` or `"orchestrator-teacher"`
- [ ] `entrypoint` uses the inner snake_case module name
- [ ] `compute_action` returns `[index]` — a list with a single integer
- [ ] Index values match the registration order of child agents in the orchestration
- [ ] All methods are declared `async def`
- [ ] `__init__` takes no required arguments
- [ ] No `variables` field in `[amesa]`
- [ ] All imports use `from amesa_core import ...`

---

## Step 6: Publish

```bash
amesa orchestrator publish ./process-orchestrator/
```

Or using the flag form:

```bash
amesa orchestrator publish --path ./process-orchestrator/
```

---

## Step 7: Confirm the Publish

```bash
amesa orchestrator list
```

| Name             | Type       | Version | Description            | UUID |
| ---------------- | ---------- | ------- | ---------------------- | ---- |
| process-orchestrator | controller | 1       | Rule-based orchestrator... | ...  |

---

## Using a Orchestrator in an Orchestration

Register the orchestrator and its child agents in the orchestration. The child agents must be registered **before** the orchestrator, and the integer indices in `compute_action` must match registration order.

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

# Define child agents — order determines the index the orchestrator uses
agent_a = Agent("startup",      StartupTeacher)       # index 0
agent_b = Agent("steady-state", SteadyStateTeacher)   # index 1
agent_c = Agent("recovery",     RecoveryTeacher)      # index 2

# Define the orchestrator with its child agents
orchestrator = AgentOrchestrator("process-orchestrator", ProcessOrchestrator, [agent_a, agent_b, agent_c])

orchestration.add_agent(orchestrator)
```

> **Index order matters.** `compute_action` returning `[0]` runs `agent_a`. Returning `[1]` runs `agent_b`. The index is a zero-based position in the child agents list passed to `AgentOrchestrator`.

---

## Updating a Published Orchestrator

Increment `version` in `pyproject.toml` and republish:

```bash
amesa orchestrator publish ./process-orchestrator/
```

## Deleting a Orchestrator

```bash
amesa orchestrator delete
```

---

## Troubleshooting

### Wrong agent selected at runtime

Check that the integer indices returned by `compute_action` match the order in which child agents are passed to `AgentOrchestrator(...)`. The first child is index `0`, the second is `1`, and so on. Returning an out-of-range index causes a runtime error.

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
entrypoint = "process-orchestrator.controller:ProcessOrchestrator"

# CORRECT
entrypoint = "process_orchestrator.controller:ProcessOrchestrator"
```

### Wrong `[amesa] type`

Orchestrator types are different from agent types. Use `"orchestrator-controller"` or `"orchestrator-teacher"`, not `"agent-controller"` or `"agent-teacher"`.

```toml
# WRONG
type = "agent-controller"

# CORRECT
type = "orchestrator-controller"
```
