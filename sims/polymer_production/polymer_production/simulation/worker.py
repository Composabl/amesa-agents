"""
Worker definitions loaded from config.
"""

import simpy
from enum import Enum
from typing import Dict, List
from .config_loader import get_config, WorkerConfig
from .equipment import EquipmentNames


class Worker:
    def __init__(self, env: simpy.Environment, sim_time: int, config: WorkerConfig):
        self.config = config
        self.id = config.id
        self.name = config.id
        
        # Skills: map equipment names to bool
        self.trained_on: Dict[str, bool] = {}
        for stage in get_config().stages:
            for machine_name in stage.machine_names:
                self.trained_on[machine_name] = stage.name in config.skills

        self._environment = env
        self._sim_time = sim_time
        self.shift_start = config.shift_start
        self.shift_end = config.shift_end
        self.busy_for: int = 0
        self._start_time: int = None

    def remaining_time(self) -> int:
        if self._start_time is not None:
            set_time_remaining = (self._start_time + self.busy_for) - self._environment.now
            if set_time_remaining > 0:
                return set_time_remaining
            else:
                return 0
        else:
            return 0

    def set_as_busy(self, task_time: int) -> None:
        self._start_time = self._environment.now
        self.busy_for = task_time

    def set_as_not_busy(self) -> None:
        self._start_time = None
        self.busy_for = 0

    def can_complete_task(self, equipment_name: str, recipe, task_time: int) -> bool:
        """Check if worker can complete task given equipment, recipe, and time."""
        if self._environment.now < self.shift_start:
            return False
        if self._environment.now + task_time > self.shift_end:
            return False
        if self.busy_for not in (0, None):
            return False
        if not self.trained_on.get(equipment_name, False):
            return False
        return True

    def is_available(self) -> bool:
        return (self.busy_for in (0, None) and 
                self._environment.now >= self.shift_start and 
                self._environment.now < self.shift_end)

    def print_worker(self) -> None:
        skills = [m for m, v in self.trained_on.items() if v]
        print(f"{self.name}: skills={skills}")
        if self._environment.now < self.shift_start:
            print(f"  - arriving in {self.shift_start - self._environment.now} mins")
        elif self.busy_for not in (0, None):
            print(f"  - busy for {self.remaining_time()} mins")
        else:
            print("  - ready!")
        if self.shift_end < self._sim_time and self.shift_end > self._environment.now:
            print(f"  - leaving in {self.shift_end - self._environment.now} mins")


# Dynamic WorkerNames enum
def get_worker_names_enum() -> Enum:
    config = get_config()
    members = {}
    for i, w in enumerate(config.workers, 1):
        members[w.id.upper()] = i
    return Enum("WorkerNames", members)


WorkerNames = get_worker_names_enum()
BakerNames = WorkerNames  # Backward compatibility alias