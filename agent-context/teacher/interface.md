# SkillTeacher Interface

`SkillTeacher` is the ML-training interface for a `Skill`.

## Full scaffold

```python
from amesa_core.agent.skill.skill_teacher import SkillTeacher
from typing import Dict, List

class MyTeacher(SkillTeacher):
    # REQUIRED: Shape the learning signal used by the trainer.
    async def compute_reward(self, transformed_sensors: Dict, action, sim_reward: float) -> float:
        error = abs(float(transformed_sensors.get("error", 0.0)))
        return float(-error)

    # REQUIRED: Define when the objective has been achieved.
    async def compute_success_criteria(self, transformed_sensors: Dict, action) -> bool:
        return abs(float(transformed_sensors.get("error", 1.0))) < 0.1

    # REQUIRED: Convert policy output into simulator-consumable action format.
    async def transform_action(self, transformed_sensors: Dict, action):
        return action

    # REQUIRED: Declare which sensor keys this teacher reads.
    async def filtered_sensor_space(self) -> List[str]:
        return ["value", "target", "error"]

    # OPTIONAL: Build derived sensor features before teacher logic runs.
    # default: sensors
    async def transform_sensors(self, sensors, action) -> Dict:
        return sensors

    # OPTIONAL: End episodes on failure/safety/timeout conditions.
    # default: False
    async def compute_termination(self, transformed_sensors: Dict, action) -> bool:
        return float(transformed_sensors.get("value", 0.0)) > 100.0

    # OPTIONAL: Restrict valid actions for the current step.
    # default: None
    async def compute_action_mask(self, transformed_sensors: Dict, action):
        return None

    # OPTIONAL: Override the trainer action-space definition.
    # default: None
    async def get_custom_action_space(self):
        return None
```

## Methods and intended use

### `compute_reward(self, transformed_sensors, action, sim_reward) -> float` (required)

Computes the scalar reward used for policy optimization. Use it for reward shaping, penalties, and blending simulator reward with task-specific objectives.

### `compute_success_criteria(self, transformed_sensors, action) -> bool` (required)

Declares when the current episode should count as success. Use it for thresholds, compound checks, or milestone-based completion.

### `transform_action(self, transformed_sensors, action)` (required)

Converts policy output into the exact action format expected by the simulator. Use it for scaling, clipping, remapping, and structural conversion.

### `filtered_sensor_space(self) -> list[str]` (required)

Defines the teacher's sensor dependencies. Use it to keep observation requirements explicit and minimal.

### `transform_sensors(self, sensors, action) -> dict` (optional)

Preprocesses raw sensors into transformed features shared by reward/success/termination. Use it for normalization, coordinate transforms, and feature engineering.

> **Important:** Values returned for keys listed in `filtered_sensor_space` must be array-like (e.g., `np.ndarray`), not plain Python `float` or `int`. The framework calls `.flatten()` on these values when building the observation vector — returning a bare scalar will raise `'float' object has no attribute 'flatten'`. If you need to remap or wrap a sensor value (e.g., angle wrapping), return `np.array([new_value], dtype=np.float32)` rather than a raw float. Derived keys that are *not* in `filtered_sensor_space` (e.g., normalized scalars used only in reward shaping) may be any Python type.

### `compute_termination(self, transformed_sensors, action) -> bool` (optional)

Signals episode termination for non-success reasons such as failure, timeout, or safety boundaries.

### `compute_action_mask(self, transformed_sensors, action)` (optional)

Builds dynamic action constraints for the current state. Use it to disable invalid actions and enforce runtime feasibility.

### `get_custom_action_space(self)` (optional)

Overrides the default trainer action space when your policy output contract needs a custom structure or bounds.

## Method contracts

- `transformed_sensors`: post-`transform_sensors` sensor dict.
- `action`: policy output shaped to action space.
- `sim_reward`: simulator reward for the current step.
- `compute_reward` **must** return a Python `float`.
- `filtered_sensor_space()` returns the exact sensor keys this teacher consumes.

## Action mask shape reminders

- `Discrete(n)`: length `n`
- `Box(shape=(N,))`: length `N*2` (mean/std pairs)
- `Tuple`: tuple/list per sub-space
- `Dict`: dict keyed by action-space keys
