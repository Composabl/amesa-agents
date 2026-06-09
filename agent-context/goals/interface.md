# Goal Interface

Goals are reusable `SkillTeacher` subclasses that provide reward/success/termination logic.

## Full scaffold

```python
from amesa_core.agent.skill.goals.maintain_goal import MaintainGoal
from typing import Dict, List

class BalanceTeacher(MaintainGoal):
    def __init__(self):
        super().__init__(
            sensor="pole_theta",
            target=0.0,
            boundary_left=-0.418,
            boundary_right=0.418,
            scale=1.0,
        )

    # REQUIRED: Declare the sensors this goal-backed teacher reads.
    async def filtered_sensor_space(self) -> List[str]:
        return ["pole_theta", "pole_alpha", "cart_pos", "cart_vel"]

    # REQUIRED: Convert policy output to simulator action format.
    async def transform_action(self, transformed_sensors: Dict, action):
        return action

    # OPTIONAL: Precompute derived features before goal logic executes.
    async def transform_sensors(self, sensors, action) -> Dict:
        return sensors

    # OPTIONAL: Override the concrete goal's default reward behavior.
    async def compute_reward(self, transformed_sensors: Dict, action, sim_reward: float) -> float:
        return await super().compute_reward(transformed_sensors, action, sim_reward)

    # OPTIONAL: Override the concrete goal's default success behavior.
    async def compute_success_criteria(self, transformed_sensors: Dict, action) -> bool:
        return await super().compute_success_criteria(transformed_sensors, action)

    # OPTIONAL: Override the concrete goal's default termination behavior.
    async def compute_termination(self, transformed_sensors: Dict, action) -> bool:
        return await super().compute_termination(transformed_sensors, action)
```

## Methods and intended use

When subclassing a concrete goal (`ApproachGoal`, `MaintainGoal`, etc.) as a teacher:

### `filtered_sensor_space(self) -> list[str]` (required)

Declares the sensor keys the goal-teacher depends on. Use it to keep observation inputs explicit and minimal.

### `transform_action(self, transformed_sensors, action)` (required)

Converts policy outputs into simulator-compatible action format.

### `transform_sensors(self, sensors, action) -> dict` (optional)

Builds derived features before reward/success/termination are evaluated.

### `compute_reward(self, transformed_sensors, action, sim_reward) -> float` (optional)

Overrides the concrete goal's reward logic when you need custom shaping beyond the goal default.

### `compute_success_criteria(self, transformed_sensors, action) -> bool` (optional)

Overrides goal success semantics for task-specific completion behavior.

### `compute_termination(self, transformed_sensors, action) -> bool` (optional)

Overrides default termination behavior for safety limits, timeout, or failure conditions.

Most users keep goal reward/success/termination defaults and only implement filtering/transforms.

## Base `Goal` constructor parameters

All goal types share these constructor parameters:

- `sensor`: required sensor name or `Sensor`
- `name`: optional display name
- `target`: number, sensor name, `Sensor`, or `None`
- `tolerance`: success band width
- `stop_value`: optional value-driven termination
- `stop_steps`: optional step-driven termination
- `boundary_left` / `boundary_right`: optional bounds used for boundary checks
- `boundary_is_relative`: apply boundary to error (`sensor - target`) instead of raw sensor
- `scale`: reward scaling factor

## Shared helper methods

```python
async def is_in_boundary(self, transformed_sensors: dict) -> bool
async def compute_error(self, transformed_sensors: dict) -> float
async def get_sensor_value(self, transformed_sensors: dict) -> float
async def get_target_value(self, transformed_sensors: dict) -> float
```

## Important behaviors

- `target=None` requires both boundaries and resolves to midpoint.
- `steps_taken` increments on reward calls and is not auto-reset per episode.
