# AgentController Interface

`AgentController` is the deterministic/rule-based interface for an `Agent`.

## Full scaffold

```python
from amesa_core.orchestration.agent.agent_controller import AgentController
from typing import Dict

class MyController(AgentController):
    # required
    async def compute_action(self, transformed_sensors: Dict, action):
        """Produce the simulator action from transformed sensors.

        :param transformed_sensors: Post-:meth:`transform_sensors` sensor dict.
        :type transformed_sensors: Dict
        :param action: Previous action (useful for stateful controllers).
        :returns: Action consumable by the sim action space.
        :raises NotImplementedError: if not overridden in the subclass.
        """
        error = float(transformed_sensors.get("error", 0.0))
        control = -0.5 * error
        return [float(control)]

    # required
    async def filtered_sensor_space(self):
        """Declare which sensor keys this controller reads.

        :returns: List of sensor key strings.
        :rtype: list[str]
        :raises NotImplementedError: if not overridden in the subclass.
        """
        return ["value", "target", "error"]

    # required
    async def compute_success_criteria(self, transformed_sensors: Dict, action) -> bool:
        """Define when the controlled behavior is successful.

        :param transformed_sensors: Post-:meth:`transform_sensors` sensor dict.
        :type transformed_sensors: Dict
        :param action: Current action taken by the orchestration.
        :returns: ``True`` when the success condition is met.
        :rtype: bool
        :raises NotImplementedError: if not overridden in the subclass.
        """
        return abs(float(transformed_sensors.get("error", 1.0))) < 0.05

    # required
    async def compute_termination(self, transformed_sensors: Dict, action) -> bool:
        """Define when the episode should terminate.

        :param transformed_sensors: Post-:meth:`transform_sensors` sensor dict.
        :type transformed_sensors: Dict
        :param action: Current action taken by the orchestration.
        :returns: ``True`` when the episode should end.
        :rtype: bool
        :raises NotImplementedError: if not overridden in the subclass.
        """
        return float(transformed_sensors.get("value", 0.0)) > 100.0

    # optional
    async def transform_sensors(self, sensors) -> Dict:
        """Derive controller-specific features from raw sensors.

        Computes ``error`` as the signed difference between ``value`` and
        ``target`` so downstream control logic only needs to read a single key.

        :param sensors: Raw sensor dict from the environment.
        :returns: Transformed sensor dict with an added ``error`` key.
        :rtype: Dict
        """
        value = float(sensors.get("value", 0.0))
        target = float(sensors.get("target", 0.0))
        return {**sensors, "error": value - target}
```

