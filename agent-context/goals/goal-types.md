# Goal Types

All imports below are from `amesa_core.orchestration.agent.goals.<module>` (or `from amesa_core.orchestration.agent.goals import ...`). Every constructor takes `sensor` as the first positional argument and `name` as the second.

Reward formulas use `error = (sensor - target) ** 2` (`Goal.compute_error`). "In boundary" means `boundary_left <= value <= boundary_right` and is always `False` unless **both** boundaries are set (`Goal.is_in_boundary`).

## `ApproachGoal`

Drive a sensor toward a target. Reward is `-log10(error + 1e-9) / 8`, plus `scale` while in boundary. **Success = in boundary** (`tolerance` is not used for success). `compute_termination` always returns `False`.

```python
from amesa_core.orchestration.agent.goals.approach_goal import ApproachGoal

goal = ApproachGoal(
    sensor="position",
    target=5.0,
    boundary_left=4.9,     # success band; required for success
    boundary_right=5.1,
    scale=1.0,             # bonus added while in boundary
)
```

## `AvoidGoal`

Keep a sensor away from a target / region. Reward is `log10(error + 1e-9) / 8 + 1`, minus `scale` while in boundary. The boundary is the region to **avoid**. Never succeeds. Terminates while in boundary only if `should_terminate_in_boundary=True` (constructor default `False`).

```python
from amesa_core.orchestration.agent.goals.avoid_goal import AvoidGoal

goal = AvoidGoal(
    sensor="obstacle_distance",
    target=0.0,
    boundary_left=-0.5,
    boundary_right=0.5,
    should_terminate_in_boundary=True,
)
```

## `MaintainGoal`

Reward staying near a target band. Same reward as `ApproachGoal` (`-log10(error + 1e-9) / 8`, plus `scale` in boundary). Never succeeds, never terminates (`can_terminate()` is `False`).

```python
from amesa_core.orchestration.agent.goals.maintain_goal import MaintainGoal

goal = MaintainGoal(
    sensor="pole_theta",
    target=0.0,
    boundary_left=-0.418,
    boundary_right=0.418,
    scale=1.0,
)
```

## `MaximizeGoal`

Reward larger values of a sensor. The reward is a squashed transform of the value (`-tanh(...) + 1`, linearly interpolated from 0.915 to 1.085 for values in `[-5, 5]`), not the raw value. `target` defaults to `np.inf`. Never succeeds, never terminates.

```python
from amesa_core.orchestration.agent.goals.maximize_goal import MaximizeGoal

goal = MaximizeGoal(sensor="score", scale=1.0)
```

## `MinimizeGoal`

Mirror of `MaximizeGoal` for smaller values (interpolated from 1.085 down to 0.915 on `[-5, 5]`). `target` defaults to `-np.inf`. Never succeeds, never terminates.

```python
from amesa_core.orchestration.agent.goals.minimize_goal import MinimizeGoal

goal = MinimizeGoal(sensor="energy_use", scale=1.0)
```

> `stop_steps` / `stop_value` are accepted by every goal, but all five concrete goals override `compute_termination`, so they have no effect on termination (see `quirks.md`).

## Choosing quickly

- Reach setpoint: `ApproachGoal` (set both boundaries)
- Stay in safe corridor: `MaintainGoal` + `AvoidGoal`
- Push metric up/down continuously: `MaximizeGoal` / `MinimizeGoal`
