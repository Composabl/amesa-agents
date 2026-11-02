# CoordinatedGoal and AgentCoach

`CoordinatedGoal` combines multiple goals inside **one** teacher with a strategy (`AND`, `OR`, `THEN`). `AgentCoach` (bottom of this page) coordinates **several agents** in an `AgentCoordinatedSet`.

## Constructor

```python
CoordinatedGoal(
    goals: list,
    goals_coordination_strategy=GoalCoordinationStrategy.AND,
    weights: list | None = None,
)
```

- `goals`: ordered list of goal instances (may include nested `CoordinatedGoal`s).
- `goals_coordination_strategy`: `GoalCoordinationStrategy.AND` (1), `.OR` (2), `.THEN` (3) — plain int constants, not an `Enum`.
- `weights`: optional per-goal multipliers; `None`/empty defaults to all `1`; otherwise length must match `len(goals)` (`ValueError`).
- `CoordinatedGoal.__init__` does not call `Goal.__init__`, so the wrapper has no `sensor`/`name`/`target` of its own.

## Scaffolded teacher example

```python
from amesa_core.orchestration.agent.goals.coordinated_goal import CoordinatedGoal, GoalCoordinationStrategy
from amesa_core.orchestration.agent.goals.maintain_goal import MaintainGoal
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

## Strategy behavior (reward)

- `AND`: weighted sum `sum(weight_i * reward_i)`.
- `OR`: `max(0, reward_1, ..., reward_n)` — unweighted, and negative child rewards are clipped to 0.
- `THEN`: returns the reward of the **first goal (in order) whose `compute_success_criteria` is currently true**; if none is true the reward is `0`. Weights are ignored.
- `compute_reward(..., return_individual=True)` returns `(reward, {goal_name: reward})` for AND/OR (not for THEN).

## Termination and success details (all strategies)

- Success: `True` only if there is at least one direct `ApproachGoal` child and **all** direct `ApproachGoal` children succeed. Other goal types (and nested `CoordinatedGoal`s) are ignored.
- Termination: `True` if any direct `AvoidGoal` child terminates (needs `should_terminate_in_boundary=True`). Other types are ignored.
- `filtered_sensor_space()` concatenates the children's lists; the stock goals return `None`, so override it in your subclass.
- Using `MaximizeGoal`, `MaintainGoal` or `MinimizeGoal` with `THEN` only logs a warning — they never succeed, so they never "unlock" anything.

## AgentCoach

`AgentCoach` (`amesa_core.orchestration.agent.agent_coach`, also `from amesa_core import AgentCoach`) is an ABC, not a `Goal`/`AgentTeacher`. It is used as `AgentCoordinatedSet(name, CoachCls)` / `AgentCoordinatedPopulation`; each child agent keeps its own teacher.

```python
from typing import Dict
from amesa_core.orchestration.agent.agent_coach import AgentCoach

class MyCoach(AgentCoach):
    def __init__(self, *args, **kwargs):        # instantiated with no arguments
        super().__init__()

    # required (abstract)
    async def compute_reward(self, transformed_sensors: Dict, action, sim_reward) -> float: ...
    async def compute_success_criteria(self, transformed_sensors: Dict, action) -> bool: ...
    async def compute_termination(self, transformed_sensors: Dict, action) -> bool: ...

    # optional (defaults shown)
    async def compute_action_mask(self, transformed_sensors: Dict, action): return None
    async def transform_action(self, transformed_sensors: Dict, action): return action
    async def transform_sensors(self, sensors, action): return sensors
    async def is_compute_done(self, transformed_sensors, action) -> bool:  # success OR termination
        ...
```

How the trainer calls it (`amesa_train/agent_processors/agent_coordinated_set_processor.py`, same in `..._population_processor.py`):

- `compute_reward(multi_sensors, action, multi_reward)`: all three are dicts keyed by child agent name (`multi_reward` = each child's teacher reward). The return value is **added to every child's reward**, so return a scalar — returning a dict breaks training (despite the base-class docstring).
- `compute_success_criteria` / `is_compute_done` receive the raw sim sensors keyed by child agent name. Episode ends when `is_compute_done` (success **or** termination) or the sim terminates.
- `transform_action` receives the dict of child actions. `transform_sensors` and `compute_action_mask` are not called by these processors.

Example: [`agents/teachers/coordinated-example/`](../../agents/teachers/coordinated-example/).
