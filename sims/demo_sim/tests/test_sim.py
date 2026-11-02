# Copyright (C) Amesa, Inc - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential

import pytest
import gymnasium as gym

from demo_sim.sim import Env


class TestEnv:
    """Test the Env class (gym.Env wrapper)"""

    def test_init_discrete(self):
        """Test initialization with discrete space type"""
        env = Env(env_init={"space_type": "discrete"})
        assert isinstance(env.observation_space, gym.spaces.Discrete)
        assert isinstance(env.action_space, gym.spaces.Discrete)

    def test_init_box(self):
        """Test initialization with box space type"""
        env = Env(env_init={"space_type": "box"})
        assert isinstance(env.observation_space, gym.spaces.Box)
        assert isinstance(env.action_space, gym.spaces.Box)

    def test_reset(self):
        """Test reset method"""
        env = Env(env_init={"space_type": "discrete"})
        obs, info = env.reset()
        assert obs is not None
        assert "action_mask" in info

    def test_step(self):
        """Test step method"""
        env = Env(env_init={"space_type": "discrete"})
        env.reset()
        obs, reward, done, truncated, info = env.step(0)
        assert obs is not None
        assert reward == 0  # Not done yet
        assert done is False
        assert "action_mask" in info

    def test_step_until_done(self):
        """Test stepping until done"""
        env = Env(env_init={"space_type": "discrete"})
        env.reset()
        done = False
        steps = 0
        while not done:
            obs, reward, done, truncated, info = env.step(0)
        assert done is True
        assert reward == 1