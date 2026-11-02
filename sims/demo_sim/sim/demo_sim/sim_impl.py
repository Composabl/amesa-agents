# Copyright (C) Amesa, Inc - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential

import random
import time
from typing import Any, Dict, List, SupportsFloat, Tuple, Union

import gymnasium as gym
import numpy as np
from gymnasium import Space

import amesa_core.utils.logger as logger_util
from amesa_core.networking.sim.server_amesa import ServerAmesa
from amesa_core.orchestration.scenario.scenario import Scenario
from amesa_core.utils import space_util

logger = logger_util.get_logger(__name__)

MAX_COUNTER = 10  # max 8 bit value due to MultiBinary space


def _coerce_action_to_space(space: gym.Space, action: Any) -> Any:
    """
    Normalize actions from RPC / policies so leaf dtypes and shapes match the
    space (e.g. float64 Box samples → float32 where the space requires it).
    """
    if isinstance(space, gym.spaces.Tuple):
        return tuple(
            _coerce_action_to_space(s, a) for s, a in zip(space.spaces, action)
        )
    if isinstance(space, gym.spaces.Dict):
        return {
            k: _coerce_action_to_space(space.spaces[k], action[k]) for k in space.spaces
        }
    if isinstance(space, gym.spaces.Box):
        return np.asarray(action, dtype=space.dtype).reshape(space.shape)
    if isinstance(space, gym.spaces.Discrete):
        return int(np.asarray(action).item())
    if isinstance(space, gym.spaces.MultiDiscrete):
        return np.asarray(action, dtype=np.int64).reshape(space.shape)
    if isinstance(space, gym.spaces.MultiBinary):
        return np.asarray(action, dtype=np.int8).reshape(space.shape)
    if isinstance(space, gym.spaces.Text):
        return str(action)
    return action


class SimImpl(ServerAmesa):
    """
    The simulation environment is designed to test and demonstrate how different sensor and
    action space configurations can be implemented and interacted with in RL.

    The goal of the simulation environment is to count to MAX_COUNTER as quickly as possible
    """

    def __init__(self, env_init: dict = {}):
        self.space_type = env_init.get("space_type", "discrete")
        self.sleep_timer = env_init.get("sleep_timer", None)
        self.counter = 0  # Initialize counter
        self.steps = 0  # keeps track of episode length
        self.scenario = None
        # Define sensor and action spaces
        if self.space_type == "discrete":
            self.sensor_space = gym.spaces.Discrete(
                MAX_COUNTER + 1
            )  # 0-MAX_COUNTER (just return the counter)
            self.action_space = gym.spaces.Discrete(2)  # Increment by 1, or reset to 0
        elif self.space_type == "multidiscrete":
            self.sensor_space = gym.spaces.MultiDiscrete([MAX_COUNTER + 1])
            self.action_space = gym.spaces.MultiDiscrete([2, 3])
        elif self.space_type == "multibinary":
            self.sensor_space = gym.spaces.MultiBinary(
                7
            )  # Binary representation of MAX_COUNTER
            self.action_space = gym.spaces.MultiDiscrete([2, 3])  # Increment or reset
        elif self.space_type == "box":
            self.sensor_space = gym.spaces.Box(
                low=np.array([0]), high=np.array([MAX_COUNTER]), dtype=np.float32
            )
            self.action_space = gym.spaces.Box(
                low=np.array([0]), high=np.array([1]), dtype=np.float32
            )  # Increment by 1 or reset
        elif self.space_type == "dictionary":
            self.sensor_space = gym.spaces.Dict(
                {
                    "counter": gym.spaces.Box(
                        low=np.array([0]),
                        high=np.array([MAX_COUNTER]),
                        dtype=np.float32,
                    )
                }
            )
            self.action_space = gym.spaces.Dict(
                {
                    "increment": gym.spaces.Discrete(
                        2
                    ),  # Increment by 1, or reset to 0
                    "increment_box": gym.spaces.Box(
                        low=np.array([-2]), high=np.array([-1]), dtype=np.float32
                    ),  # Increment by 1 or reset
                    "nested_action": gym.spaces.Dict(
                        {
                            "increment_nested": gym.spaces.Discrete(2),
                            "increment_nested_box": gym.spaces.Box(
                                low=-2, high=5, shape=(1,), dtype=np.float32
                            ),
                        }
                    ),
                }
            )
        elif self.space_type == "tuple":
            self.sensor_space = gym.spaces.Tuple(
                [
                    gym.spaces.Discrete(10),
                    gym.spaces.Box(low=0, high=1, shape=(1,), dtype=np.float32),
                    gym.spaces.Tuple(
                        [
                            gym.spaces.Discrete(2),
                            gym.spaces.Box(low=0, high=1, shape=(1,), dtype=np.float32),
                        ]
                    ),
                ]
            )
            self.action_space = gym.spaces.Tuple(
                [
                    gym.spaces.Discrete(2),
                    gym.spaces.Box(low=0, high=1, shape=(1,), dtype=np.float32),
                    gym.spaces.Tuple(
                        [
                            gym.spaces.Discrete(2),
                            gym.spaces.Box(low=0, high=1, shape=(1,), dtype=np.float32),
                        ]
                    ),
                ]
            )
        elif self.space_type == "text":
            self.sensor_space = gym.spaces.Dict(
                {
                    "text": gym.spaces.Text(max_length=16),
                    "counter": gym.spaces.Box(
                        low=np.array([0]),
                        high=np.array([MAX_COUNTER]),
                        dtype=np.float32,
                    ),
                }
            )
            self.action_space = gym.spaces.Discrete(2)  # Increment by 1, or reset to 0
        else:
            raise ValueError(f"Unknown space type {self.space_type}")

        # Print Debug
        logger.debug(
            f"Initialized Sim (action space: {self.action_space}, obs space: {self.sensor_space})"
        )

    async def make(self, env_id: str, env_init: dict) -> dict:
        """Make the environment."""
        # Re-initialize with the new env_init
        self.__init__(env_init)
        return {"id": env_id, "max_episode_steps": MAX_COUNTER}

    @property
    def sensor_space(self):
        return self._sensor_space

    @property
    def action_space(self):
        return self._action_space

    @sensor_space.setter
    def sensor_space(self, value):
        self._sensor_space = value

    @action_space.setter
    def action_space(self, value):
        self._action_space = value

    async def sensor_space_info(self) -> 'Space':
        return self.sensor_space

    async def action_space_info(self) -> 'Space':
        return self.action_space

    async def action_space_sample(self) -> Union[Any, List[Any]]:
        return self.action_space.sample()

    async def reset(self) -> Tuple[Any, Dict[str, Any]]:
        self.counter = 0
        self.steps = 0
        obs = self._get_sensor()
        info = await self.get_action_mask()
        return obs, {"action_mask": await self.get_action_mask()}

    async def step(
        self, action
    ) -> Tuple[Any, SupportsFloat, bool, bool, Dict[str, Any]]:
        # Process action
        self.steps += 1
        self._process_action(action)

        # Generate sensor based on space type
        sensors = self._get_sensor()

        # Check if goal is reached
        done = self.steps == MAX_COUNTER
        reward = 1 if done else 0  # Reward when goal is reached
        info = await self.get_action_mask()

        # intentionally slow down the simulation to ensure the SDK can handle it
        if self.sleep_timer:
            time.sleep(self.sleep_timer)

        return sensors, reward, done, False, {"action_mask": await self.get_action_mask()}

    async def get_action_mask(self):
        if self.space_type == "discrete":
            mask = random.choice([np.array([0, 1]), np.array([1, 0])])
        elif self.space_type == "multidiscrete" or self.space_type == "multibinary":
            mask1 = random.choice([np.array([0, 1]), np.array([1, 0])])
            mask2 = random.choice([np.array([0, 1, 1]), np.array([1, 1, 0])])
            mask = tuple([mask1, mask2])
        elif self.space_type == "box":
            mask = [1, 1]  # can't mask box
        elif self.space_type == "dictionary":
            mask = {
                "increment": random.choice([np.array([0, 1]), np.array([1, 0])]),
                "increment_box": np.array([1, 1]),
                "nested_action": {
                    "increment_nested": random.choice(
                        [np.array([0, 1]), np.array([1, 0])]
                    ),
                    "increment_nested_box": np.array([1, 1]),
                },
            }
        elif self.space_type == "tuple":
            mask = (
                random.choice([np.array([0, 1]), np.array([1, 0])]),
                np.array([1, 1]),
                (random.choice([np.array([0, 1]), np.array([1, 0])]), np.array([1, 1])),
            )
        elif self.space_type == "text":
            mask = random.choice([np.array([0, 1]), np.array([1, 0])])
        return {"action_mask": mask}

    def _process_action(self, action):
        action = _coerce_action_to_space(self.action_space, action)
        assert self.action_space.contains(
            action
        ), f"Invalid action {action} not in {self.action_space}. Example: {self.action_space.sample()}"

        # 0 = increment, 1 = decrement
        value_to_add = 0

        if (
            self.space_type == "discrete"
            or self.space_type == "multibinary"
            or self.space_type == "text"
        ):
            value_to_add = 1 if action == 0 else -1
        elif self.space_type == "multidiscrete" or self.space_type == "multibinary":
            value_to_add = 1 if action[0] == 0 else -1
        elif self.space_type == "box":
            value_to_add = 1 if action[0] <= 0.5 else -1
        elif self.space_type == "dictionary":
            value_to_add = 1 if action["increment"] == 0 else -1
        elif self.space_type == "tuple":
            value_to_add = 1 if action[0] == 0 else -1
        else:
            raise ValueError(f"Unknown space type {self.space_type}")

        # Update the counter but ensure it stays within the bounds
        self.counter = max(0, min(MAX_COUNTER, self.counter + value_to_add))

    def _get_sensor(self):
        return self.sensor_space.sample()

    async def render(self, mode="human"):
        print(f"Counter: {self.counter}")

    async def close(self) -> None:
        pass

    async def set_scenario(self, scenario) -> None:
        self.scenario = scenario

    async def get_scenario(self):
        return self.scenario

    async def get_render(self):
        return f"Counter: {self.counter}"

    async def get_mappings(self):
        action_space = await self.action_space_info()
        sensor_space = await self.sensor_space_info()

        variables_action_space = space_util.convert_space_to_json(action_space)
        variables_sensor_space = space_util.convert_space_to_json(sensor_space)

        return {
            "action_space": {
                "space": action_space,
                "mappings": variables_action_space,
            },
            "sensor_space": {
                "space": sensor_space,
                "mappings": variables_sensor_space,
            },
        }