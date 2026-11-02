"""
Production controller with action validation and execution.
"""

import array
import numpy as np
import simpy
from typing import Dict, Any, List
from .controller import Controller
from .config_loader import get_config
from .state import State
from .task import Task, make_task_from_action
from .recipe import Recipe


class ProductionController(Controller):
    def __init__(self, env: simpy.Environment, debug: bool = False):
        super().__init__(env, debug)
        config = get_config()
        self.step_action_dict = self._build_action_dict()
        self.default_state = self._build_default_state()

    def _build_action_dict(self) -> Dict[int, str]:
        """Build human-readable action names."""
        config = get_config()
        action_dict = {0: "wait"}
        
        for action_id in range(1, config.action_space_size):
            action = config.get_action(action_id)
            if action["type"] == "wait":
                action_dict[action_id] = "wait"
            else:
                name = f"{action['worker_id']}_{action['type']}_{action['product_id']}_on_{action['machine_name']}"
                action_dict[action_id] = name
        
        return action_dict

    def _build_default_state(self) -> Dict[str, Any]:
        """Build default state for reset."""
        config = get_config()
        default = {
            'sim_time': config.episode_minutes,
        }
        
        # Worker busy times
        for w in config.workers:
            default[f"{w.id}_time_remaining"] = 0
        
        # Equipment state
        for stage in config.stages:
            for machine_name in stage.machine_names:
                default[f"{machine_name}_recipe"] = "none"
                default[f"{machine_name}_time_remaining"] = 0
        
        # Completed products
        for p in config.products:
            default[f"completed_{p.id}"] = 0
        
        return default

    def get_state(self) -> Dict[str, Any]:
        return self.state.get_state()

    def get_mask(self) -> array.array:
        mask = self.get_action_mask()
        return array.array('b', mask.astype(int))

    def reset(self, config_dict: Dict[str, Any]) -> Dict[str, Any]:
        reset_state = self.production_sim.reset(config_dict, self.state)
        
        # Reinitialize stores
        self.equipment_store = simpy.FilterStore(self.env, capacity=get_config().total_machines)
        self.equipment_store.items = list(self.state.equipment.values())
        
        self.worker_store = simpy.FilterStore(self.env, capacity=get_config().num_workers)
        self.worker_store.items = list(self.state.workers.values())
        
        # Regenerate real demands
        self.state._generate_real_demands()
        self.state.profit = 0
        
        # Run reset time
        self.env.run(until=self.RESET_TIME + self.env.now)
        
        return reset_state

    def step(self, action: int) -> Dict[str, Any]:
        config = get_config()
        action_dict = config.get_action(action)
        action_string = self.map_action_to_dict(action)
        
        done = False
        
        # Advance time by yield_time
        self.env.run(until=self.yield_time + self.env.now)
        
        # Update equipment time remaining
        for stage in config.stages:
            for machine_name in stage.machine_names:
                eq = self.state.equipment[machine_name]
                eq.time_remaining = eq.set_remaining_time()

        # Count batches that finished while time advanced (including during waits)
        self._check_completions()

        if action_string["type"] == "wait":
            if self.debug:
                print(f"Wait. Time: {self.env.now}")
            return self.get_state()
        
        # Create and validate task
        task_data = {
            "env": self.env,
            "state": self.state,
            "equipment_store": self.equipment_store,
            "worker_store": self.worker_store,
            "product_id": action_dict["product_id"],
            "stage_idx": action_dict["stage_idx"],
            "worker_id": action_dict["worker_id"],
            "equipment_name": action_dict["machine_name"],
            "machine_name": action_dict["machine_name"],
        }
        
        task = make_task_from_action(action_dict, self.state, self.env)
        
        if not task.validate_task(task_data):
            if self.debug:
                print(f"Invalid action: {action_string}")
            return self.get_state()
        
        # Execute task
        self.env.process(task.equipment_task(task_data))
        self.env.process(task.worker_task(task_data))
        
        # Wait for yield_time
        self.env.run(until=self.yield_time + self.env.now)
        
        # Update equipment time remaining
        for stage in config.stages:
            for machine_name in stage.machine_names:
                eq = self.state.equipment[machine_name]
                eq.time_remaining = eq.set_remaining_time()
        
        # Check for completed products (finish stage outputs)
        self._check_completions()
        
        if self.debug:
            self._debug_print(action_string)
        
        return self.get_state()

    def _check_completions(self):
        """Check for completed products at finish stage."""
        config = get_config()
        finish_stage = config.stages[-1]  # Last stage
        
        for machine_name in finish_stage.machine_names:
            eq = self.state.equipment[machine_name]
            if eq.current_recipe.product_id != "none" and eq.time_remaining == 0:
                # Product completed: count it and free the finish station
                product_id = eq.current_recipe.product_id
                self.move_to_completed(product_id)
                eq.set_not_in_use()
                if self.debug:
                    print(f"Completed: {product_id} on {machine_name}")

    def _debug_print(self, action_string: Dict):
        print(f"\nAction: {action_string}")
        print(f"Time: {self.env.now}")
        print(f"Profit: {self.state.profit}")
        self.state.print_equipment()
        self.state.print_workers()
        self.state.print_completed()


# Backward compatibility
RLLibController = ProductionController