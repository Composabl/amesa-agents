# Copyright (C) Amesa, Inc - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential

import random
import time
from typing import Optional, Dict, Any

import gymnasium as gym
import numpy as np
from gymnasium.spaces import Dict as GymDict, Box, Discrete

from amesa_core.orchestration.scenario.scenario import Scenario

from .sim_impl import SimImpl


class Env(gym.Env):
    """
    Demo simulation environment for testing different space types.
    Uses SimImpl for the actual simulation logic.
    """

    def __init__(self, *args, **kwargs):
        # Extract env_init from kwargs
        env_init = kwargs.get("env_init", {})
        
        config = {
            "env_config": {
                "debug": False,
                "render_mode": "human"
            }
        }
        self.config = config
        self.sim = SimImpl(env_init)

        # Use the sensor and action spaces from SimImpl
        self.observation_space = self.sim.sensor_space
        self.action_space = self.sim.action_space

        self.counter = 0
        self.scenario: Scenario = None

    def reset(
        self,
        *,
        seed: Optional[int] = None,
        options: Optional[dict] = None,
    ):
        # Define scenario in the simulation
        if isinstance(self.scenario, (Scenario, dict)):
            if type(self.scenario) == dict:
                sample = self.scenario
            else:
                sample = self.scenario.sample()

            for key in list(sample.keys()):
                setattr(self.sim, key, sample[key])

        self.sim = SimImpl()
        self.sim.space_type = self.sim.space_type  # Keep the space type

        self.counter = 0
        self.sim.counter = 0
        self.sim.steps = 0

        obs, info = self.sim.reset()
        return obs, info

    def step(self, action):
        # Process action
        self.sim.steps += 1
        self.sim._process_action(action)

        # Generate sensor based on space type
        sensors = self.sim._get_sensor()

        # Check if goal is reached
        done = self.sim.steps == 10
        reward = 1 if done else 0  # Reward when goal is reached
        info = self.get_action_mask()

        return sensors, reward, done, False, info

    def get_action_mask(self):
        return self.sim.get_action_mask()

    def set_scenario(self, scenario):
        self.scenario = scenario

    def render(self, mode='human', close=False):
        print(f"Counter: {getattr(self.sim, 'counter', 'N/A')}")

    def close(self):
        pass