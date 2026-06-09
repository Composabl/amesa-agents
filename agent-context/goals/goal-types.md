# Goal Types

## `ApproachGoal`

Drive sensor values toward a target and report success once in boundary/tolerance.

```python
from amesa_core.agent.skill.goals.approach_goal import ApproachGoal

goal = ApproachGoal(
    sensor="position",
    target=5.0,
    tolerance=0.1,
    boundary_left=4.9,
    boundary_right=5.1,
    scale=1.0,
)
```

## `AvoidGoal`

Penalize entering risky regions; contributes termination rather than success.

```python
from amesa_core.agent.skill.goals.avoid_goal import AvoidGoal

goal = AvoidGoal(
    sensor="obstacle_distance",
    target=0.0,
    boundary_left=-0.5,
    boundary_right=0.5,
    should_terminate_in_boundary=True,
)
```

## `MaintainGoal`

Reward staying near a target band; does not inherently succeed.

```python
from amesa_core.agent.skill.goals.maintain_goal import MaintainGoal

goal = MaintainGoal(
    sensor="pole_theta",
    target=0.0,
    boundary_left=-0.418,
    boundary_right=0.418,
    scale=1.0,
)
```

## `MaximizeGoal`

Reward larger values for a target sensor.

```python
from amesa_core.agent.skill.goals.maximize_goal import MaximizeGoal

goal = MaximizeGoal(sensor="score", stop_steps=1000, scale=1.0)
```

## `MinimizeGoal`

Reward smaller values for a target sensor.

```python
from amesa_core.agent.skill.goals.minimize_goal import MinimizeGoal

goal = MinimizeGoal(sensor="energy_use", stop_steps=1000, scale=1.0)
```

## Choosing quickly

- Reach setpoint: `ApproachGoal`
- Stay in safe corridor: `MaintainGoal` + `AvoidGoal`
- Push metric up/down continuously: `MaximizeGoal` / `MinimizeGoal`
