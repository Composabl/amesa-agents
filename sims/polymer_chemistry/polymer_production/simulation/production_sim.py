"""
Low-level SimPy process definitions for production simulation.
"""

from typing import Dict, Any
import simpy
from .task import Task
from .state import State
from .config_loader import get_config


class ProductionSim:
    def __init__(self):
        self.yield_time = 1
        config = get_config()
        self._setup_stores()

    def _setup_stores(self):
        """Stores are set up by controller, not here."""
        pass

    def reset(self, config_dict: Dict[str, Any], state: State) -> Dict[str, Any]:
        state.set_state(config_dict)
        return state.get_state()

    def execute_stage_task(self, task_data: Dict[str, Any], task: Task):
        """Execute a stage task (prep/process/finish)."""
        yield_time = self.yield_time
        valid_task = False
        
        stage_idx = task_data["stage_idx"]
        stage = get_config().stages[stage_idx]
        
        if task.equipment_name != "none":
            if len(task_data["equipment_store"].items) > 0 and len(task_data["worker_store"].items) > 0 and not valid_task:
                while not valid_task:
                    if task.validate_task(task_data):
                        if task.worker_id == "none" and task.equipment_name == "none":
                            valid_task = True
                            return True
                        else:
                            valid_task = True
                            task_data["env"].process(task.equipment_task(task_data))
                            task_data["env"].process(task.worker_task(task_data))
                    else:
                        break
        
        yield task_data["env"].timeout(yield_time)
        return True


# For backward compatibility
BakerySim = ProductionSim