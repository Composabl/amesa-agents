from typing import Dict, List

from amesa_core import AgentTeacher


class CounterOrchestratorTeacher(AgentTeacher):
    """
    Orchestrator teacher that chooses a child agent index based on demand and error.

    Expected child mapping:
        index 0 -> "stabilize"
        index 1 -> "recover"

    Sensors expected from the sim:
        demand (float): current operating demand (0..1)
        error  (float): absolute process error
    """

    async def compute_reward(self, transformed_sensors: Dict, action, sim_reward: float) -> float:
        demand = float(transformed_sensors["demand"])
        error = float(transformed_sensors["error"])

        # Favor high demand with low error.
        reward = float(sim_reward) - error + (0.2 * demand)
        return float(reward)

    async def compute_success_criteria(self, transformed_sensors: Dict, action) -> bool:
        error = float(transformed_sensors["error"])
        return bool(error < 0.05)

    async def compute_termination(self, transformed_sensors: Dict, action) -> bool:
        error = float(transformed_sensors["error"])
        return bool(error > 5.0)

    async def transform_action(self, transformed_sensors: Dict, action):
        # Orchestrator actions must resolve to a valid child index.
        if isinstance(action, (list, tuple)):
            action = action[0]
        return int(action)

    async def filtered_sensor_space(self) -> List[str]:
        return ["demand", "error"]

    async def transform_sensors(self, sensors, action) -> Dict:
        return sensors

    async def compute_action_mask(self, transformed_sensors: Dict, action):
        demand = float(transformed_sensors["demand"])

        # Two children: [stabilize, recover]
        # Under high demand, force stabilize; otherwise allow both.
        if demand > 0.8:
            return [1, 0]
        return [1, 1]
