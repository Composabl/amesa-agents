# Creating and Publishing Controllers

This guide walks you through everything you need to build a Skill Controller from scratch and publish it to Amesa Orchestration Studio using the `amesa` CLI. By the end, you will have a working controller packaged as an artifact and registered in the AMESA registry.

---

## What Is a Controller?

A **Controller** is a deterministic, hand-coded skill. Instead of learning a policy through reinforcement learning, a controller executes rule-based, algorithmic, or expert-system logic that you write directly. Every call to the controller runs your code — there is no training involved.

Use a controller when:

- The correct action can be computed directly from sensor values (PID, proportional, rule-based)
- You have an existing algorithm or expert system you want to run as a skill
- You want a reliable baseline to compare against a trained RL skill
- The action logic is fully specified and does not need to adapt to new conditions

Controllers and RL Teachers can coexist in the same agent. A common pattern is to use a controller as a stabilizing baseline skill alongside RL teachers that handle more complex sub-tasks.

---

## Step 1: Understand the Controller Methods

A Controller is a subclass of `SkillController` from `amesa_core`. You must implement four methods.

### Required Methods

| Method                     | What it does                                                                                                 |
| -------------------------- | ------------------------------------------------------------------------------------------------------------ |
| `compute_action`           | Returns the action to send to the simulator. This is your core control logic — called once per timestep.     |
| `filtered_sensor_space`    | Returns the list of sensor names this controller reads. Only listed sensors are visible in `compute_action`. |
| `compute_success_criteria` | Returns `True` when the current episode should be considered a success.                                      |
| `compute_termination`      | Returns `True` to end the episode early as a failure.                                                        |

> **All four methods are async.** Declare every method with `async def`.

> **`__init__` must accept zero required arguments.** The framework re-creates your controller at the start of every episode by calling `MyController()` with no arguments. Any `__init__` parameter without a default value causes a `TypeError` on every episode reset.

### Method Signatures

```python
from typing import Dict, List
from amesa_core import SkillController

class MyController(SkillController):

    def __init__(self):
        # Must accept zero required arguments
        # All self.* state is wiped at every episode reset
        pass

    async def filtered_sensor_space(self, obs_spec) -> List[str]:
        # Declare which sensors this controller observes
        # Called once at startup; result is cached
        ...

    async def compute_action(self, obs_spec: Dict, action) -> any:
        # Core control logic — called every timestep
        # obs_spec: filtered sensor dict (keys match filtered_sensor_space)
        # action:   previous action sent to the sim (None on first step)
        # Returns:  the action to send to the simulator
        ...

    async def compute_success_criteria(self, obs_spec: Dict, action) -> bool:
        # Return True when the episode should end as a success
        ...

    async def compute_termination(self, obs_spec: Dict, action) -> bool:
        # Return True to end the episode early as a failure
        ...
```

### `compute_action` Parameters

| Parameter  | Type   | Description                                                                                           |
| ---------- | ------ | ----------------------------------------------------------------------------------------------------- |
| `obs_spec` | `Dict` | Filtered sensor observations for this step. Keys match the names returned by `filtered_sensor_space`. |
| `action`   | any    | The action sent to the simulator on the **previous** step. `None` on the first step of each episode.  |

**Return value:** The action to send to the simulator. Must match the simulator's expected action format.

---

## Step 2: Write Your Controller

The example below implements a proportional controller that maintains dissolved oxygen in a fermentation reactor near a target setpoint by adjusting agitation speed.

```python
# fermentation_controller/controller.py

from typing import Dict, List
from amesa_core import SkillController


class FermentationController(SkillController):
    """
    Proportional controller for dissolved oxygen in a fermentation reactor.
    Adjusts agitation speed based on deviation from target DO setpoint.
    """

    TARGET_DO = 0.65       # target dissolved oxygen fraction
    TOLERANCE = 0.03       # success band: ±0.03
    FAIL_DO_LOW = 0.10     # terminate if DO drops this low
    KP = 2.5               # proportional gain

    def __init__(self):
        # No required arguments — called with no args at every episode reset
        self.prev_error = 0.0

    async def filtered_sensor_space(self, obs_spec) -> List[str]:
        # Expose only the sensors this controller actually reads
        return ["dissolved_oxygen", "agitation_rpm"]

    async def compute_action(self, obs_spec: Dict, action) -> List[float]:
        do_level = obs_spec["dissolved_oxygen"]
        error = self.TARGET_DO - do_level

        # Proportional control: positive error → increase agitation
        delta_rpm = self.KP * error
        self.prev_error = error

        return [float(delta_rpm)]

    async def compute_success_criteria(self, obs_spec: Dict, action) -> bool:
        do_level = obs_spec["dissolved_oxygen"]
        return abs(do_level - self.TARGET_DO) <= self.TOLERANCE

    async def compute_termination(self, obs_spec: Dict, action) -> bool:
        do_level = obs_spec["dissolved_oxygen"]
        return do_level < self.FAIL_DO_LOW
```

### Accessing Full Sensor List

To expose all agent sensors to the controller rather than a subset:

```python
async def filtered_sensor_space(self, obs_spec) -> List[str]:
    return obs_spec   # pass through — observe everything
```

---

## Step 3: Create the Artifact Directory

### Using the CLI Scaffold (Recommended)

```bash
amesa skill new \
  --name fermentation-controller \
  --type controller \
  --description "Proportional DO controller for fermentation reactor" \
  --location ./
```

This creates:

```text
fermentation-controller/
  fermentation_controller/
    __init__.py        ← empty; required
    controller.py      ← your SkillController subclass goes here
  pyproject.toml
```

Replace the placeholder `controller.py` with your implementation from Step 2.

### Creating Manually

```bash
mkdir -p fermentation-controller/fermentation_controller
touch fermentation-controller/fermentation_controller/__init__.py
touch fermentation-controller/fermentation_controller/controller.py
touch fermentation-controller/pyproject.toml
```

### Naming Rules

| Layer               | Convention    | Example                   |
| ------------------- | ------------- | ------------------------- |
| Outer directory     | kebab-case    | `fermentation-controller` |
| Inner Python module | snake_case    | `fermentation_controller` |
| Source file         | by convention | `controller.py`           |
| `__init__.py`       | always empty  | _(no content)_            |

The outer kebab-case directory is used by the CLI only. The inner snake_case directory is the importable Python module referenced in `pyproject.toml`. Never use the kebab-case outer name in your entrypoint.

---

## Step 4: Configure `pyproject.toml`

```toml
[build-system]
requires = ["setuptools"]
build-backend = "setuptools.backends.legacy:build"

[project]
name = "fermentation-controller"
version = "0.1.0"
description = "Proportional DO controller for fermentation reactor"
dependencies = [
    "amesa-core",
]

[amesa]
type = "skill-controller"
entrypoint = "fermentation_controller.controller:FermentationController"
```

### Field Reference

| Field          | Where       | Required | Description                                                  |
| -------------- | ----------- | -------- | ------------------------------------------------------------ |
| `name`         | `[project]` | Yes      | Artifact name as it will appear in the registry. Kebab-case. |
| `version`      | `[project]` | Yes      | Semantic version string.                                     |
| `description`  | `[project]` | Yes      | Short human-readable description.                            |
| `dependencies` | `[project]` | Yes      | Must include `"amesa-core"`.                                 |
| `type`         | `[amesa]`   | Yes      | Must be `"skill-controller"`.                                |
| `entrypoint`   | `[amesa]`   | Yes      | `inner_module.filename:ClassName`                            |

> **Do not add a `variables` field.** The `variables` field is for perceptors only. Including it in a skill `pyproject.toml` causes a validation error on publish.

### Entrypoint Format

| Part           | Value in this example                                  |
| -------------- | ------------------------------------------------------ |
| `inner_module` | `fermentation_controller` (inner snake_case directory) |
| `filename`     | `controller` (the `.py` file, without extension)       |
| `ClassName`    | `FermentationController`                               |

**Full entrypoint:** `fermentation_controller.controller:FermentationController`

---

## Step 5: Verify Your Directory

```text
fermentation-controller/
├── fermentation_controller/
│   ├── __init__.py        ← must exist; must be empty
│   └── controller.py      ← contains FermentationController class
└── pyproject.toml         ← contains [amesa] section with type and entrypoint
```

Checklist:

- [ ] `__init__.py` exists and is empty
- [ ] `pyproject.toml` is in the outer directory (same level as `fermentation_controller/`)
- [ ] `type` in `[amesa]` is `"skill-controller"`
- [ ] `entrypoint` uses the inner snake_case module name
- [ ] `entrypoint` class name matches the class in `controller.py`
- [ ] All four required methods are implemented with `async def`
- [ ] `__init__` takes no required arguments
- [ ] No `variables` field in `[amesa]`
- [ ] All imports use `from amesa_core import ...`

---

## Step 6: Publish

```bash
amesa skill publish ./fermentation-controller/
```

Or using the flag form:

```bash
amesa skill publish --path ./fermentation-controller/
```

The path must point to the **outer kebab-case directory** containing `pyproject.toml`.

---

## Step 7: Confirm the Publish

```bash
amesa skill list
```

| Name                    | Type       | Version | Description                   | UUID |
| ----------------------- | ---------- | ------- | ----------------------------- | ---- |
| fermentation-controller | controller | 1       | Proportional DO controller... | ...  |

---

## Using a Controller in an Agent

Controllers can be registered in-process the same way as teachers:

```python
from amesa_core import Agent, Skill, Sensor
from fermentation_controller.controller import FermentationController

agent = Agent()
agent.add_sensors([
    Sensor("dissolved_oxygen", "Dissolved oxygen fraction [0..1]"),
    Sensor("agitation_rpm",    "Agitator speed in RPM"),
])

# Pass the CLASS — not an instance
skill = Skill("fermentation-ctrl", FermentationController)
agent.add_skill(skill)
```

---

## Updating a Published Controller

Increment `version` in `pyproject.toml` and republish:

```bash
amesa skill publish ./fermentation-controller/
```

## Deleting a Controller

```bash
amesa skill delete
```

---

## Troubleshooting

### `TypeError` during episode reset

Your `__init__` has a required argument. The framework calls `MyController()` with no arguments at every episode boundary:

```python
# WRONG — threshold has no default, raises TypeError on reset
def __init__(self, threshold: float):
    self.threshold = threshold

# CORRECT — provide a default value
def __init__(self, threshold: float = 0.65):
    self.threshold = threshold
```

### `ModuleNotFoundError` on publish

The entrypoint is using the kebab-case outer directory name:

```toml
# WRONG
entrypoint = "fermentation-controller.controller:FermentationController"

# CORRECT
entrypoint = "fermentation_controller.controller:FermentationController"
```

### Action type mismatch at runtime

`compute_action` must return a value in the format the simulator expects. Returning a plain `float` when the simulator expects a list, or vice versa, causes a coercion error. Check your simulator's action space and match the return type accordingly.

### Legacy import error

```python
# WRONG
from composabl import SkillController

# CORRECT
from amesa_core import SkillController
```
