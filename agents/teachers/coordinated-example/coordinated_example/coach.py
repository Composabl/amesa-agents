from typing import Dict

from amesa_core.orchestration.agent.agent_coach import AgentCoach


class DriveCoach(AgentCoach):
    """
    Coordinates two sub-agents for autonomous driving:
        navigate — steers toward the goal position.
        avoid    — keeps clear of nearby obstacles.

    Each sub-agent is trained by its own teacher (NavigateTeacher, AvoidTeacher),
    which supplies that agent's individual reward. The coach adds ONE shared
    scalar on top: the coordinated-set processor calls

        coach_reward = await coach.compute_reward(multi_sensors, action, multi_reward)
        multi_reward[agent_name] += coach_reward   # for every child agent

    so compute_reward must return a float, not a dict
    (amesa_train/agent_processors/agent_coordinated_set_processor.py).

    Arguments the coach receives (all keyed by child agent name):
        compute_reward:            multi_sensors (each child's filtered sensors),
                                   action, multi_reward (each child's teacher reward)
        compute_success_criteria / compute_termination:
                                   the raw sim sensors per child, e.g.
                                   transformed_sensors["navigate"]["distance_to_goal"]

    Sensors expected from the sim (per child agent):
        distance_to_goal     (float): Remaining distance to the target (metres).
        obstacle_proximity   (float): Distance to the nearest obstacle (metres).

    Success: within 0.5 m of the goal AND no obstacle within 1.0 m.
    Termination: obstacle closer than 0.2 m (collision imminent).
    The episode ends when success OR termination is true (AgentCoach.is_compute_done).

    Usage:
        coordinated = AgentCoordinatedSet("drive", DriveCoach)
        coordinated.add_agent(Agent("navigate", NavigateTeacher, training_cycles=50))
        coordinated.add_agent(Agent("avoid",    AvoidTeacher,    training_cycles=50))
        orchestration.add_coordinated_agent(coordinated)
    """

    def __init__(self, *args, **kwargs):
        super().__init__()

    async def compute_reward(self, transformed_sensors: Dict, action, sim_reward) -> float:
        # sim_reward is a dict of the children's teacher rewards. Give a small
        # shared bonus when both children are doing well, so they cooperate.
        rewards = list(sim_reward.values()) if isinstance(sim_reward, dict) else [sim_reward]
        if rewards and all(float(r) > 0.0 for r in rewards):
            return 0.1
        return 0.0

    async def compute_success_criteria(self, transformed_sensors: Dict, action) -> bool:
        sensors = transformed_sensors["navigate"]
        distance = float(sensors["distance_to_goal"])
        proximity = float(sensors["obstacle_proximity"])
        return distance < 0.5 and proximity >= 1.0

    async def compute_termination(self, transformed_sensors: Dict, action) -> bool:
        return float(transformed_sensors["avoid"]["obstacle_proximity"]) < 0.2

    async def transform_action(self, transformed_sensors: Dict, action):
        return action
