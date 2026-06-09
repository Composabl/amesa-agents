# CoordinatedGoal

`CoordinatedGoal` combines multiple goals with a strategy (`AND`, `OR`, `THEN`).

## Constructor

```python
CoordinatedGoal(
    goals: list,
    goals_coordination_strategy=GoalCoordinationStrategy.AND,
    weights: list | None = None,
)
```

- `goals`: ordered list of goal instances.
- `goals_coordination_strategy`: coordination constant.
- `weights`: optional per-goal multipliers; length must match `len(goals)`.

## Scaffolded teacher example

```python
from amesa_core.agent.skill.goals.coordinated_goal import CoordinatedGoal, GoalCoordinationStrategy
from amesa_core.agent.skill.goals.maintain_goal import MaintainGoal
from typing import Dict, List

class CartpoleTeacher(CoordinatedGoal):
    def __init__(self):
        pole_goal = MaintainGoal(
            "pole_theta",
            name="keep pole upright",
            target=0.0,
            boundary_left=-0.418,
            boundary_right=0.418,
            scale=2.0,
        )
        cart_goal = MaintainGoal(
            "cart_pos",
            name="keep cart centered",
            target=0.0,
            boundary_left=-2.4,
            boundary_right=2.4,
            scale=1.0,
        )
        super().__init__(
            goals=[pole_goal, cart_goal],
            goals_coordination_strategy=GoalCoordinationStrategy.AND,
            weights=[2.0, 1.0],
        )

    async def filtered_sensor_space(self) -> List[str]:
        return ["cart_pos", "cart_vel", "pole_theta", "pole_alpha"]

    async def transform_sensors(self, sensors, action) -> Dict:
        return sensors

    async def transform_action(self, transformed_sensors: Dict, action):
        return action
```

## Strategy behavior

- `AND`: weighted sum reward; success requires all `ApproachGoal` children to succeed.
- `OR`: max single-goal reward; success still requires all `ApproachGoal` children.
- `THEN`: reward comes from the first unsatisfied goal in order.

## Termination and success details

- Success logic is driven by `ApproachGoal` members.
- Termination logic is driven by `AvoidGoal` members.
- Goal order matters for `THEN`.
- `ApproachGoal` and `AvoidGoal` are safe as leading goals in staged chains.
