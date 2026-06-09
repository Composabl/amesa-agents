# SkillController Interface

`SkillController` is the deterministic/rule-based interface for a `Skill`.

## Full scaffold

```python
from amesa_core.agent.skill.skill_controller import SkillController
from typing import Dict

class MyController(SkillController):
    # REQUIRED: Produce the simulator action from transformed sensors.
    async def compute_action(self, transformed_sensors: Dict, action):
        error = float(transformed_sensors.get("error", 0.0))
        control = -0.5 * error
        return [float(control)]

    # REQUIRED: Declare which sensor keys this controller reads.
    async def filtered_sensor_space(self):
        return ["value", "target", "error"]

    # REQUIRED: Define when the controlled behavior is successful.
    async def compute_success_criteria(self, transformed_sensors: Dict, action) -> bool:
        return abs(float(transformed_sensors.get("error", 1.0))) < 0.05

    # REQUIRED: Define when the episode should terminate.
    async def compute_termination(self, transformed_sensors: Dict, action) -> bool:
        return float(transformed_sensors.get("value", 0.0)) > 100.0

    # OPTIONAL: Derive controller-specific features from raw sensors.
    # default: sensors
    async def transform_sensors(self, sensors) -> Dict:
        return sensors

    # OPTIONAL: Restrict valid actions for the current state.
    # default: None
    async def compute_action_mask(self, transformed_sensors: Dict, action):
        return None
```

## Methods and intended use

### `compute_action(self, transformed_sensors, action)` (required)

Computes the control output applied to the simulator at each step. Use it for deterministic control laws, rule engines, and stateful policy logic.

### `filtered_sensor_space(self) -> list[str]` (required)

Declares the controller's sensor dependency set. Use it to explicitly limit observations to what control logic needs.

### `compute_success_criteria(self, transformed_sensors, action) -> bool` (required)

Defines success conditions for the controlled objective. Use it for tolerance bands, state goals, and composite completion checks.

### `compute_termination(self, transformed_sensors, action) -> bool` (required)

Defines termination conditions (for example safety limits, dead-ends, or max bounds). This is required for controllers.

### `transform_sensors(self, sensors) -> dict` (optional)

Preprocesses raw sensors before controller logic executes. Use it for normalization, derived features, and compact state construction.

### `compute_action_mask(self, transformed_sensors, action)` (optional)

Builds dynamic action validity constraints for the current state when action masking is supported.

## Method contracts

- `transformed_sensors`: post-`transform_sensors` sensor dict.
- `action`: previous action (useful for stateful controllers).
- `compute_action`: must return a value consumable by the sim action space.
- `transform_sensors` takes only `sensors` (no `action` argument).
