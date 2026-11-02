"""
Full simulation state loaded from config.
"""

import array
import simpy
from typing import Dict, Any, List
from .config_loader import get_config
from .worker import Worker
from .recipe import Recipe, make_recipe_dict
from .equipment import Equipment


class State:
    def __init__(self, environment: simpy.Environment, sim_time: int):
        config = get_config()
        
        # Recipes
        self.recipes = make_recipe_dict()
        
        # Workers
        self.workers: Dict[str, Worker] = {}
        for w_config in config.workers:
            self.workers[w_config.id] = Worker(environment, sim_time, w_config)
        
        # Equipment
        self.equipment: Dict[str, Equipment] = {}
        for stage in config.stages:
            for machine_name in stage.machine_names:
                self.equipment[machine_name] = Equipment(machine_name, environment)
        
        # Completed products
        self.completed: Dict[str, int] = {p.id: 0 for p in config.products}
        
        # Market conditions (can be overridden by scenario)
        self.prices: Dict[str, float] = {p.id: p.price for p in config.products}
        self.demands: Dict[str, int] = {p.id: p.base_demand for p in config.products}
        self.costs: Dict[str, float] = {p.id: p.cost for p in config.products}
        
        # Real demand with noise
        self.real_demands: Dict[str, float] = {}
        self._generate_real_demands()
        
        self._env = environment
        self._sim_time = sim_time
        self.profit = 0

    def _generate_real_demands(self):
        import random
        config = get_config()
        for p in config.products:
            noise = random.uniform(-config.demand_noise, config.demand_noise)
            self.real_demands[p.id] = max(0, p.base_demand * (1 + noise))

    def set_state(self, config_dict: Dict[str, Any]) -> None:
        """Set state from scenario config dict."""
        if config_dict == {'nothing': None} or config_dict == {}:
            return
        
        self._sim_time = config_dict.get('sim_time', self._sim_time)
        
        # Workers
        for w in get_config().workers:
            key = f"{w.id}_time_remaining"
            if key in config_dict:
                self.workers[w.id].busy_for = config_dict[key]
        
        # Equipment
        for stage in get_config().stages:
            for machine_name in stage.machine_names:
                recipe_key = f"{machine_name}_recipe"
                time_key = f"{machine_name}_time_remaining"
                if recipe_key in config_dict and time_key in config_dict:
                    recipe_id = config_dict[recipe_key]
                    remaining = config_dict[time_key]
                    self.set_equipment(machine_name, recipe_id, remaining)
        
        # Completed products
        for p in get_config().products:
            key = f"completed_{p.id}"
            if key in config_dict:
                self.completed[p.id] = config_dict[key]
        
        # Market conditions
        for p in get_config().products:
            if f"{p.id}_price" in config_dict:
                self.prices[p.id] = config_dict[f"{p.id}_price"]
            if f"{p.id}_demand" in config_dict:
                self.demands[p.id] = config_dict[f"{p.id}_demand"]
            if f"{p.id}_cost" in config_dict:
                self.costs[p.id] = config_dict[f"{p.id}_cost"]

    def set_equipment(self, machine_name: str, recipe_id: str, remaining_time: int):
        """Set equipment state from scenario."""
        equipment = self.equipment[machine_name]
        recipe = self.recipes.get(recipe_id, self.recipes["none"])
        stage = get_config().get_stage_for_machine(machine_name)
        if stage:
            total_time = recipe.times.get(stage.name, 0)
            start_time = self._env.now - (total_time - remaining_time)
            equipment.set_in_use(recipe, start_time, remaining_time)

    def get_state(self) -> Dict[str, Any]:
        """Serialize state for observation/action masking."""
        state = {}
        
        # Worker busy times
        for w_config in get_config().workers:
            state[f"{w_config.id}_time_remaining"] = self.workers[w_config.id].remaining_time()
        
        # Equipment state
        for stage in get_config().stages:
            for machine_name in stage.machine_names:
                eq = self.equipment[machine_name]
                state[f"{machine_name}_recipe"] = eq.current_recipe.product_id
                state[f"{machine_name}_time_remaining"] = eq.time_remaining
        
        # Completed products
        for p in get_config().products:
            state[f"completed_{p.id}"] = self.completed[p.id]
        
        # Market
        for p in get_config().products:
            state[f"{p.id}_price"] = self.prices[p.id]
            state[f"{p.id}_demand"] = self.demands[p.id]
            state[f"{p.id}_cost"] = self.costs[p.id]
        
        return state

    def print_equipment(self) -> None:
        print('\nEQUIPMENT')
        for stage in get_config().stages:
            for machine_name in stage.machine_names:
                self.equipment[machine_name].print_equipment()

    def print_workers(self) -> None:
        print('\nWORKERS')
        for w in self.workers.values():
            w.print_worker()

    def print_completed(self) -> None:
        print('\nCOMPLETED')
        for p in get_config().products:
            print(f"{p.id}: {self.completed[p.id]}")