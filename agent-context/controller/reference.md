# AgentController Interface

`AgentController` is the deterministic/rule-based interface for an `Agent`.

Source: `amesa_core/amesa_core/orchestration/agent/agent_controller.py`. Import either
`from amesa_core import AgentController` (as the CLI scaffold does) or
`from amesa_core.orchestration.agent.agent_controller import AgentController`.

## Full scaffold

```python
from amesa_core import AgentController
from typing import Dict, List

class MyController(AgentController):
    # optional; must be callable with no arguments (the runtime calls MyController())
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)  # sets self.action_space / sensor_space / scenario = None

    # required
    async def compute_action(self, transformed_sensors: Dict, action):
        """Produce the simulator action from the sensors.

        :param transformed_sensors: AMESA sensor dict (sim sensors + perceptor outputs).
            The runtime does NOT run :meth:`transform_sensors` first, and the dict is
            not reduced to :meth:`filtered_sensor_space`.
        :param action: The controller's previous action; ``None`` on the first step of an episode.
        :returns: Action consumable by the sim action space (must not be ``None``).
        """
        error = float(transformed_sensors["value"]) - float(transformed_sensors["target"])
        control = -0.5 * error
        return [float(control)]

    # required
    async def filtered_sensor_space(self) -> List[str]:
        """Declare which sensor keys this controller reads.

        :returns: List of sensor names; each must exist on the sim (or a perceptor).
        """
        return ["value", "target"]

    # required
    async def compute_success_criteria(self, transformed_sensors: Dict, action) -> bool:
        """Define when the controlled behavior is successful. Must return a ``bool``."""
        error = float(transformed_sensors["value"]) - float(transformed_sensors["target"])
        return bool(abs(error) < 0.05)

    # required
    async def compute_termination(self, transformed_sensors: Dict, action) -> bool:
        """Define when the episode should terminate. Must return a ``bool``."""
        return bool(float(transformed_sensors["value"]) > 100.0)

    # optional — default returns ``sensors`` unchanged. Part of the interface, but
    # no controller execution path (training, inference, validation) calls it.
    async def transform_sensors(self, sensors):
        return sensors
```

## Lifecycle

- Instantiated with no arguments, and re-instantiated at every episode reset (instance state does not carry across episodes).
- Each step: `compute_action(sensors, previous_action)` is awaited with the raw AMESA sensors.
- All four abstract methods must be `async def`; the validator rejects non-async overrides.

## Helpers on the base class (not for overriding)

`get_action_space()` / `set_action_space(space)`, `get_sim_sensor_space()` / `set_sim_sensor_space(space)`, `add_scenario(scenario)` (sets `self.scenario`), `is_controller()` (returns `True`), `to_json()` / `from_json(data)` (cloudpickle class serialization).
