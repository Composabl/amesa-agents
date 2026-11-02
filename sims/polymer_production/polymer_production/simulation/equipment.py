"""
Equipment definitions loaded from config.
"""

import simpy
from enum import Enum
from typing import Dict, Optional
from .config_loader import get_config
from .recipe import Recipe


class Equipment:
    def __init__(self, name: str, environment: simpy.Environment):
        self.name = name
        self.current_recipe: Recipe = Recipe("none", 0, [0])
        self._start_time: Optional[int] = None
        self._environment = environment
        self.time_remaining: int = 0

    def set_remaining_time(self) -> int:
        if self._start_time is not None:
            finish_time = self._finish_time()
            set_time_remaining = finish_time - self._environment.now
            if set_time_remaining > 0:
                return set_time_remaining
            else:
                return 0
        else:
            return 0

    def _finish_time(self) -> int:
        if self.current_recipe.product_id == "none":
            return 0
        
        # Determine stage from machine name
        config = get_config()
        stage = config.get_stage_for_machine(self.name)
        if stage is None:
            return 0
        
        return self._start_time + self.current_recipe.times.get(stage.name, 0)

    def set_in_use(self, recipe: Recipe, start_time: int, task_time: int) -> None:
        self.current_recipe = recipe
        self._start_time = start_time
        self.time_remaining = task_time

    def set_not_in_use(self) -> None:
        self.current_recipe = Recipe("none", 0, [0])
        self._start_time = None
        self.time_remaining = 0

    def is_idle(self) -> bool:
        return self.current_recipe.product_id == "none" or self.current_recipe.product_id is None

    def print_equipment(self) -> None:
        if self.is_idle():
            print(f"{self.name}: -")
        elif self.time_remaining == 0:
            print(f"{self.name}: {self.current_recipe.product_id} ready!")
        else:
            print(f"{self.name}: {self.current_recipe.product_id} in {self.time_remaining} mins left")


# Dynamic EquipmentNames enum
def get_equipment_names_enum() -> Enum:
    config = get_config()
    members = {"none": 0}
    idx = 1
    for stage in config.stages:
        for m_name in stage.machine_names:
            members[m_name.upper()] = idx
            idx += 1
    return Enum("EquipmentNames", members)


EquipmentNames = get_equipment_names_enum()