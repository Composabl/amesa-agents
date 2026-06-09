# Coordinated Interface

`SkillCoach` defines reward/success/termination across a coordinated group of child skills.

## Full scaffold

```python
from amesa_core.agent.skill.skill_coach import SkillCoach
from typing import Dict

class MyCoach(SkillCoach):
    # REQUIRED: Return per-child rewards for coordinated learning.
    async def compute_reward(self, transformed_sensors: Dict, action, sim_reward):
        return {
            "striker": float(transformed_sensors.get("goal_proximity", 0.0)),
            "defender": float(-transformed_sensors.get("opponent_proximity", 0.0)),
        }

    # REQUIRED: Define success for the coordinated group as a whole.
    async def compute_success_criteria(self, transformed_sensors: Dict, action) -> bool:
        return bool(transformed_sensors.get("score", 0) > 5)

    # REQUIRED: Define coordinated termination logic for the full unit.
    async def compute_termination(self, transformed_sensors: Dict, action) -> bool:
        return bool(transformed_sensors.get("time_elapsed", 0) > 300)

    # OPTIONAL: Build transformed shared features from raw sensors.
    # default: sensors
    async def transform_sensors(self, sensors, action) -> Dict:
        return sensors

    # OPTIONAL: Rewrite child-action dict before env application.
    # default: action
    async def transform_action(self, transformed_sensors: Dict, action):
        return action

    # OPTIONAL: Mask invalid child actions at runtime.
    # default: None
    async def compute_action_mask(self, transformed_sensors: Dict, action):
        return None
```

## Methods and intended use

### `compute_reward(self, transformed_sensors, action, sim_reward) -> dict[str, float]` (required)

Computes reward for each child skill in the coordinated group. Use it to implement role-specific reward shaping while preserving a shared team objective.

### `compute_success_criteria(self, transformed_sensors, action) -> bool` (required)

Defines when the coordinated objective is complete. Use it for team-level milestones and aggregate success checks.

### `compute_termination(self, transformed_sensors, action) -> bool` (required)

Defines when the coordinated episode should stop, including failures, limits, or safety exits.

### `transform_sensors(self, sensors, action) -> dict` (optional)

Transforms shared observations before coordinated logic runs. Use it for feature extraction and normalization used by reward/success/termination.

### `transform_action(self, transformed_sensors, action) -> dict` (optional)

Rewrites or post-processes the per-child action dict before it is applied. Use it for clipping, remapping, and enforcing joint-action structure.

### `compute_action_mask(self, transformed_sensors, action)` (optional)

Returns dynamic constraints on allowable coordinated actions per step.

## Method contracts

- `compute_reward` returns per-child rewards.
- Reward dict keys must exactly match child skill names added to the coordinated set/population.
- Success and termination apply to the coordinated unit as a whole.
- `action` is a dict keyed by child skill name.
