from typing import Dict, List

from amesa_core import AgentTeacher


class ReactorTemperatureTeacher(AgentTeacher):
    """
    Regulates a reactor's temperature toward a target setpoint.

    Sensors expected from the sim:
        temperature (float): Current reactor temperature in degrees Celsius.
        setpoint    (float): Desired target temperature in degrees Celsius.

    Action space: Box(low=-1.0, high=1.0, shape=(1,))
        action[0] > 0  → increase heating power
        action[0] < 0  → increase cooling power

    Success: temperature is within 1 °C of setpoint for a single step.
    Termination: temperature exceeds 200 °C (unsafe) or drops below -10 °C.
    """

    async def compute_reward(self, transformed_sensors: Dict, action, sim_reward: float) -> float:
        temperature = transformed_sensors["temperature"]
        setpoint = transformed_sensors["setpoint"]
        error = abs(float(temperature) - float(setpoint))

        # Shaped reward: 0 at setpoint, increasingly negative with distance.
        # Bonus of +1 when within the 1 °C success band.
        reward = -error / 10.0
        if error <= 1.0:
            reward += 1.0

        return float(reward)

    async def compute_success_criteria(self, transformed_sensors: Dict, action) -> bool:
        temperature = transformed_sensors["temperature"]
        setpoint = transformed_sensors["setpoint"]
        return bool(abs(float(temperature) - float(setpoint)) <= 1.0)

    async def compute_termination(self, transformed_sensors: Dict, action) -> bool:
        temperature = float(transformed_sensors["temperature"])
        return temperature > 200.0 or temperature < -10.0

    async def transform_action(self, transformed_sensors: Dict, action):
        # Action is already in [-1, 1]; pass through unchanged.
        return action

    async def filtered_sensor_space(self) -> List[str]:
        return ["temperature", "setpoint"]

    async def transform_sensors(self, sensors, action) -> Dict:
        return sensors
