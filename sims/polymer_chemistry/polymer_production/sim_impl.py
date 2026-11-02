# Copyright (C) Amesa, Inc - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential

import re
from typing import Any, Dict, List, SupportsFloat, Tuple

import amesa_core.utils.logger as logger_util
import amesa_core.utils.space_util as amesa_space_utils
import gymnasium as gym
from amesa_core.orchestration.scenario.scenario import Scenario
from amesa_core.networking.sim.server_amesa import ServerAmesa

from .sim import Env

logger = logger_util.get_logger(__name__)

_VALID_MAPPED_NAME = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")


def _flatten_mapping_name(name: str) -> str:
    """Turn a bracket accessor into a clean identifier.

    ['action_mask'][14] -> action_mask_14
    """
    flat = name.replace("'", "").replace("[", "_").replace("]", "")
    return re.sub(r"_+", "_", re.sub(r"[^A-Za-z0-9_]+", "_", flat)).strip("_")


def _name_mappings(mappings: List[Dict[str, Any]], default_mapped: str) -> None:
    """Fill `name` / `name_mapped` on every mapping and fail fast on bad names.

    - `name` is the bracket accessor the training runtime eval()s; it is kept
      verbatim. A top-level non-composite space (the Discrete(64) action) comes
      back with an empty name, so it gets `[0]`, the SDK's default accessor.
    - `name_mapped` is what the UI, scenario conditions and the historian use:
      [A-Za-z][A-Za-z0-9_]*, unique.
    """
    for v in mappings:
        # Space sizes can be numpy ints (e.g. Discrete.n); send plain ints.
        v["shape"] = [int(s) for s in v.get("shape", [])]
        if not v.get("name"):
            v["name"] = "[0]"
            mapped = default_mapped if len(mappings) == 1 else f"{default_mapped}_0"
        else:
            mapped = _flatten_mapping_name(v["name"])
            if not mapped or not mapped[0].isalpha():
                mapped = f"{default_mapped}_{mapped}" if mapped else default_mapped
        v["name_mapped"] = mapped

    names = [v["name_mapped"] for v in mappings]
    bad = [n for n in names if not _VALID_MAPPED_NAME.match(n)]
    dupes = sorted({n for n in names if names.count(n) > 1})
    if bad or dupes:
        raise ValueError(f"Invalid {default_mapped} mapping names: bad={bad[:10]} duplicates={dupes[:10]}")


class SimImpl(ServerAmesa):
    def __init__(self):
        self.env = Env()
        self.env_id = None
        self.env_init = None

    async def make(self, env_id: str, env_init: dict):
        self.env_id = env_id if env_id else self.env_id
        self.env_init = env_init if env_init else self.env_init

        print("Creating Production Scheduling Env with env_init: ", self.env_init)
        self.env = Env()

        return {"id": "polymer-production", "max_episode_steps": 480}

    async def sensor_space_info(self) -> gym.Space:
        return self.env.observation_space

    async def action_space_info(self) -> gym.Space:
        return self.env.action_space

    async def action_space_sample(self) -> Any:
        return self.env.action_space.sample()

    async def reset(self) -> Tuple[Any, Dict[str, Any]]:
        return self.env.reset()

    async def step(self, action) -> Tuple[Any, SupportsFloat, bool, bool, Dict[str, Any]]:
        if self.env_id == "case-error":
            raise Exception("Random Error")
        return self.env.step(action)

    async def close(self):
        self.env.close()

    async def set_scenario(self, scenario):
        self.env.scenario = scenario

    async def get_scenario(self):
        if self.env.scenario is None:
            return Scenario({"dummy": 0})
        return self.env.scenario

    async def get_render(self):
        return f"Production Scheduling Env"

    async def get_mappings(self) -> Dict[str, Any]:
        """Name every sensor and action variable for the AMESA mapping screen.

        Without this override the Discrete(64) action has an empty name, so a
        platform build stops at AWAITING_MAPPING_CONFIGURATION.
        """
        action_space = await self.action_space_info()
        sensor_space = await self.sensor_space_info()

        action_mappings = amesa_space_utils.convert_space_to_json(action_space, is_condensed_enabled=False)
        sensor_mappings = amesa_space_utils.convert_space_to_json(sensor_space, is_condensed_enabled=False)

        _name_mappings(sensor_mappings, default_mapped="sensor")
        _name_mappings(action_mappings, default_mapped="action")

        return {
            "action_space": {"space": action_space, "mappings": action_mappings},
            "sensor_space": {"space": sensor_space, "mappings": sensor_mappings},
        }
