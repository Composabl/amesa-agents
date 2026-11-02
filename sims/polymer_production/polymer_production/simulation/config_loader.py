"""
Configuration loader for generic production scheduling simulation.
Loads YAML config and generates enums, action spaces, observation spaces dynamically.
"""

import yaml
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from pathlib import Path


@dataclass
class StageConfig:
    name: str
    machine_count: int
    machine_prefix: str
    
    @property
    def machine_names(self) -> List[str]:
        return [f"{self.machine_prefix}_{i+1}" for i in range(self.machine_count)]


@dataclass
class ProductConfig:
    id: str
    batch_yield: int
    stage_times: List[int]  # one per stage
    price: float
    base_demand: int
    cost: float
    
    def get_time(self, stage_idx: int) -> int:
        return self.stage_times[stage_idx] if stage_idx < len(self.stage_times) else 0


@dataclass
class WorkerConfig:
    id: str
    skills: List[str]  # stage names this worker can operate
    shift_start: int
    shift_end: int


@dataclass
class RewardConfig:
    type: str = "profit"
    opportunity_cost: bool = True
    waste_cost: bool = True


@dataclass
class ProductionConfig:
    stages: List[StageConfig]
    products: List[ProductConfig]
    workers: List[WorkerConfig]
    episode_minutes: int = 480
    demand_noise: float = 0.3
    reward: RewardConfig = field(default_factory=RewardConfig)
    
    # Cached computed properties
    _product_map: Dict[str, ProductConfig] = field(default_factory=dict, init=False)
    _stage_map: Dict[str, StageConfig] = field(default_factory=dict, init=False)
    _worker_map: Dict[str, WorkerConfig] = field(default_factory=dict, init=False)
    _action_list: List[Dict] = field(default_factory=list, init=False)
    
    def __post_init__(self):
        self._product_map = {p.id: p for p in self.products}
        self._stage_map = {s.name: s for s in self.stages}
        self._worker_map = {w.id: w for w in self.workers}
        self._build_action_list()
    
    def _build_action_list(self):
        """Build the complete action list from config."""
        self._action_list = [{"type": "wait", "action_id": 0}]  # Action 0 = wait
        
        action_id = 1
        for stage_idx, stage in enumerate(self.stages):
            # Workers skilled in this stage
            skilled_workers = [w for w in self.workers if stage.name in w.skills]
            
            for worker in skilled_workers:
                for product in self.products:
                    for machine_idx in range(stage.machine_count):
                        self._action_list.append({
                            "type": stage.name,
                            "action_id": action_id,
                            "stage_idx": stage_idx,
                            "stage_name": stage.name,
                            "worker_id": worker.id,
                            "product_id": product.id,
                            "machine_idx": machine_idx,
                            "machine_name": stage.machine_names[machine_idx],
                        })
                        action_id += 1
    
    @property
    def action_space_size(self) -> int:
        return len(self._action_list)
    
    @property
    def num_stages(self) -> int:
        return len(self.stages)
    
    @property
    def num_products(self) -> int:
        return len(self.products)
    
    @property
    def num_workers(self) -> int:
        return len(self.workers)
    
    @property
    def total_machines(self) -> int:
        return sum(s.machine_count for s in self.stages)
    
    def get_action(self, action_id: int) -> Dict:
        if 0 <= action_id < len(self._action_list):
            return self._action_list[action_id]
        return self._action_list[0]  # default to wait
    
    def get_product(self, product_id: str) -> ProductConfig:
        return self._product_map.get(product_id)
    
    def get_stage(self, stage_name: str) -> StageConfig:
        return self._stage_map.get(stage_name)
    
    def get_worker(self, worker_id: str) -> WorkerConfig:
        return self._worker_map.get(worker_id)
    
    def get_stage_for_machine(self, machine_name: str) -> Optional[StageConfig]:
        for stage in self.stages:
            if machine_name in stage.machine_names:
                return stage
        return None
    
    def get_machine_stage_idx(self, machine_name: str) -> int:
        for idx, stage in enumerate(self.stages):
            if machine_name in stage.machine_names:
                return idx
        return -1
    
    def get_workers_for_stage(self, stage_name: str) -> List[WorkerConfig]:
        return [w for w in self.workers if stage_name in w.skills]
    
    def get_machines_for_stage(self, stage_name: str) -> List[str]:
        stage = self.get_stage(stage_name)
        return stage.machine_names if stage else []
    
    def observation_space_shape(self) -> int:
        """Calculate observation space dimension."""
        # Workers: busy_time_remaining per worker
        worker_dims = self.num_workers
        # Equipment: (recipe_id, time_remaining) per machine
        equip_dims = self.total_machines * 2
        # Products: completed count per product
        product_dims = self.num_products
        # Market: price, demand, cost per product
        market_dims = self.num_products * 3
        # Action mask
        mask_dims = self.action_space_size
        
        return worker_dims + equip_dims + product_dims + market_dims + mask_dims


def load_config(config_path: Optional[str] = None) -> ProductionConfig:
    """Load production config from YAML file."""
    if config_path is None:
        # Look for config in package root config/ directory
        config_path = Path(__file__).parent.parent / "config" / "production_config.yaml"
    
    with open(config_path, 'r') as f:
        raw = yaml.safe_load(f)
    
    stages = [StageConfig(**s) for s in raw.get("stages", [])]
    products = [ProductConfig(**p) for p in raw.get("products", [])]
    workers = [WorkerConfig(**w) for w in raw.get("workers", [])]
    episode_minutes = raw.get("episode_minutes", 480)
    demand_noise = raw.get("demand_noise", 0.3)
    reward_raw = raw.get("reward", {})
    reward = RewardConfig(**reward_raw)
    
    return ProductionConfig(
        stages=stages,
        products=products,
        workers=workers,
        episode_minutes=episode_minutes,
        demand_noise=demand_noise,
        reward=reward,
    )


# Global config instance (loaded on first import)
_config: Optional[ProductionConfig] = None


def get_config(config_path: Optional[str] = None) -> ProductionConfig:
    """Get global config instance, loading if necessary."""
    global _config
    if _config is None:
        _config = load_config(config_path)
    return _config


def reset_config():
    """Reset global config (useful for testing)."""
    global _config
    _config = None


# Dynamic enums generated from config
def make_enums(config: ProductionConfig):
    """Create dynamic enums from config."""
    
    # Product enum
    product_members = {"none": 0}
    for i, p in enumerate(config.products, 1):
        product_members[p.id.upper()] = i
    ProductNames = Enum("ProductNames", product_members)
    
    # Machine/Equipment enum
    machine_members = {"none": 0}
    idx = 1
    for stage in config.stages:
        for m_name in stage.machine_names:
            machine_members[m_name.upper()] = idx
            idx += 1
    EquipmentNames = Enum("EquipmentNames", machine_members)
    
    # Worker enum
    worker_members = {}
    for i, w in enumerate(config.workers, 1):
        worker_members[w.id.upper()] = i
    WorkerNames = Enum("WorkerNames", worker_members)
    
    # Stage enum
    stage_members = {}
    for i, s in enumerate(config.stages):
        stage_members[s.name.upper()] = i
    StageNames = Enum("StageNames", stage_members)
    
    return {
        "ProductNames": ProductNames,
        "EquipmentNames": EquipmentNames,
        "WorkerNames": WorkerNames,
        "StageNames": StageNames,
    }


if __name__ == "__main__":
    # Test loading
    cfg = load_config()
    print(f"Stages: {cfg.num_stages}")
    print(f"Products: {cfg.num_products}")
    print(f"Workers: {cfg.num_workers}")
    print(f"Total machines: {cfg.total_machines}")
    print(f"Action space size: {cfg.action_space_size}")
    print(f"Obs space shape: {cfg.observation_space_shape()}")
    print("\nActions:")
    for a in cfg._action_list[:5]:
        print(f"  {a}")
    print("  ...")
    for a in cfg._action_list[-3:]:
        print(f"  {a}")
    
    enums = make_enums(cfg)
    print("\nEnums:")
    for name, enum_cls in enums.items():
        print(f"  {name}: {[e.name for e in enum_cls]}")