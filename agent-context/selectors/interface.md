# Selector Interface

A selector implementation is either a `SkillTeacher` subclass (learned selector) or a `SkillController` subclass (rule-based selector).

## Full scaffold (teacher selector)

```python
from amesa_core.agent.skill.skill_teacher import SkillTeacher
from typing import Dict, List

class MySelectorTeacher(SkillTeacher):
    # REQUIRED: reward for selector-policy training.
    async def compute_reward(self, transformed_sensors: Dict, action, sim_reward: float) -> float:
        return float(sim_reward)

    # REQUIRED: success condition for selector episode.
    async def compute_success_criteria(self, transformed_sensors: Dict, action) -> bool:
        return False

    # REQUIRED: convert policy output into selected child index.
    async def transform_action(self, transformed_sensors: Dict, action):
        return int(action)

    # REQUIRED: selector sensor dependencies.
    async def filtered_sensor_space(self) -> List[str]:
        return ["counter"]

    # OPTIONAL: preprocess sensors before selector logic.
    # default: sensors
    async def transform_sensors(self, sensors, action) -> Dict:
        return sensors

    # OPTIONAL: terminate selector episode.
    # default: False
    async def compute_termination(self, transformed_sensors: Dict, action) -> bool:
        return False

    # OPTIONAL: mask child-index actions; length must equal number of children.
    # default: None
    async def compute_action_mask(self, transformed_sensors: Dict, action):
        return None
```

## Full scaffold (controller selector)

```python
from amesa_core.agent.skill.skill_controller import SkillController
from typing import Dict, List

class MySelectorController(SkillController):
    # REQUIRED: choose child index directly.
    async def compute_action(self, transformed_sensors: Dict, action):
        return [0]  # selects first child

    # REQUIRED: selector sensor dependencies.
    async def filtered_sensor_space(self) -> List[str]:
        return ["counter"]

    # REQUIRED: success condition for selector run.
    async def compute_success_criteria(self, transformed_sensors: Dict, action) -> bool:
        return False

    # REQUIRED: termination condition for selector run.
    async def compute_termination(self, transformed_sensors: Dict, action) -> bool:
        return False

    # OPTIONAL: preprocess sensors before compute_action.
    # default: sensors
    async def transform_sensors(self, sensors) -> Dict:
        return sensors
```

## Selector-specific method behavior

### `transform_action(...)` (teacher selector, required)

Returns the selected child index. Capabilities include mapping policy outputs to child indices, clamping/validation, and deterministic fallback logic when needed.

### `compute_action(...)` (controller selector, required)

Returns the selected child index directly from rules/logic. Capabilities include threshold gates, finite-state routing, and deterministic orchestration.

### `compute_action_mask(...)` (teacher selector, optional)

Constrains which child indices are selectable at a step. Use this to disable unavailable child skills dynamically.

## Selector runtime contract

- Selector action space is always `Discrete(number_of_children)`.
- The selected index points into `config.children` order.
- Runtime returns the selected **child skill action** to the environment, not the selector index.
