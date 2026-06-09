from typing import Dict, List

from amesa_core.agent.skill.goals.approach_goal import ApproachGoal
from amesa_core.agent.skill.goals.avoid_goal import AvoidGoal
from amesa_core.agent.skill.goals.coordinated_goal import CoordinatedGoal, GoalCoordinationStrategy


class LandingGoal(CoordinatedGoal):
    """
    Soft-landing goal: guide a lander to altitude 0.0 while keeping
    descent velocity above the crash threshold.

    Combines two goals with AND strategy:
        approach_altitude — drives altitude to 0.0 m (the landing pad).
        avoid_crash       — terminates the episode if descent speed exceeds
                            5.0 m/s (hard landing / crash).

    Sensors expected from the sim:
        altitude          (float): Current altitude in metres. Target is 0.0.
        descent_velocity  (float): Downward speed in m/s (positive = descending).
                                   Must stay below 5.0 m/s for a safe landing.

    Success: altitude within 0.5 m of 0.0 (ApproachGoal boundary satisfied).
    Termination: descent_velocity >= 5.0 m/s (AvoidGoal boundary breached
                 with should_terminate_in_boundary=True).

    Scale weights: approach_altitude gets 2× weight — reaching the pad is
    the primary objective; avoiding a crash is a hard constraint via termination.

    Usage:
        skill = Skill("landing", LandingGoal, training_cycles=150)
    """

    def __init__(self):
        approach_altitude = ApproachGoal(
            sensor="altitude",
            name="reach landing pad",
            target=0.0,
            tolerance=0.5,
            boundary_left=-0.5,
            boundary_right=0.5,
            scale=2.0,
        )

        avoid_crash = AvoidGoal(
            sensor="descent_velocity",
            name="avoid hard landing",
            target=0.0,
            boundary_left=0.0,
            boundary_right=5.0,
            scale=1.0,
            should_terminate_in_boundary=False,   # reward penalty, not hard stop
        )

        super().__init__(
            goals=[approach_altitude, avoid_crash],
            goals_coordination_strategy=GoalCoordinationStrategy.AND,
            weights=[2.0, 1.0],
        )

    async def filtered_sensor_space(self) -> List[str]:
        return ["altitude", "descent_velocity"]

    async def transform_sensors(self, sensors, action) -> Dict:
        return sensors

    async def transform_action(self, transformed_sensors: Dict, action):
        return action
