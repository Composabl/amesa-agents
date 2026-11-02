"""
Recipe definitions loaded from config.
"""

from enum import Enum
from typing import Dict, List
from .config_loader import get_config, ProductConfig


class Recipe:
    def __init__(self, product_id: str, batch_yield: int, stage_times: List[int]):
        self.product_id = product_id
        self.batch_yield = batch_yield
        self.times = {}  # stage_name -> time
        config = get_config()
        for idx, stage in enumerate(config.stages):
            self.times[stage.name] = stage_times[idx] if idx < len(stage_times) else 0


def make_recipe_dict() -> Dict[str, Recipe]:
    """Create recipe dict from config."""
    config = get_config()
    recipes = {"none": Recipe("none", 0, [0]*config.num_stages)}
    for p in config.products:
        recipes[p.id] = Recipe(p.id, p.batch_yield, p.stage_times)
    return recipes


# Dynamic ProductNames enum
def get_product_names_enum() -> Enum:
    config = get_config()
    members = {"none": 0}
    for i, p in enumerate(config.products, 1):
        members[p.id.upper()] = i
    return Enum("ProductNames", members)


# For backward compatibility
ProductNames = get_product_names_enum()
RecipeNames = ProductNames  # Alias