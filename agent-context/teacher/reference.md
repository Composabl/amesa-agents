# AgentTeacher Interface

`AgentTeacher` is the ML-training interface for a `Agent`.

Source of truth: `amesa_core/orchestration/agent/agent_teacher.py`. It is also exported at the top
level (`from amesa_core import AgentTeacher`). Abstract (must override, as `async def`):
`compute_reward`, `compute_success_criteria`, `transform_action`, `filtered_sensor_space`.
`amesa agent validate` fails if one is missing or not `async` (`utils/validate_util.py`,
`validate_abstract_class_implementation`).

## Call order per step (V2 trainer, `amesa_train/v2/agent_processor_component.py` `compute_step`)

1. `transform_sensors(sensors, None)` — the action argument is always `None` here.
2. `compute_reward` / `compute_success_criteria` / `compute_termination` are called with the
   **previous** action (the one that produced this observation). Skipped on the reset step.
3. If success **or** termination is `True`, the episode ends on this observation and no new action
   is computed.
4. Otherwise `compute_action_mask(transformed_sensors, previous_action)`, policy inference, then
   `transform_action(transformed_sensors, action)` (action already rescaled to the action-space bounds).

`reset()` runs at the start of every episode; `filtered_sensor_space()`,
`get_custom_action_space()` and `compute_scenario_advancement()` are read once when the
observation/action schema is built. `is_compute_done()` is **not** called by the V2 training loop.

## Full scaffold

```python
import numpy as np
from amesa_core.orchestration.agent.agent_teacher import AgentTeacher
from typing import Dict, List

class MyTeacher(AgentTeacher):
    # required
    async def compute_reward(self, transformed_sensors: Dict, action, sim_reward: float) -> float:
        """Shape the learning signal used by the trainer.

        :param transformed_sensors: Post-:meth:`transform_sensors` sensor dict.
        :type transformed_sensors: Dict
        :param action: Policy output shaped to the action space.
        :param sim_reward: Simulator reward for the current step.
        :type sim_reward: float
        :returns: Scalar reward for policy optimization.
        :rtype: float
        :raises NotImplementedError: if not overridden in the subclass.
        """
        error = abs(float(transformed_sensors["error"][0]))
        return float(-error)

    # required
    async def compute_success_criteria(self, transformed_sensors: Dict, action) -> bool:
        """Define when the objective has been achieved.

        :param transformed_sensors: Post-:meth:`transform_sensors` sensor dict.
        :type transformed_sensors: Dict
        :param action: Policy output shaped to the action space.
        :returns: ``True`` when the episode should count as success.
        :rtype: bool
        :raises NotImplementedError: if not overridden in the subclass.
        """
        return abs(float(transformed_sensors["error"][0])) < 0.1

    # required
    async def transform_action(self, transformed_sensors: Dict, action):
        """Convert policy output into simulator-consumable action format.

        :param transformed_sensors: Post-:meth:`transform_sensors` sensor dict.
        :type transformed_sensors: Dict
        :param action: Raw policy output.
        :returns: Action in the format expected by the simulator.
        :raises NotImplementedError: if not overridden in the subclass.
        """
        return action

    # required
    async def filtered_sensor_space(self) -> List[str]:
        """Declare which sensor keys the policy observes.

        Every key must be a sim sensor or a perceptor output. Keys derived only
        inside :meth:`transform_sensors` (like ``error`` below) are NOT part of
        the observation space and are reported as missing.

        :returns: List of sensor key strings.
        :rtype: List[str]
        :raises NotImplementedError: if not overridden in the subclass.
        """
        return ["value", "target"]

    # optional
    async def transform_sensors(self, sensors, action) -> Dict:
        """Build derived sensor features before teacher logic runs.

        Sensors arrive as ``np.ndarray`` values (usually shape ``(1,)``).
        Keep every key listed in :meth:`filtered_sensor_space` and keep its
        shape matching the sensor space; extra derived keys (``error``) are
        visible to reward/success logic but not to the policy.

        :param sensors: Sensor dict (sim sensors + perceptor outputs).
        :param action: Always ``None`` when called by the trainer.
        :returns: Transformed sensor dict.
        :rtype: Dict
        """
        value = float(sensors["value"])
        target = float(sensors["target"])
        error = value - target
        return {
            **sensors,
            "value": np.array([value], dtype=np.float32),
            "target": np.array([target], dtype=np.float32),
            "error": np.array([error], dtype=np.float32),
        }

    # optional
    async def compute_termination(self, transformed_sensors: Dict, action) -> bool:
        """End episodes on failure, safety, or timeout conditions.

        :param transformed_sensors: Post-:meth:`transform_sensors` sensor dict.
        :type transformed_sensors: Dict
        :param action: Policy output shaped to the action space.
        :returns: ``True`` when the episode should terminate early.
        :rtype: bool
        """
        return float(transformed_sensors["value"][0]) > 100.0

    # optional
    async def compute_action_mask(self, transformed_sensors: Dict, action) -> List[bool]:
        """Restrict valid actions for the current step.

        Disables the ``increase`` action (index 1) when the value is already
        within the success band, preventing unnecessary exploration.

        :param transformed_sensors: Post-:meth:`transform_sensors` sensor dict.
        :type transformed_sensors: Dict
        :param action: Current action.
        :returns: Boolean mask of length ``n_actions`` (``Discrete`` example),
            or ``None`` (the default) for no mask.
        :rtype: List[bool]
        :raises ValueError: if the returned mask length differs from the action
            space size (e.g., ``n`` for ``Discrete(n)``, ``N*2`` for
            ``Box(shape=(N,))``).
        """
        error = float(transformed_sensors["error"][0])
        at_target = abs(error) < 0.1
        # Discrete(2): [decrease, increase]
        return [True, not at_target]

    # optional
    async def get_custom_action_space(self):
        """Return a custom action space for this agent's policy.

        When provided, the policy trains against this space instead of the
        simulator's native action space. :meth:`transform_action` is then
        responsible for mapping policy output back to the sim's format.

        :returns: A space definition (e.g. ``Box``, ``Discrete``) for the
            custom action space, or ``None`` to use the simulator's action
            space (default).
        """
        return None  # replace with e.g. Box(low=-1, high=1, shape=(1,))

    # optional
    async def compute_scenario_advancement(self) -> Dict:
        """When a scenario is mastered and training moves to the next one.

        Default: success rate >= 0.8 over the last 100 completed episodes.
        ``amesa agent validate`` checks the returned dict: only these two
        keys, ``0 < scenario_success_rate <= 1``, ``scenario_success_window``
        an ``int > 0``; invalid values are dropped for the defaults at
        training time (``networking/remote_agent/curriculum.py``).
        """
        return {"scenario_success_rate": 0.8, "scenario_success_window": 100}

    # optional
    async def reset(self):
        """Called at the start of each episode; clear per-episode state here."""
        pass

    # optional (legacy)
    async def is_compute_done(self, transformed_sensors: Dict, action) -> bool:
        """Combined done signal (legacy).

        The base returns ``True`` only when both :meth:`compute_success_criteria`
        **and** :meth:`compute_termination` are ``True``. The V2 trainer does
        not call it: it ends the episode when either one is ``True``.

        :param transformed_sensors: Post-:meth:`transform_sensors` sensor dict.
        :type transformed_sensors: Dict
        :param action: Policy output shaped to the action space.
        :returns: ``True`` when the episode is done.
        :rtype: bool
        """
        return (
            await self.compute_success_criteria(transformed_sensors, action)
            and await self.compute_termination(transformed_sensors, action)
        )

    # optional
    def add_scenario(self, scenario) -> None:
        """Associate a scenario with this teacher.

        Stores ``scenario``
        on ``self.scenario``. Override to react to scenario changes at setup
        time; most teachers can use the default.

        :param scenario: The ``Scenario`` instance provided by the framework.
        """
        self.scenario = scenario
```

## Action mask shape reminders

- `Discrete(n)`: length `n`
- `Box(shape=(N,))`: length `N*2` (mean/std pairs)
- `Tuple`: tuple/list per sub-space
- `Dict`: dict keyed by action-space keys
