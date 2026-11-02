# Copyright (C) Amesa, Inc - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential

"""
Thin wrapper around ProductionEnv for backward compatibility.
"""

from typing import Optional
import gymnasium as gym
from .production_env import ProductionEnv


class Env(ProductionEnv):
    """
    Production scheduling simulation environment.
    Wrapper for backward compatibility.
    """
    pass