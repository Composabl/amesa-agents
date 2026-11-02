# Copyright (C) Amesa, Inc - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential

import pytest
import numpy as np
import gymnasium as gym

from demo_sim.sim_impl import SimImpl


class TestSimImpl:
    """Test the SimImpl class"""

    def test_init_discrete(self):
        """Test initialization with discrete space type"""
        sim = SimImpl({"space_type": "discrete"})
        assert sim.space_type == "discrete"
        assert isinstance(sim.sensor_space, gym.spaces.Discrete)
        assert isinstance(sim.action_space, gym.spaces.Discrete)
        assert sim.counter == 0
        assert sim.steps == 0

    def test_init_box(self):
        """Test initialization with box space type"""
        sim = SimImpl({"space_type": "box"})
        assert sim.space_type == "box"
        assert isinstance(sim.sensor_space, gym.spaces.Box)
        assert isinstance(sim.action_space, gym.spaces.Box)

    def test_init_multidiscrete(self):
        """Test initialization with multidiscrete space type"""
        sim = SimImpl({"space_type": "multidiscrete"})
        assert sim.space_type == "multidiscrete"
        assert isinstance(sim.sensor_space, gym.spaces.MultiDiscrete)
        assert isinstance(sim.action_space, gym.spaces.MultiDiscrete)

    def test_init_multibinary(self):
        """Test initialization with multibinary space type"""
        sim = SimImpl({"space_type": "multibinary"})
        assert sim.space_type == "multibinary"
        assert isinstance(sim.sensor_space, gym.spaces.MultiBinary)
        assert isinstance(sim.action_space, gym.spaces.MultiDiscrete)

    def test_init_dictionary(self):
        """Test initialization with dictionary space type"""
        sim = SimImpl({"space_type": "dictionary"})
        assert sim.space_type == "dictionary"
        assert isinstance(sim.sensor_space, gym.spaces.Dict)
        assert isinstance(sim.action_space, gym.spaces.Dict)

    def test_init_tuple(self):
        """Test initialization with tuple space type"""
        sim = SimImpl({"space_type": "tuple"})
        assert sim.space_type == "tuple"
        assert isinstance(sim.sensor_space, gym.spaces.Tuple)
        assert isinstance(sim.action_space, gym.spaces.Tuple)

    def test_init_text(self):
        """Test initialization with text space type"""
        sim = SimImpl({"space_type": "text"})
        assert sim.space_type == "text"
        assert isinstance(sim.sensor_space, gym.spaces.Dict)
        assert isinstance(sim.action_space, gym.spaces.Discrete)

    def test_invalid_space_type(self):
        """Test that invalid space type raises ValueError"""
        with pytest.raises(ValueError, match="Unknown space type"):
            SimImpl({"space_type": "invalid_type"})

    def test_reset(self):
        """Test reset method"""
        sim = SimImpl({"space_type": "discrete"})
        sim.counter = 5
        sim.steps = 3
        obs, info = sim.reset()
        assert sim.counter == 0
        assert sim.steps == 0
        assert obs is not None
        assert "action_mask" in info

    def test_step(self):
        """Test step method"""
        sim = SimImpl({"space_type": "discrete"})
        obs, reward, done, truncated, info = sim.step(0)  # increment
        assert sim.steps == 1
        assert sim.counter == 1
        assert reward == 0  # Not done yet
        assert done is False

    def test_step_until_done(self):
        """Test stepping until done"""
        sim = SimImpl({"space_type": "discrete"})
        done = False
        while not done:
            obs, reward, done, truncated, info = sim.step(0)  # always increment
        assert sim.steps == 10  # MAX_COUNTER
        assert done is True
        assert reward == 1

    def test_get_action_mask(self):
        """Test action mask generation"""
        sim = SimImpl({"space_type": "discrete"})
        mask = sim.get_action_mask()
        assert "action_mask" in mask
        # Check that the action mask is one of the expected arrays
        mask_array = mask["action_mask"]
        expected_masks = [np.array([0, 1]), np.array([1, 0])]
        assert any(np.array_equal(mask_array, expected) for expected in expected_masks)

    def test_compute_reward(self):
        """Test that reward is 1 when done, 0 otherwise"""
        sim = SimImpl({"space_type": "discrete"})
        
        # Not done
        obs, reward, done, truncated, info = sim.step(0)
        assert reward == 0
        assert done is False
        
        # Step until done
        while not done:
            obs, reward, done, truncated, info = sim.step(0)
        assert reward == 1
        assert done is True