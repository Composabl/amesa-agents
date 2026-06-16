# SkillTeacher Interface

`SkillTeacher` is the ML-training interface for a `Skill`.

## Full scaffold

```python
import numpy as np
from amesa_core.agent.skill.skill_teacher import SkillTeacher
from typing import Dict, List

class MyTeacher(SkillTeacher):
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
        """Declare which sensor keys this teacher reads.

        :returns: List of sensor key strings.
        :rtype: List[str]
        :raises NotImplementedError: if not overridden in the subclass.
        """
        return ["value", "target", "error"]

    # optional
    async def transform_sensors(self, sensors, action) -> Dict:
        """Build derived sensor features before teacher logic runs.

        Wraps each sensor listed in :meth:`filtered_sensor_space` in a
        ``np.ndarray`` so the framework can call ``.flatten()`` when building
        the observation vector. Also derives ``error`` so reward and success
        logic can read a single key.

        :param sensors: Raw sensor dict from the environment.
        :param action: Current action (may influence feature construction).
        :returns: Transformed sensor dict.
        :rtype: Dict
        :raises AttributeError: if a key listed in :meth:`filtered_sensor_space`
            is returned as a plain ``float`` or ``int`` rather than a
            ``np.ndarray``; the framework calls ``.flatten()`` on those values
            when building the observation vector
            (``"'float' object has no attribute 'flatten'"``).
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
        :returns: Boolean mask of length ``n_actions`` (``Discrete`` example).
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
        """Return a custom action space for this skill's policy.

        When provided, the policy trains against this space instead of the
        simulator's native action space. :meth:`transform_action` is then
        responsible for mapping policy output back to the sim's format.

        :returns: A space definition (e.g. ``Box``, ``Discrete``) for the
            custom action space, or ``None`` to use the simulator's action
            space (default).
        """
        return None  # replace with e.g. Box(low=-1, high=1, shape=(1,))

    # optional
    async def is_compute_done(self, transformed_sensors: Dict, action) -> bool:
        """Combined done signal for the training loop.

        Returns ``True`` when both :meth:`compute_success_criteria` **and**
        :meth:`compute_termination` return ``True``. Override only when you
        need custom gate logic beyond their conjunction.

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

        Called by the framework before training begins. Stores ``scenario``
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
