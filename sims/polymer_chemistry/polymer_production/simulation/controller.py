"""
Controller base class and action mapping loaded from config.
"""

from abc import ABC, abstractmethod
import array
import random
import simpy
from typing import Dict, Any, List
import numpy as np

from .config_loader import get_config
from .production_sim import ProductionSim
from .equipment import Equipment
from .task import Task
from .state import State
from .worker import Worker
from .recipe import Recipe


class Controller(ABC):
    yield_time = 1
    MAX_TIME = 480

    def __init__(self, env: simpy.Environment, debug: bool = False):
        config = get_config()
        self.MAX_TIME = config.episode_minutes
        
        self.RESET_TIME = 1
        self.env = env
        self.state = State(env, self.MAX_TIME)
        self.production_sim = ProductionSim()
        
        # Equipment store
        self.equipment_store = simpy.FilterStore(env, capacity=config.total_machines)
        self.equipment_store.items = list(self.state.equipment.values())
        
        # Worker store
        self.worker_store = simpy.FilterStore(env, capacity=config.num_workers)
        self.worker_store.items = list(self.state.workers.values())
        
        self.debug = debug
        
        # Build action mask mapping
        self._build_action_masks()

    def _build_action_masks(self):
        """Build action masks for each possible state (simplified)."""
        config = get_config()
        self.action_mask_template = {}
        
        # Base mask: all actions valid by default
        # Actual validation happens at runtime in step()
        self.masking = [1] * config.action_space_size

    @abstractmethod
    def step(self, action: int) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_mask(self) -> List[int]:
        pass

    @abstractmethod
    def get_state(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def reset(self, config_dict: Dict[str, Any]) -> Dict[str, Any]:
        pass

    def move_to_completed(self, product_id: str) -> None:
        """Move completed product to output."""
        config = get_config()
        product = config.get_product(product_id)
        if product:
            self.state.completed[product_id] += product.batch_yield

    def map_action_to_dict(self, action: int) -> Dict[str, Any]:
        """Map integer action to action dictionary."""
        config = get_config()
        return config.get_action(action)

    def get_action_mask(self) -> np.ndarray:
        """Get current valid action mask."""
        config = get_config()
        mask = np.zeros(config.action_space_size, dtype=np.bool_)
        
        # Action 0 (wait) is always valid
        mask[0] = True
        
        # Check each action
        for action_id in range(1, config.action_space_size):
            action = config.get_action(action_id)
            
            if action["type"] == "wait":
                mask[action_id] = True
                continue
            
            # Validate action
            recipe = self.state.recipes[action["product_id"]]
            stage_idx = action["stage_idx"]
            stage = config.stages[stage_idx]
            task_time = recipe.times.get(stage.name, 0)
            
            # Check worker
            worker = self.state.workers[action["worker_id"]]
            worker_ok = (
                worker.busy_for in (0, None) and
                self.env.now >= worker.shift_start and
                self.env.now + task_time <= worker.shift_end and
                worker.trained_on.get(action["machine_name"], False)
            )
            
            # Check equipment
            equipment = self.state.equipment[action["machine_name"]]
            equip_ok = equipment.is_idle()
            
            # Check dependency
            dep_ok = True
            if stage_idx > 0:
                prev_stage = config.stages[stage_idx - 1]
                dep_ok = False
                for machine_name in prev_stage.machine_names:
                    dep_eq = self.state.equipment[machine_name]
                    if dep_eq.current_recipe.product_id == action["product_id"] and dep_eq.time_remaining == 0:
                        dep_ok = True
                        break
            
            if worker_ok and equip_ok and dep_ok:
                mask[action_id] = True
        
        return mask


def make_controller(env: simpy.Environment, debug: bool = False) -> Controller:
    """Factory function to create controller."""
    from .production_controller import ProductionController
    return ProductionController(env, debug)