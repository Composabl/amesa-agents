# Orchestrator Interface

An orchestrator package's entrypoint class subclasses `AgentTeacher` (type `orchestrator-teacher`)
or `AgentController` (type `orchestrator-controller`). The method sets and signatures are exactly
those of the base classes — see `../teacher/reference.md` and `../controller/reference.md` — with
one difference: **the action is a child index**.

Validation maps `orchestrator-teacher` → `AgentTeacher` and `orchestrator-controller` →
`AgentController` and requires every abstract method as `async def`
(`amesa_core/amesa_core/utils/validate_util.py`, `validate_plugin`, `validate_abstract_class_implementation`):

- `AgentTeacher`: `compute_reward`, `compute_success_criteria`, `transform_action`, `filtered_sensor_space`.
- `AgentController`: `compute_action`, `filtered_sensor_space`, `compute_success_criteria`, `compute_termination`.

## Action space and action meaning

- The orchestrator's action space is always `Discrete(len(children))`
  (`AgentOrchestrator.get_action_space`; reset by the trainer in
  `agent_processor_component.py` `_initialize_orchestrator_child_processors`).
- Index `i` selects `children[i]` — the position in the orchestrator's children list (on the
  platform, the order of `skills` / `children` in the workflow).
- The returned value goes through `child_index` (`amesa_core/amesa_core/utils/space_util.py`):
  a scalar or a one-element list/array is accepted (`2`, `[2]`, `np.int64(2)`); anything with
  more than one element, or an index outside `0..len(children)-1`, raises `ValueError`.
- The `action` argument your methods receive (previous action) is the **child index** chosen
  on the previous step, `None` on the first step (`amesa_core/.../networking/remote_agent/v2/event_agent_processor.py`,
  `_record_sent_action`).

## Call order per step

**Teacher orchestrator** (`agent_processor_component.py` `compute_step`):

1. `transform_sensors(sensors, None)`.
2. `compute_reward` / `compute_success_criteria` / `compute_termination` with the previous child
   index (skipped on the reset step). Success or termination ends the episode here.
3. Action mask = fixed-order mask (see quirks) AND `compute_action_mask(transformed_sensors, previous_child_index)`.
4. Policy samples from `Discrete(n)` → `transform_action(transformed_sensors, action)` → `child_index(...)`.
5. The selected child's `compute_step` runs (greedy, `previous_action=None`) and its action goes to the sim.

**Controller orchestrator** (`agent_processor_component.py` `_compute_controller_step`):

1. `compute_action(raw_amesa_sensors, previous_child_index)` → `child_index(...)`.
2. The selected child's `compute_step` runs; its action goes to the sim, and the step's
   success/termination flags are copied from the child's step result. The orchestrator
   controller's own `compute_success_criteria` / `compute_termination` are **not** called here
   (they are called by the validators only).

Both variants are instantiated with no arguments and re-instantiated at every episode reset
(`agent.py` `get_impl_cls_instance`, `agent_processor_component.py` `reset`).

## Minimal controller orchestrator

Verified with `amesa orchestrator validate` and with `validate_util.validate_plugin` against a
mock sim with `Discrete(3)`.

```python
# my_orchestrator/controller.py
from typing import Dict, List

from amesa_core import AgentController

# Child index = position of the skill in the orchestrator's children list
STARTUP, STEADY, RECOVERY = 0, 1, 2


class MyOrchestrator(AgentController):
    # required: return the index of the child skill that acts this step
    async def compute_action(self, transformed_sensors: Dict, action):
        """:param transformed_sensors: raw AMESA sensors (sim sensors + perceptor outputs).
        :param action: the child index this orchestrator picked last step; None on the first step.
        :returns: an int (or one-element list) in range(number of children)."""
        state = float(transformed_sensors["process_state"])
        if state < 0.05:
            return RECOVERY
        if state < 0.2:
            return STARTUP
        return STEADY

    # required
    async def filtered_sensor_space(self) -> List[str]:
        return ["process_state"]

    # required (validated, but the trainer does not end episodes on them; see quirks.md)
    async def compute_success_criteria(self, transformed_sensors: Dict, action) -> bool:
        return False

    # required
    async def compute_termination(self, transformed_sensors: Dict, action) -> bool:
        return False
```

## Minimal teacher orchestrator

Verified the same way.

```python
# my_orchestrator/teacher.py
from typing import Dict, List

from amesa_core import AgentTeacher


class MyOrchestrator(AgentTeacher):
    # required
    async def compute_reward(self, transformed_sensors: Dict, action, sim_reward: float) -> float:
        """:param action: the child index chosen last step (the one that led here)."""
        return float(transformed_sensors["process_state"][0])

    # required
    async def compute_success_criteria(self, transformed_sensors: Dict, action) -> bool:
        return bool(float(transformed_sensors["process_state"][0]) >= 0.9)

    # required: the policy samples from Discrete(len(children)); return a child index
    async def transform_action(self, transformed_sensors: Dict, action):
        return action

    # required
    async def filtered_sensor_space(self) -> List[str]:
        return ["process_state", "temperature"]

    # optional
    async def compute_termination(self, transformed_sensors: Dict, action) -> bool:
        return bool(float(transformed_sensors["process_state"][0]) < 0.05)

    # optional: one entry per child (1 = allowed); AND-combined with the fixed-order mask
    async def compute_action_mask(self, transformed_sensors: Dict, action):
        return None
```

Optional teacher hooks (`transform_sensors`, `reset`, `compute_scenario_advancement`, …) behave
as in `../teacher/reference.md`, except `get_custom_action_space` (ignored, see quirks).

## Wiring in local SDK code

```python
from amesa_core import AgentOrchestrator

orch = AgentOrchestrator(
    "process-orchestrator",
    MyOrchestrator,                                  # the class, not an instance
    children=["startup", "steady-state", "recovery"],  # names (or Agent objects); order = index
    fixed_order=False,                               # optional; default is fixed order
    repeat=False,                                    # optional
)
orchestration.add_agent(orch)                        # children must also be added to the orchestration
```

Signature: `AgentOrchestrator(name: str, impl_cls, config: AgentOrchestratorSchema | dict = {}, **kwargs)`;
`children`, `fixed_order`, `repeat`, `needs_warmup`, `train_batch_size`, `training_cycles`,
`fc_layers` are keyword-only (`process_kwargs`). Passing children as the third positional
argument puts them in `config` and fails.
Alternative: `orchestration.add_orchestrator_agent(orchestrator_agent, children=[], fixed_order=False, repeat=False, needs_warmup=False)`
(`amesa_core/amesa_core/orchestration/orchestration.py`).
