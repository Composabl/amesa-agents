# Creating and Publishing Teachers

This guide walks you through everything you need to build an Agent Teacher from scratch and publish it to Amesa Orchestration Studio using the `amesa` CLI. By the end, you will have a working teacher packaged as an artifact and registered in the AMESA registry.

---

## What Is a Teacher?

A **Teacher** is a Python class that defines how an agent learns. When an agent trains with reinforcement learning, it needs to know three things:

- **What is a good outcome?** — the reward signal
- **When has the agent succeeded?** — the success condition
- **When should training stop early?** — the failure/termination condition

Your Teacher class answers all three. It also controls which sensors the agent pays attention to and how actions are processed before being sent to the simulation.

You write the domain logic. AMESA handles the RL training engine, the simulator connection, and the infrastructure.

---

## Step 1: Understand the Teacher Methods

A Teacher is a subclass of `AgentTeacher` from `amesa_core`. You must implement four methods. The rest are optional.

### Required Methods

| Method                     | What it does                                                                                                                               |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| `compute_reward`           | Returns a `float` reward for each training step. Higher is better. This is your primary teaching signal.                                   |
| `compute_success_criteria` | Returns `True` when the agent has achieved its goal for this episode.                                                                      |
| `transform_action`         | Pre-processes the raw action from the RL model before it is sent to the simulator. Return the action unchanged if no processing is needed. |
| `filtered_sensor_space`    | Returns a list of sensor name strings that this agent observes. Only listed sensors are visible to the RL policy.                          |

### Optional Methods

| Method                | What it does                                                                                                                      | Default        |
| --------------------- | --------------------------------------------------------------------------------------------------------------------------------- | -------------- |
| `compute_termination` | Returns `True` to end the episode early as a failure. Use this to cut off episodes that have gone badly wrong and cannot recover. | `return False` |
| `transform_sensors`   | Pre-processes the raw sensor dict before it reaches the RL policy. Use for unit conversion; keys it adds are visible to your reward logic but are **not** policy inputs. | pass-through   |
| `compute_action_mask` | Returns a mask of valid actions for the current step. | `return None` |
| `get_custom_action_space` | Returns a gymnasium space the policy trains in instead of the sim's; `transform_action` must map back. | `return None` |
| `compute_scenario_advancement` | Returns `{"scenario_success_rate": ..., "scenario_success_window": ...}` — when to advance to the next scenario. | `0.8` over `100` episodes |
| `reset`               | Called at the start of every episode; clear per-episode state. | no-op |

### Method Signatures

```python
from typing import Dict, List
from amesa_core import AgentTeacher

class MyTeacher(AgentTeacher):

    # Required — called once at startup; result is cached
    async def filtered_sensor_space(self) -> List[str]:
        ...

    # Required — called every step; return a float
    async def compute_reward(self, transformed_sensors: Dict, action, sim_reward: float) -> float:
        ...

    # Required — called every step; return True when the agent has succeeded
    async def compute_success_criteria(self, transformed_sensors: Dict, action) -> bool:
        ...

    # Required — called every step; return the action to send to the simulator
    async def transform_action(self, transformed_sensors: Dict, action):
        ...

    # Optional — called every step; return True to end the episode as a failure
    async def compute_termination(self, transformed_sensors: Dict, action) -> bool:
        return False

    # Optional — called every step (action is always None); return a modified sensors dict
    async def transform_sensors(self, sensors, action) -> Dict:
        return sensors

    # Optional — called at the start of every episode
    async def reset(self):
        pass
```

Each step, the trainer calls `transform_sensors`, then scores the **previous** action with `compute_reward`, `compute_success_criteria` and `compute_termination`. If success or termination is `True` the episode ends; otherwise the policy acts and `transform_action` runs. Sensor values arrive as NumPy arrays (usually shape `(1,)`).

> **Important — all methods are `async`** (except `add_scenario`). Declare every method with `async def`. `amesa agent validate` reports a required method that is not `async`.

> **Important — `__init__` must accept zero arguments.** The framework re-creates your teacher at the start of every training episode by calling `MyTeacher()` with no arguments. Any `__init__` parameter that does not have a default value will cause a `TypeError` on every episode reset.

---

## Step 2: Write Your Teacher

There are two approaches: writing a **custom teacher** from scratch, or using a **built-in Goal class** for common objectives.

---

### Option A: Custom Teacher

Use a custom teacher when your reward logic or success criteria are specific to your domain.

The example below trains a agent to maintain a process temperature near a target setpoint. The reward decreases the further the temperature drifts from the target. The episode succeeds when temperature is within tolerance and terminates early if it goes too far off.

```python
# temperature_teacher/teacher.py

from typing import Dict, List

import numpy as np
from amesa_core import AgentTeacher


class TemperatureTeacher(AgentTeacher):
    """
    Trains an agent to maintain process temperature near a setpoint.

    Reward: negative absolute error from target (closer = higher reward)
    Success: temperature within TOLERANCE of target
    Termination: temperature more than FAIL_DISTANCE from target
    """

    TARGET = 80.0       # desired temperature
    TOLERANCE = 2.0     # success band: ±2 degrees
    FAIL_DISTANCE = 20.0  # terminate if this far from target

    def __init__(self):
        # __init__ must take no required arguments
        # self.* state is wiped at every episode reset — do not store cross-episode data here
        pass

    async def filtered_sensor_space(self) -> List[str]:
        # Declare which sensors the RL policy observes
        # Only these sensor names will be visible during training; each must be
        # a sim sensor or a perceptor output
        return ["temperature", "heater_output"]

    async def compute_reward(self, transformed_sensors: Dict, action, sim_reward: float) -> float:
        error = abs(float(transformed_sensors["temperature"]) - self.TARGET)
        return float(-error)  # reward = 0 at target; decreases with distance

    async def compute_success_criteria(self, transformed_sensors: Dict, action) -> bool:
        error = abs(float(transformed_sensors["temperature"]) - self.TARGET)
        return error <= self.TOLERANCE

    async def compute_termination(self, transformed_sensors: Dict, action) -> bool:
        error = abs(float(transformed_sensors["temperature"]) - self.TARGET)
        return error >= self.FAIL_DISTANCE

    async def transform_action(self, transformed_sensors: Dict, action):
        # Clamp heater output to valid range [0.0, 1.0]
        return np.clip(action, 0.0, 1.0)

    async def transform_sensors(self, sensors, action) -> Dict:
        # No pre-processing needed — pass sensors through unchanged
        # Note: action is always None here; do not write logic that depends on it
        return sensors
```

---

### Option B: Goal-Based Teacher (Less Code)

If your objective fits one of the built-in patterns — maximize, minimize, maintain, approach, or avoid a sensor value — use a **Goal class** instead of writing reward logic by hand. Goal classes are subclasses of `AgentTeacher` and satisfy the full teacher contract automatically.

| Goal Class        | Use when you want to...                         |
| ----------------- | ----------------------------------------------- |
| `MaximizeGoal`    | Drive a sensor value as high as possible        |
| `MinimizeGoal`    | Drive a sensor value as low as possible         |
| `MaintainGoal`    | Hold a sensor near a target value within a band |
| `ApproachGoal`    | Reach a target value as quickly as possible     |
| `AvoidGoal`       | Keep a sensor away from a boundary value        |
| `CoordinatedGoal` | Combine multiple goals into a single teacher    |

The example below reproduces the temperature setpoint objective above using `MaintainGoal`, with no manual reward function:

```python
# temperature_teacher/teacher.py

from typing import Dict

import numpy as np
from amesa_core.orchestration.agent.goals.coordinated_goal import CoordinatedGoal
from amesa_core.orchestration.agent.goals.maintain_goal import MaintainGoal


class TemperatureTeacher(CoordinatedGoal):
    """
    Goal-based teacher: maintain temperature near setpoint using MaintainGoal.
    CoordinatedGoal handles compute_reward, compute_success_criteria,
    and compute_termination automatically.
    """

    def __init__(self):
        temperature_goal = MaintainGoal(
            "temperature",
            "Maintain process temperature near setpoint",
            target=80.0,
            tolerance=2.0,
        )
        super().__init__([temperature_goal])

    async def transform_action(self, transformed_sensors: Dict, action):
        return np.clip(action, 0.0, 1.0)

    async def transform_sensors(self, sensors, action) -> Dict:
        return sensors
```

Use `CoordinatedGoal` when you have one or more goal objectives. Pass all goal instances as a list to `super().__init__()`.

---

## Step 3: Create the Artifact Directory

A published teacher must be packaged in a specific directory layout. The `amesa agent new` command scaffolds this for you automatically, or you can create it manually.

### Using the CLI Scaffold (Recommended)

```bash
amesa agent new \
  --name temperature-teacher \
  --type teacher \
  --description "Maintains process temperature near setpoint" \
  --location ./
```

This creates the following directory:

```text
temperature-teacher/
  temperature_teacher/
    __init__.py        ← required (the scaffold's holds only a header comment)
    teacher.py         ← your AgentTeacher subclass goes here
  pyproject.toml       ← artifact metadata; CLI reads this on publish
```

Replace the placeholder `teacher.py` with your implementation from Step 2. The scaffold's entrypoint is `temperature_teacher.teacher:Teacher`; update it if you rename the class.

### Creating Manually

If you prefer to create the structure yourself:

```bash
mkdir -p temperature-teacher/temperature_teacher
touch temperature-teacher/temperature_teacher/__init__.py
touch temperature-teacher/temperature_teacher/teacher.py
touch temperature-teacher/pyproject.toml
```

Then copy your teacher code into `temperature_teacher/teacher.py` and fill in `pyproject.toml` as described in the next step.

---

### Naming Rules

The directory has two layers with different naming conventions:

| Layer               | Convention    | Example               |
| ------------------- | ------------- | --------------------- |
| Outer directory     | kebab-case    | `temperature-teacher` |
| Inner Python module | snake_case    | `temperature_teacher` |
| Source file         | by convention | `teacher.py`          |
| `__init__.py`       | required      | usually empty         |

The outer directory is a **filesystem path used by the CLI only**. The inner snake_case directory is the **Python module** referenced in your `pyproject.toml` entrypoint. Do not mix these up — using the kebab-case outer name as your Python import path will cause a `ModuleNotFoundError` on publish.

---

## Step 4: Configure `pyproject.toml`

Open `temperature-teacher/pyproject.toml` and fill it in:

```toml
[build-system]
requires = ["setuptools"]
build-backend = "setuptools.backends.legacy:build"

[project]
name = "temperature-teacher"
version = "0.1.0"
description = "Maintains process temperature near setpoint"
dependencies = [
    "amesa-core",
]

[amesa]
type = "agent-teacher"
entrypoint = "temperature_teacher.teacher:TemperatureTeacher"
```

### Field Reference

| Field          | Where       | Required | Description                                                                           |
| -------------- | ----------- | -------- | ------------------------------------------------------------------------------------- |
| `name`         | `[project]` | Yes      | Artifact name as it will appear in the registry. Kebab-case.                          |
| `version`      | `[project]` | Yes      | Semantic version string (e.g. `0.1.0`).                                               |
| `description`  | `[project]` | No       | Short human-readable description (used as the agent description on publish).         |
| `dependencies` | `[project]` | Recommended | Include `"amesa-core"` and any other packages your teacher imports.                |
| `type`         | `[amesa]`   | Yes      | Must be `"agent-teacher"` for a teacher.                                              |
| `entrypoint`   | `[amesa]`   | Yes      | `module_name.file_name:ClassName` — resolves your class from inside the inner module. |

### Entrypoint Format

The entrypoint string follows the pattern: `inner_module.filename:ClassName`

| Part           | Value in this example                                           |
| -------------- | --------------------------------------------------------------- |
| `inner_module` | `temperature_teacher` (the snake_case inner directory)          |
| `filename`     | `teacher` (the `.py` file, without extension)                   |
| `ClassName`    | `TemperatureTeacher` (the class that subclasses `AgentTeacher`) |

**Full entrypoint:** `temperature_teacher.teacher:TemperatureTeacher`

> The section is top-level `[amesa]` — not `[tool.amesa]`, which the validator does not read.

> **Common mistake:** using the outer kebab-case directory name (`temperature-teacher`) in the entrypoint. Python cannot import a name with a hyphen. Always use the inner snake_case module name.

---

## Step 5: Verify Your Directory

Before publishing, confirm your structure looks correct:

```text
temperature-teacher/
├── temperature_teacher/
│   ├── __init__.py        ← must exist
│   └── teacher.py         ← contains TemperatureTeacher class
└── pyproject.toml         ← contains [amesa] section with type and entrypoint
```

Quick checklist:

- [ ] `__init__.py` exists
- [ ] `pyproject.toml` is in the **outer** directory (same level as `temperature_teacher/`)
- [ ] `type` in `[amesa]` is `"agent-teacher"`
- [ ] `entrypoint` uses the **inner snake_case** module name, not the outer kebab-case name
- [ ] The class name in `entrypoint` exactly matches the class name in `teacher.py`
- [ ] All imports in `teacher.py` use `from amesa_core import ...`
- [ ] `__init__` in your teacher class takes no required arguments
- [ ] Every name in `filtered_sensor_space` is a sim sensor or perceptor output

Then validate locally:

```bash
amesa agent validate ./temperature-teacher/            # also runs it against a mock of the project's sim
amesa agent validate ./temperature-teacher/ --static   # files and code only
```

Validation checks the `pyproject.toml`, loads the entrypoint, checks the abstract methods are implemented as `async`, checks `compute_scenario_advancement`, and (without `--static`) runs the teacher for a number of steps (`--max-steps`, default 50) on sensors sampled from the sim's bounds.

---

## Step 6: Publish

From the directory that **contains** your artifact folder, run:

```bash
amesa agent publish ./temperature-teacher/
```

You can also use the `--path` flag:

```bash
amesa agent publish --path ./temperature-teacher/
```

The CLI will:

1. Ask you to select a project (if you have more than one)
2. Package the directory as a compressed archive
3. Read `pyproject.toml` to extract the name, description, and type
4. Reuse the project's agent with the same `[project].name`, or create it if none exists
5. Upload the artifact as a new version

A successful publish prints the artifact name and confirms the upload. The teacher is now registered and available to training jobs in your selected project.

---

## Step 7: Confirm the Publish

List your project's agents to confirm the teacher appeared:

```bash
amesa agent list
```

This prints a table of all agents registered to the project, including:

| Name                | Type    | Version | Description                                 | UUID |
| ------------------- | ------- | ------- | ------------------------------------------- | ---- |
| temperature-teacher | teacher | 1       | Maintains process temperature near setpoint | ...  |

Copy the UUID if you need to reference this teacher in an agent orchestration.

---

## Updating a Published Teacher

To publish a new version of a teacher, keep the same `[project].name`, bump the `version` field in `pyproject.toml` (recommended), and run `amesa agent publish` again:

```toml
[project]
version = "0.2.0"   # ← increment before re-publishing
```

```bash
amesa agent publish ./temperature-teacher/
```

Each publish creates a new version entry in the registry, numbered by the platform. Prior versions remain available; download one with `amesa agent retrieve`.

### Publishing through the AMESA MCP tools

Find the use case with `organization_list` / `use_case_list`, then either `operational_agent_create` (`type: "teacher"`, first version, returns an upload URL) or `operational_agent_implementation_publish` (new version) → upload → `operational_agent_confirm_upload`; or send the files with `submit_code_file` (`artifactType: "skill"`, `skillType: "teacher"`). Validate on compute with `amesa_agent_validate` + `component_validation_status`. See `agent-context/teacher/publishing.md`.

---

## Deleting a Teacher

To remove a teacher from the registry:

```bash
amesa agent delete
```

The CLI presents an interactive list of your project's agents. Select the one you want to remove and confirm. Deletion is permanent and cannot be undone.

---

## Troubleshooting

### `ModuleNotFoundError` on publish

Your `entrypoint` in `pyproject.toml` is using the wrong module path. Check that you are using the **inner snake_case** directory name, not the outer kebab-case name:

```toml
# WRONG — hyphens are not valid in Python imports
entrypoint = "temperature-teacher.teacher:TemperatureTeacher"

# CORRECT — use the inner snake_case module
entrypoint = "temperature_teacher.teacher:TemperatureTeacher"
```

### `TypeError` during episode reset

Your `__init__` method has a required argument. The framework calls `MyTeacher()` with no arguments at every episode boundary. Use keyword arguments with default values:

```python
# WRONG — threshold is required, will raise TypeError on episode reset
def __init__(self, threshold: float):
    self.threshold = threshold

# CORRECT — provide a default value
def __init__(self, threshold: float = 80.0):
    self.threshold = threshold
```

### `ImportError` — `composabl` or `composabl_core` not found

These are legacy package names. Update all imports to use `amesa_core`:

```python
# WRONG
from composabl import AgentTeacher
from composabl_core import AgentTeacher

# CORRECT
from amesa_core import AgentTeacher
```

Also update `pyproject.toml`:

```toml
# WRONG
dependencies = ["composabl-core"]

# CORRECT
dependencies = ["amesa-core"]
```

### Reward is `None` or training crashes immediately

`compute_reward` must return a finite number. If you forget to return a value or return `None` (or NaN/inf), validation fails and training crashes. Add an explicit `return`:

```python
async def compute_reward(self, transformed_sensors, action, sim_reward) -> float:
    error = abs(float(transformed_sensors["temperature"]) - self.TARGET)
    return float(-error)   # ← must always return a number
```

### Both success and termination return `True` on the same step

If `compute_success_criteria` and `compute_termination` both return `True` simultaneously, the episode ends as a **failure**, not a success. Review your threshold logic to make sure success and failure conditions are mutually exclusive, or ensure the termination threshold is strictly worse than the success threshold.
