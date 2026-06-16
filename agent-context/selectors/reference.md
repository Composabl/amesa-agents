# Selector Interface

A selector implementation is either a `SkillTeacher` subclass (learned selector) or a `SkillController` subclass (rule-based selector).

## Full scaffold (teacher selector)

```python
import numpy as np
from amesa_core.agent.skill.skill_teacher import SkillTeacher
from typing import Dict, List

class MySelectorTeacher(SkillTeacher):
    # required
    async def compute_reward(self, transformed_sensors: Dict, action, sim_reward: float) -> float:
        """Reward for selector-policy training.

        :param transformed_sensors: Post-:meth:`transform_sensors` sensor dict.
        :type transformed_sensors: Dict
        :param action: Policy output (child index or probability distribution).
        :param sim_reward: Simulator reward for the current step.
        :type sim_reward: float
        :returns: Scalar reward for selector policy optimization.
        :rtype: float
        :raises NotImplementedError: if not overridden in the subclass.
        """
        return float(sim_reward)

    # required
    async def compute_success_criteria(self, transformed_sensors: Dict, action) -> bool:
        """Success condition for the selector episode.

        :param transformed_sensors: Post-:meth:`transform_sensors` sensor dict.
        :type transformed_sensors: Dict
        :param action: Policy output shaped to the action space.
        :returns: ``True`` when the selector episode succeeds.
        :rtype: bool
        :raises NotImplementedError: if not overridden in the subclass.
        """
        return False

    # required
    async def transform_action(self, transformed_sensors: Dict, action):
        """Convert policy output into the selected child index.

        :param transformed_sensors: Post-:meth:`transform_sensors` sensor dict.
        :type transformed_sensors: Dict
        :param action: Raw policy output.
        :returns: Integer child index into ``config.children``.
        :rtype: int
        :raises NotImplementedError: if not overridden in the subclass.
        """
        return int(action)

    # required
    async def filtered_sensor_space(self) -> List[str]:
        """Selector sensor dependencies.

        :returns: List of sensor key strings.
        :rtype: List[str]
        :raises NotImplementedError: if not overridden in the subclass.
        """
        return ["counter"]

    # optional
    async def transform_sensors(self, sensors, action) -> Dict:
        """Preprocess sensors before selector logic.

        Wraps ``counter`` in a ``np.ndarray`` and derives a normalised value
        so the policy receives a consistent input range.

        :param sensors: Raw sensor dict from the environment.
        :param action: Current action.
        :returns: Transformed sensor dict.
        :rtype: Dict
        :raises AttributeError: if a key listed in :meth:`filtered_sensor_space`
            is returned as a plain ``float`` or ``int`` rather than a
            ``np.ndarray``; the framework calls ``.flatten()`` on those values
            when building the observation vector
            (``"'float' object has no attribute 'flatten'"``).
        """
        counter = float(sensors.get("counter", 0.0))
        return {
            **sensors,
            "counter": np.array([counter], dtype=np.float32),
            "counter_norm": np.array([counter / 10.0], dtype=np.float32),
        }

    # optional
    async def compute_termination(self, transformed_sensors: Dict, action) -> bool:
        """Terminate the selector episode when counter goes out of valid range.

        :param transformed_sensors: Post-:meth:`transform_sensors` sensor dict.
        :type transformed_sensors: Dict
        :param action: Policy output shaped to the action space.
        :returns: ``True`` when the episode should terminate.
        :rtype: bool
        """
        return float(transformed_sensors["counter"][0]) < -10.0

    # optional
    async def compute_action_mask(self, transformed_sensors: Dict, action) -> List[bool]:
        """Mask child-index actions; length must equal number of children.

        Disables child 1 (e.g. an aggressive sub-skill) when the counter is
        already negative, keeping only the conservative child available.

        :param transformed_sensors: Post-:meth:`transform_sensors` sensor dict.
        :type transformed_sensors: Dict
        :param action: Current action.
        :returns: Boolean mask of length ``n_children``.
        :rtype: List[bool]
        :raises ValueError: if the returned list length differs from the number
            of children (``Discrete(n_children)``).
        """
        counter = float(transformed_sensors["counter"][0])
        # Discrete(2): [conservative child, aggressive child]
        return [True, counter >= 0.0]
```

## Full scaffold (controller selector)

```python
from amesa_core.agent.skill.skill_controller import SkillController
from typing import Dict, List

class MySelectorController(SkillController):
    # required
    async def compute_action(self, transformed_sensors: Dict, action):
        """Choose the child index directly.

        Routes to child 1 while the counter is positive; falls back to
        child 0 (the conservative sub-skill) once it goes non-positive.

        :param transformed_sensors: Post-:meth:`transform_sensors` sensor dict.
        :type transformed_sensors: Dict
        :param action: Previous action.
        :returns: List containing the selected child index.
        :rtype: list[int]
        :raises NotImplementedError: if not overridden in the subclass.
        """
        counter = float(transformed_sensors.get("counter_norm", 0.0))
        return [1] if counter > 0.0 else [0]

    # required
    async def filtered_sensor_space(self) -> List[str]:
        """Selector sensor dependencies.

        :returns: List of sensor key strings.
        :rtype: List[str]
        :raises NotImplementedError: if not overridden in the subclass.
        """
        return ["counter"]

    # required
    async def compute_success_criteria(self, transformed_sensors: Dict, action) -> bool:
        """Success condition for the selector run.

        :param transformed_sensors: Post-:meth:`transform_sensors` sensor dict.
        :type transformed_sensors: Dict
        :param action: Current action.
        :returns: ``True`` when the selector run succeeds.
        :rtype: bool
        :raises NotImplementedError: if not overridden in the subclass.
        """
        return False

    # required
    async def compute_termination(self, transformed_sensors: Dict, action) -> bool:
        """Termination condition for the selector run.

        :param transformed_sensors: Post-:meth:`transform_sensors` sensor dict.
        :type transformed_sensors: Dict
        :param action: Current action.
        :returns: ``True`` when the selector run should terminate.
        :rtype: bool
        :raises NotImplementedError: if not overridden in the subclass.
        """
        return False

    # optional
    async def transform_sensors(self, sensors) -> Dict:
        """Preprocess sensors before :meth:`compute_action`.

        Normalises ``counter`` so routing thresholds are expressed in
        ``[-1, 1]`` space rather than raw simulator units.

        :param sensors: Raw sensor dict from the environment.
        :returns: Transformed sensor dict with an added ``counter_norm`` key.
        :rtype: Dict
        """
        counter = float(sensors.get("counter", 0.0))
        return {**sensors, "counter_norm": counter / 10.0}
```

## Selector runtime contract

- Selector action space is always `Discrete(number_of_children)`.
- The selected index points into `config.children` order.
- Runtime returns the selected **child skill action** to the environment, not the selector index.
