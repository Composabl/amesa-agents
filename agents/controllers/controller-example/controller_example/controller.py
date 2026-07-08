from typing import Dict, List

from amesa_core import OrchestrationController


class PDController(OrchestrationController):
    """
    Proportional-derivative controller for a 1-D position servo.

    Drives the controlled element toward position 0.0 using a PD law:
        force = -(Kp * position + Kd * velocity)

    Sensors expected from the sim:
        position (float): Current position (metres). Target is 0.0.
        velocity (float): Current velocity (m/s).

    Action space: Box(low=-10.0, high=10.0, shape=(1,))
        action[0]: Force command applied to the servo (Newtons).

    Success: |position| < 0.05 m (within 5 cm of origin).
    Termination: |position| > 10.0 m (out of range).
    """

    # PD gains — tune these for your plant's dynamics.
    KP = 2.0
    KD = 0.8

    async def compute_action(self, transformed_sensors: Dict, action) -> List[float]:
        position = float(transformed_sensors["position"])
        velocity = float(transformed_sensors["velocity"])
        force = -(self.KP * position + self.KD * velocity)
        # Clamp to action space bounds.
        force = max(-10.0, min(10.0, force))
        return [force]

    async def compute_success_criteria(self, transformed_sensors: Dict, action) -> bool:
        return bool(abs(float(transformed_sensors["position"])) < 0.05)

    async def compute_termination(self, transformed_sensors: Dict, action) -> bool:
        return bool(abs(float(transformed_sensors["position"])) > 10.0)

    async def filtered_sensor_space(self) -> List[str]:
        return ["position", "velocity"]

    async def transform_sensors(self, sensors) -> Dict:
        return sensors
