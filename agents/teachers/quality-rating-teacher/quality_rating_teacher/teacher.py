from typing import Dict, List

from amesa_core.orchestration.agent.goals.maximize_goal import MaximizeGoal

QUALITY_RATING = "Quality_Rating"


class QualityRatingTeacher(MaximizeGoal):
    """
    Teacher agent that maximizes Quality_Rating.
    """

    def __init__(self):
        super().__init__(
            sensor=QUALITY_RATING,
            name="maximize quality rating",
        )

    async def filtered_sensor_space(self) -> List[str]:
        return [QUALITY_RATING]

    async def transform_sensors(self, sensors, action) -> Dict:
        return sensors

    async def transform_action(self, transformed_sensors: Dict, action):
        return action
