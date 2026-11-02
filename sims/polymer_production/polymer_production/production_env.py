"""
Generic Production Scheduling Environment.
Pure gymnasium.Env implementation - no RLlib dependencies.
Uses FLAT Dict observation space with meaningful keys and full Box shapes.
Uses Discrete action space with action_names metadata for platform.
"""

import random
from typing import Optional, Dict, Any, List

import gymnasium as gym
import numpy as np
from gymnasium.spaces import Box, Discrete, Dict as GymDict

from .simulation.config_loader import get_config, load_config, reset_config
from .simulation.state import State
from .simulation.production_controller import ProductionController
from .simulation.recipe import Recipe
from .simulation.equipment import Equipment
from .simulation.worker import Worker


class ProductionEnv(gym.Env):
    """
    Generic production scheduling simulation environment.
    Configurable via production_config.yaml
    Uses FLAT Dict observation space with meaningful keys and full Box shapes.
    Uses Discrete action space with action_names metadata for platform.
    """
    
    def __init__(self, env_config: Optional[Dict] = None):
        config = get_config()
        
        # Default env config
        default_config = {
            "env_config": {
                "debug": False,
                "reward_fn": None,
            }
        }
        
        if env_config:
            default_config.update(env_config)
        self.config = default_config
        
        # Debug flag
        debug = self.config["env_config"].get("debug", False)
        
        # Reward function
        self.reward_fn = self.config["env_config"].get("reward_fn", self.default_reward_fn)
        
        # Initialize controller (contains SimPy env, state, etc.)
        self.controller = ProductionController(None, debug)  # Will be replaced in reset
        
        # Action space: single Discrete (platform expects this)
        self.action_space = Discrete(config.action_space_size)
        
        # Store action names for platform metadata
        self.action_names = self._build_action_names(config)
        
        # Observation space: FLAT Dict with meaningful keys and full Box shapes
        self.observation_space = self._build_observation_space(config)
        
        # State placeholders
        self.obs = None
        self.scenario = None
        self.cnt = 0
        
        # Market conditions (set from scenario or defaults)
        self.prices = {}
        self.demands = {}
        self.costs = {}
        self.real_demands = {}
        self.profit = 0

    def _build_action_names(self, config) -> List[str]:
        """Build human-readable action names."""
        names = ["wait"]
        for action_id in range(1, config.action_space_size):
            action = config.get_action(action_id)
            if action["type"] == "wait":
                names.append("wait")
            else:
                name = f"{action['worker_id']}_{action['type']}_{action['product_id']}_on_{action['machine_name']}"
                names.append(name)
        return names

    def _build_observation_space(self, config) -> GymDict:
        """Build FLAT Dict observation space with meaningful keys and full Box shapes."""
        spaces = {}
        
        # Workers - each as separate element in array
        worker_names = [f"{w.id}_time_remaining" for w in config.workers]
        spaces["worker_times"] = Box(low=0, high=config.episode_minutes, shape=(config.num_workers,), dtype=np.float32)
        
        # Equipment: recipe_id, time_remaining per machine
        equip_names = []
        for stage in config.stages:
            for machine_name in stage.machine_names:
                equip_names.append(f"{machine_name}_recipe")
                equip_names.append(f"{machine_name}_time_remaining")
        spaces["equipment"] = Box(low=0, high=max(config.num_products, config.episode_minutes), shape=(len(equip_names),), dtype=np.float32)
        
        # Completed products
        product_names = [f"completed_{p.id}" for p in config.products]
        spaces["completed_products"] = Box(low=0, high=np.inf, shape=(config.num_products,), dtype=np.float32)
        
        # Market: price, demand, cost per product
        market_names = []
        for p in config.products:
            market_names.append(f"{p.id}_price")
            market_names.append(f"{p.id}_demand")
            market_names.append(f"{p.id}_cost")
        spaces["market"] = Box(low=0, high=np.inf, shape=(len(market_names),), dtype=np.float32)
        
        # Action mask
        spaces["action_mask"] = Box(low=0, high=1, shape=(config.action_space_size,), dtype=np.bool_)
        
        return GymDict(spaces)

    def default_reward_fn(self, step_state: Dict, prices: Dict, costs: Dict) -> float:
        """Default reward: profit from completed products."""
        config = get_config()
        reward = 0
        
        for p in config.products:
            completed = step_state.get(f"completed_{p.id}", 0)
            if completed > 0:
                revenue = completed * (prices.get(p.id, p.price) - costs.get(p.id, p.cost))
                reward += revenue
        
        return reward

    def reset(
        self,
        *,
        seed: Optional[int] = None,
        options: Optional[Dict] = None,
    ):
        super().reset(seed=seed)
        
        config = get_config()
        self.cnt = 0
        
        # Create new SimPy environment
        import simpy
        env = simpy.Environment()
        
        # Create controller with new env
        debug = self.config["env_config"].get("debug", False)
        self.controller = ProductionController(env, debug)
        
        # Handle scenario
        scenario_config = {}
        if options and "scenario" in options:
            scenario_config = options["scenario"]
        elif isinstance(self.scenario, dict):
            scenario_config = self.scenario
        elif self.scenario is not None:
            # AMESA Scenario object
            if hasattr(self.scenario, 'sample'):
                scenario_config = self.scenario.sample()
            else:
                scenario_config = self.scenario
        
        # Platform scenarios use the mapped sensor names (equipment_6, ...);
        # translate them to the raw state keys State.set_state reads.
        scenario_config = self._translate_scenario(scenario_config)

        # Reset controller
        obs_dict = self.controller.reset(scenario_config)
        
        # Extract market conditions from state
        self.prices = self.controller.state.prices.copy()
        self.demands = self.controller.state.demands.copy()
        self.costs = self.controller.state.costs.copy()
        self.real_demands = self.controller.state.real_demands.copy()
        self.profit = 0
        
        # Process observation into FLAT Dict with arrays
        self.obs = self.process_state_dict(obs_dict)
        
        return self.obs, {}

    def process_state_dict(self, state_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Convert state dict to FLAT Dict observation with arrays."""
        config = get_config()
        obs = {}
        
        # Workers - array
        worker_times = []
        for w in config.workers:
            worker_times.append(state_dict.get(f"{w.id}_time_remaining", 0))
        obs["worker_times"] = np.array(worker_times, dtype=np.float32)
        
        # Equipment - flat array
        equipment = []
        for stage in config.stages:
            for machine_name in stage.machine_names:
                recipe_id = state_dict.get(f"{machine_name}_recipe", "none")
                recipe_encoded = 0.0
                if recipe_id != "none":
                    try:
                        for i, p in enumerate(config.products):
                            if p.id == recipe_id:
                                recipe_encoded = float(i + 1)
                                break
                    except:
                        recipe_encoded = float(hash(recipe_id) % 100)
                equipment.append(recipe_encoded)
                equipment.append(state_dict.get(f"{machine_name}_time_remaining", 0))
        obs["equipment"] = np.array(equipment, dtype=np.float32)
        
        # Completed products - array
        completed = []
        for p in config.products:
            completed.append(state_dict.get(f"completed_{p.id}", 0))
        obs["completed_products"] = np.array(completed, dtype=np.float32)
        
        # Market - flat array
        market = []
        for p in config.products:
            market.append(state_dict.get(f"{p.id}_price", p.price))
            market.append(state_dict.get(f"{p.id}_demand", p.base_demand))
            market.append(state_dict.get(f"{p.id}_cost", p.cost))
        obs["market"] = np.array(market, dtype=np.float32)
        
        # Action mask
        obs["action_mask"] = np.array(self.controller.get_mask(), dtype=np.bool_)
        
        return obs

    @staticmethod
    def _scenario_number(value) -> Optional[float]:
        """A scenario value as a float; a two-element list is a range, so take its low end."""
        if isinstance(value, (list, tuple)):
            if not value:
                return None
            value = value[0]
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def _translate_scenario(self, scenario_config: Dict[str, Any]) -> Dict[str, Any]:
        """Turn mapped scenario keys into the raw keys State.set_state reads.

        Mapped keys (the sensor names the platform's scenario conditions use):
          equipment_{2k}       recipe on machine k, in stage order (0 = empty,
                               i = product i-1; rounded, since range
                               conditions are sampled as floats)
          equipment_{2k+1}     minutes left on machine k (default 0 = done,
                               clamped to the recipe's time at that stage)
          completed_products_i completed units of product i
          market_{3i}/{3i+1}/{3i+2}  price / demand / cost of product i
        Raw keys already present win. worker_times_* is not supported:
        State.set_state marks a worker busy without a start time, so the
        worker would never free up.
        """
        if not isinstance(scenario_config, dict) or not scenario_config:
            return scenario_config
        config = get_config()
        out = dict(scenario_config)

        machines = [m for stage in config.stages for m in stage.machine_names]
        for k, machine_name in enumerate(machines):
            recipe_key, time_key = f"equipment_{2 * k}", f"equipment_{2 * k + 1}"
            if recipe_key not in scenario_config:
                continue
            raw_recipe = f"{machine_name}_recipe"
            if raw_recipe in scenario_config:
                continue
            recipe_val = self._scenario_number(scenario_config[recipe_key])
            if recipe_val is None:
                continue
            idx = int(round(recipe_val))
            if idx <= 0 or idx > config.num_products:
                continue
            product = config.products[idx - 1]
            stage = config.get_stage_for_machine(machine_name)
            stage_time = product.stage_times[config.stages.index(stage)] if stage else 0
            remaining = self._scenario_number(scenario_config.get(time_key, 0)) or 0.0
            remaining = int(round(min(max(remaining, 0.0), float(stage_time))))
            out[raw_recipe] = product.id
            out[f"{machine_name}_time_remaining"] = remaining

        for i, p in enumerate(config.products):
            key = f"completed_products_{i}"
            if key in scenario_config and f"completed_{p.id}" not in scenario_config:
                val = self._scenario_number(scenario_config[key])
                if val is not None:
                    out[f"completed_{p.id}"] = max(0.0, val)
            for offset, field in enumerate(("price", "demand", "cost")):
                key = f"market_{3 * i + offset}"
                if key in scenario_config and f"{p.id}_{field}" not in scenario_config:
                    val = self._scenario_number(scenario_config[key])
                    if val is not None:
                        out[f"{p.id}_{field}"] = max(0.0, val)
        return out

    def set_scenario(self, scenario):
        self.scenario = scenario

    def get_real_demands(self):
        return list(self.real_demands.values())

    def step(self, action: int):
        config = get_config()
        
        # Handle integer action (Discrete space)
        action_idx = action if isinstance(action, (int, np.integer)) else 0
        
        # Execute action in controller
        obs_dict = self.controller.step(action_idx)
        
        # Process observation
        self.obs = self.process_state_dict(obs_dict)
        
        # Calculate profit/reward
        self.profit = 0
        for p in config.products:
            completed = obs_dict.get(f"completed_{p.id}", 0)
            if completed > 0:
                price = self.prices.get(p.id, p.price)
                cost = self.costs.get(p.id, p.cost)
                real_demand = self.real_demands.get(p.id, p.base_demand)
                
                if completed <= real_demand:
                    # Revenue minus opportunity cost
                    revenue = completed * (price - cost)
                    opportunity = (real_demand - completed) * (price - cost)
                    self.profit += revenue - opportunity
                else:
                    # Revenue minus waste
                    revenue = real_demand * (price - cost)
                    waste = (completed - real_demand) * cost
                    self.profit += revenue - waste
        
        reward = self.profit
        
        # Termination
        terminated = self.controller.env.now >= config.episode_minutes
        
        info = {
            "profit": self.profit,
            "completed": {p.id: obs_dict.get(f"completed_{p.id}", 0) for p in config.products},
            "real_demands": self.real_demands,
        }
        
        return self.obs, reward, terminated, False, info

    @property
    def env(self):
        return self.controller.env

    def render(self, mode='human', close=False):
        if mode == 'human':
            self.controller._debug_print({"type": "step"})


# Backward compatibility
Env = ProductionEnv