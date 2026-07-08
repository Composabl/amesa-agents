from typing import Dict

from amesa_core.orchestration.agent.agent_coach import AgentCoach


class DriveCoach(AgentCoach):
    """
    Coordinates two sub-agents for autonomous driving:
        navigate — steers toward the goal position.
        avoid    — keeps clear of nearby obstacles.

    The coach distributes independent rewards to each sub-agent so their
    policies can specialise without interfering with each other's gradient.

    Sensors expected from the sim:
        distance_to_goal     (float): Remaining distance to the target (metres).
                                      Lower is better.
        obstacle_proximity   (float): Distance to the nearest obstacle (metres).
                                      Higher is safer.

    Child agent names (must match keys in compute_reward):
        "navigate"
        "avoid"

    Success: within 0.5 m of the goal AND no obstacle within 1.0 m.
    Termination: obstacle closer than 0.2 m (collision imminent).

    Usage:
        coordinated = AgentCoordinatedSet("drive", DriveCoach)
        coordinated.add_agent(Agent("navigate", NavigateTeacher, training_cycles=50))
        coordinated.add_agent(Agent("avoid",    AvoidTeacher,    training_cycles=50))
        orchestration.add_coordinated_agent(coordinated)
    """

    async def compute_reward(self, transformed_sensors: Dict, action, sim_reward) -> Dict[str, float]:
        distance = float(transformed_sensors["distance_to_goal"])
        proximity = float(transformed_sensors["obstacle_proximity"])

        # Navigate sub-agent: reward decreases linearly with remaining distance.
        navigate_reward = float(max(0.0, 1.0 - distance / 10.0))

        # Avoid sub-agent: reward increases with clearance from obstacles.
        # Penalise sharply when inside the 1 m safety margin.
        if proximity < 1.0:
            avoid_reward = float(proximity - 1.0)   # negative in the danger zone
        else:
            avoid_reward = float(min(1.0, (proximity - 1.0) / 4.0))

        return {
            "navigate": navigate_reward,
            "avoid": avoid_reward,
        }

    async def compute_success_criteria(self, transformed_sensors: Dict, action) -> bool:
        distance = float(transformed_sensors["distance_to_goal"])
        proximity = float(transformed_sensors["obstacle_proximity"])
        return distance < 0.5 and proximity >= 1.0

    async def compute_termination(self, transformed_sensors: Dict, action) -> bool:
        return float(transformed_sensors["obstacle_proximity"]) < 0.2

    async def transform_sensors(self, sensors, action) -> Dict:
        return sensors

    async def transform_action(self, transformed_sensors: Dict, action):
        return action
