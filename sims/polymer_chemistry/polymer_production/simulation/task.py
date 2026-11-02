"""
Task execution and validation loaded from config.
"""

import string
import simpy
from typing import Dict, Any
from .equipment import Equipment, EquipmentNames
from .recipe import Recipe
from .worker import Worker
from .state import State
from .config_loader import get_config


class Task:
    def __init__(
        self,
        task_type: string,
        worker_id: str,
        equipment_name: str,
        dependency_equipment: str = "",
    ):
        self.task_type = task_type
        self.worker_id = worker_id
        self.equipment_name = equipment_name
        self.dependency_equipment = dependency_equipment

    def equipment_task(self, task_data: Dict[str, Any]):
        """SimPy process for equipment operation."""
        config = get_config()
        recipe: Recipe = task_data["state"].recipes[task_data["product_id"]]
        stage_idx = task_data["stage_idx"]
        stage = config.stages[stage_idx]
        
        # Get time for this stage
        task_time = recipe.times.get(stage.name, 0)
        
        # Acquire equipment
        to_equipment: Equipment = yield task_data["equipment_store"].get(
            lambda x: x.name == self.equipment_name
        )
        
        # Release dependency equipment if applicable
        if self.dependency_equipment:
            from_equipment: Equipment = yield task_data["equipment_store"].get(
                lambda x: x.name == self.dependency_equipment
            )
            from_equipment.set_not_in_use()
            yield task_data["equipment_store"].put(from_equipment)
        
        # Start processing
        to_equipment.set_in_use(recipe, task_data["env"].now, task_time)
        
        # Wait for processing
        yield task_data["env"].timeout(task_time)
        
        # Release equipment
        yield task_data["equipment_store"].put(to_equipment)

    def worker_task(self, task_data: Dict[str, Any]) -> int:
        """SimPy process for worker operation."""
        config = get_config()
        recipe: Recipe = task_data["state"].recipes[task_data["product_id"]]
        stage_idx = task_data["stage_idx"]
        stage = config.stages[stage_idx]
        
        task_time = recipe.times.get(stage.name, 0)
        
        worker: Worker = yield task_data["worker_store"].get(
            lambda x: x.id == self.worker_id
        )
        
        worker.set_as_busy(task_time)
        yield task_data["env"].timeout(task_time)
        worker.set_as_not_busy()
        
        yield task_data["worker_store"].put(worker)
        return task_time

    def validate_task(self, task_data: Dict[str, Any]) -> bool:
        """Validate if task can be executed."""
        config = get_config()
        recipe: Recipe = task_data["state"].recipes[task_data["product_id"]]
        
        if task_data["product_id"] == "none":
            return False
        
        if task_data["worker_id"] == "none" and task_data["equipment_name"] == "none":
            return True
        
        stage_idx = task_data["stage_idx"]
        stage = config.stages[stage_idx]
        task_time = recipe.times.get(stage.name, 0)
        
        # Check worker availability
        available_workers = [
            x for x in task_data["worker_store"].items 
            if x.id == task_data["worker_id"] 
            and (x.busy_for in (0, None))
            and x.can_complete_task(task_data["equipment_name"], recipe, task_time)
        ]
        
        # Check equipment availability
        available_equipment = [
            x for x in task_data["equipment_store"].items 
            if x.name == task_data["equipment_name"] 
            and x.is_idle()
        ]
        
        # Check dependency (for stages 1 and 2)
        if stage_idx > 0:
            prev_stage = config.stages[stage_idx - 1]
            dependency_met = False
            for machine_name in prev_stage.machine_names:
                dep_eq = next((x for x in task_data["equipment_store"].items if x.name == machine_name), None)
                if dep_eq and dep_eq.current_recipe.product_id == recipe.product_id and dep_eq.time_remaining == 0:
                    dependency_met = True
                    break
            if not dependency_met:
                return False
        
        return len(available_workers) > 0 and len(available_equipment) > 0


def make_task_from_action(action_dict: Dict, state: State, env: simpy.Environment) -> Task:
    """Create Task from action dictionary."""
    config = get_config()
    if action_dict["type"] == "wait":
        return Task("wait", "none", "none")
    
    # Find dependency equipment (output from previous stage): a previous-stage
    # machine holding this product that has finished, the same rule validate_task
    # and the action mask use. equipment_task releases it when the batch moves on;
    # without it, upstream machines were never freed and the line deadlocked.
    dependency = ""
    if action_dict["stage_idx"] > 0:
        prev_stage = config.stages[action_dict["stage_idx"] - 1]
        for machine_name in prev_stage.machine_names:
            dep_eq = state.equipment[machine_name]
            if dep_eq.current_recipe.product_id == action_dict["product_id"] and dep_eq.time_remaining == 0:
                dependency = machine_name
                break
    
    return Task(
        task_type=action_dict["type"],
        worker_id=action_dict["worker_id"],
        equipment_name=action_dict["machine_name"],
        dependency_equipment=dependency,
    )