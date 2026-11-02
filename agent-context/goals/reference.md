# Goal Interface

Goals are reusable `AgentTeacher` subclasses (through the abstract `Goal` base in `amesa_core/orchestration/agent/goals/goal.py`) that provide reward/success/termination logic. All hooks are `async`.

The platform instantiates your entrypoint class with **no arguments** (`agent.py:get_impl_cls_instance`, `validate_util.py`), so subclass a goal and configure it inside a zero-argument `__init__`.

## Full scaffold

```python
import numpy as np
from amesa_core.orchestration.agent.goals.maintain_goal import MaintainGoal
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

    # optional (Goal default returns None; override to declare sensors)
    async def filtered_sensor_space(self) -> List[str]:
        """Declare the sensors this goal-backed teacher reads.

        :returns: List of sensor key strings.
        :rtype: List[str]
        """
        return ["pole_theta", "pole_alpha", "cart_pos", "cart_vel"]

    # optional (Goal default returns action unchanged)
    async def transform_action(self, transformed_sensors: Dict, action):
        """Convert policy output to simulator action format.

        :param transformed_sensors: Post-:meth:`transform_sensors` sensor dict.
        :type transformed_sensors: Dict
        :param action: Raw policy output.
        :returns: Action in the format expected by the simulator.
        """
        return action

    # optional
    async def transform_sensors(self, sensors, action) -> Dict:
        """Precompute derived features before goal logic executes.

        Wraps each sensor in a ``np.ndarray`` so the framework can call
        ``.flatten()`` when building the observation vector.

        :param sensors: Raw sensor dict from the environment.
        :param action: Current action.
        :returns: Transformed sensor dict.
        :rtype: Dict
        """
        return {
            **sensors,
            "pole_theta": np.array([float(sensors.get("pole_theta", 0.0))], dtype=np.float32),
            "pole_alpha": np.array([float(sensors.get("pole_alpha", 0.0))], dtype=np.float32),
            "cart_pos":   np.array([float(sensors.get("cart_pos",   0.0))], dtype=np.float32),
            "cart_vel":   np.array([float(sensors.get("cart_vel",   0.0))], dtype=np.float32),
        }

    # optional
    async def compute_reward(self, transformed_sensors: Dict, action, sim_reward: float) -> float:
        """Override the concrete goal's default reward behavior.

        Delegates to :meth:`MaintainGoal.compute_reward` by default.

        :param transformed_sensors: Post-:meth:`transform_sensors` sensor dict.
        :type transformed_sensors: Dict
        :param action: Policy output shaped to the action space.
        :param sim_reward: Simulator reward for the current step.
        :type sim_reward: float
        :returns: Scalar reward.
        :rtype: float
        """
        return await super().compute_reward(transformed_sensors, action, sim_reward)

    # optional
    async def compute_success_criteria(self, transformed_sensors: Dict, action) -> bool:
        """Override the concrete goal's default success behavior.

        Delegates to :meth:`MaintainGoal.compute_success_criteria` by default.

        :param transformed_sensors: Post-:meth:`transform_sensors` sensor dict.
        :type transformed_sensors: Dict
        :param action: Policy output shaped to the action space.
        :returns: ``True`` when the goal success condition is met.
        :rtype: bool
        """
        return await super().compute_success_criteria(transformed_sensors, action)

    # optional
    async def compute_termination(self, transformed_sensors: Dict, action) -> bool:
        """Override the concrete goal's default termination behavior.

        Delegates to :meth:`MaintainGoal.compute_termination` by default.

        :param transformed_sensors: Post-:meth:`transform_sensors` sensor dict.
        :type transformed_sensors: Dict
        :param action: Policy output shaped to the action space.
        :returns: ``True`` when the episode should terminate.
        :rtype: bool
        """
        return await super().compute_termination(transformed_sensors, action)
```

## Base `Goal` constructor parameters

All goal types share these constructor parameters (`Goal.__init__`; defaults shown):

- `sensor`: required sensor name (`str`) or `Sensor`; anything else raises `TypeError`
- `name=""`: optional display name (used as the key in `CoordinatedGoal` individual rewards)
- `target=None`: number, sensor name, `Sensor`, or `None` (`MaximizeGoal` defaults to `np.inf`, `MinimizeGoal` to `-np.inf`)
- `tolerance=0.1`: must be a number; only used by the base `Goal.compute_termination`, which every concrete goal overrides — it does **not** define the success band
- `stop_value=None`, `stop_steps=None`: only read by the base `Goal.compute_termination`; no effect on the concrete goals
- `boundary_left=None` / `boundary_right=None`: bounds used by `is_in_boundary` (success for `ApproachGoal`, bonus/penalty for Approach/Maintain/Avoid, termination for `AvoidGoal`)
- `boundary_is_relative=False`: apply boundary to `sensor - target` instead of the raw sensor
- `scale=1.0`: bonus (Approach/Maintain) or penalty (Avoid) applied while in boundary; unused by Maximize/Minimize reward

`AvoidGoal` adds `should_terminate_in_boundary=False`.

## Shared helper methods

```python
async def is_in_boundary(self, transformed_sensors: dict) -> bool
async def compute_error(self, transformed_sensors: dict) -> float   # (sensor - target) ** 2
async def get_sensor_value(self, transformed_sensors: dict) -> float  # sums iterables (arrays)
async def get_target_value(self, transformed_sensors: dict) -> float
def can_terminate(self) -> bool   # sync; True for Approach/Avoid, False for Maintain/Maximize/Minimize
def to_json(self) -> dict          # sync; see job-json-schema.md
```

Inherited `AgentTeacher` hooks you may still override: `compute_action_mask`, `compute_scenario_advancement`, `get_custom_action_space`, `reset` (all `async`).

## Important behaviors

- `target=None` requires both boundaries (else `ValueError`), resolves to their midpoint, and forces `boundary_is_relative=False`.
- `steps_taken` only increments in `Goal.compute_reward`; of the concrete goals only `MinimizeGoal` calls it, and it is never reset per episode.
- Success/termination per goal: Approach succeeds in boundary; Avoid terminates in boundary when `should_terminate_in_boundary=True`; Maintain/Maximize/Minimize never succeed or terminate.
