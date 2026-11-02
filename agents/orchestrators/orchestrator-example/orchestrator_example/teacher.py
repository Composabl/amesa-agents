from typing import Dict, List

import numpy as np
from amesa_core import AgentTeacher


def _scalar(value) -> float:
    """Sensor values arrive as one-element arrays; read them as a float."""
    return float(np.asarray(value, dtype=float).reshape(-1)[0])


class CounterOrchestratorTeacher(AgentTeacher):
    """
    Orchestrator teacher that chooses a child agent index based on demand and error.

    Expected child mapping:
        index 0 -> "stabilize"
        index 1 -> "recover"

    Sensors expected from the sim:
        demand (float): current operating demand (0..1)
        error  (float): absolute process error

    The action is the index of the child that acts. By default an orchestrator
    runs its children in fixed order (child 0 first, then stay or move to the
    next); deploy it with sequenceType "variable" to let it switch freely.
    """

    async def compute_reward(self, transformed_sensors: Dict, action, sim_reward: float) -> float:
        demand = _scalar(transformed_sensors["demand"])
        error = _scalar(transformed_sensors["error"])

        # Favor high demand with low error.
        reward = float(sim_reward) - error + (0.2 * demand)
        return float(reward)

    async def compute_success_criteria(self, transformed_sensors: Dict, action) -> bool:
        error = _scalar(transformed_sensors["error"])
        return bool(error < 0.05)

    async def compute_termination(self, transformed_sensors: Dict, action) -> bool:
        error = _scalar(transformed_sensors["error"])
        return bool(error > 5.0)

    async def transform_action(self, transformed_sensors: Dict, action):
        # Orchestrator actions must resolve to a valid child index. The sampled
        # action may be a plain int, a list or a one-element array.
        return int(np.asarray(action).reshape(-1)[0])

    async def filtered_sensor_space(self) -> List[str]:
        return ["demand", "error"]

    async def transform_sensors(self, sensors, action) -> Dict:
        return sensors

    async def compute_action_mask(self, transformed_sensors: Dict, action):
        demand = _scalar(transformed_sensors["demand"])

        # Two children: [stabilize, recover]
        # Under high demand, force stabilize; otherwise allow both.
        if demand > 0.8:
            return [1, 0]
        return [1, 1]
