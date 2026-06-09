from typing import Dict, List

from amesa_core import PerceptorImpl


class KinematicsPerceptor(PerceptorImpl):
    """
    Derives velocity and acceleration from consecutive position readings.

    Reads:
        position (float): Raw position from the sim (metres).
        dt       (float): Elapsed time since the last step (seconds).
                          If the sim does not provide dt, a fixed timestep
                          of 0.05 s is assumed.

    Produces:
        velocity     (float): First derivative of position (m/s).
        acceleration (float): Second derivative of position (m/s²).

    Both outputs are 0.0 on the first step of each episode because no
    prior position is available. State persists across steps within an
    episode but is NOT reset between episodes — reset it explicitly in
    compute() when you detect a new episode (e.g. step_count == 0).
    """

    DEFAULT_DT = 0.05  # seconds, used when the sim does not supply dt

    def __init__(self, *args, **kwargs):
        self.prev_position: float | None = None
        self.prev_velocity: float | None = None

    async def compute(self, obs_spec, obs) -> Dict:
        position = float(obs["position"])
        dt = float(obs.get("dt", self.DEFAULT_DT))

        # Reset state at the start of a new episode.
        if obs.get("step_count", 1) == 0:
            self.prev_position = None
            self.prev_velocity = None

        if self.prev_position is None:
            velocity = 0.0
            acceleration = 0.0
        else:
            velocity = (position - self.prev_position) / dt if dt > 0.0 else 0.0
            if self.prev_velocity is None:
                acceleration = 0.0
            else:
                acceleration = (velocity - self.prev_velocity) / dt if dt > 0.0 else 0.0

        self.prev_position = position
        self.prev_velocity = velocity

        return {
            "velocity": velocity,
            "acceleration": acceleration,
        }

    def filtered_sensor_space(self, obs) -> List[str]:
        return ["position", "dt"]
