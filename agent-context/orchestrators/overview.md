# Orchestrator Overview

An orchestrator decides **which child skill acts at each step**. Its action is the index of one of
its children; the selected child then computes the action that is sent to the sim. The
orchestrator's own index never reaches the sim (`amesa_train/amesa_train/v2/agent_processor_component.py`,
`_compute_orchestrator_child_action` / `_compute_controller_step`).

```
Orchestration
└── orchestrator "process-orchestrator"   ← action = child index
    ├── skill "startup"        (index 0)
    ├── skill "steady-state"   (index 1)
    └── skill "recovery"       (index 2)
```

## There is no separate orchestrator base class

You implement an orchestrator with the **same base classes as a skill**:

| Variant | Base class you subclass | pyproject `[amesa] type` | Job JSON `type` |
| --- | --- | --- | --- |
| Learned (PPO) | `AgentTeacher` | `"orchestrator-teacher"` | `"AgentOrchestrator"` |
| Programmed (rules) | `AgentController` | `"orchestrator-controller"` | `"AgentOrchestratorController"` |

- `AgentOrchestrator` (`amesa_core/amesa_core/orchestration/agent/agent_orchestrator.py`) is **not** a
  class you subclass. It is the SDK node that wraps your teacher/controller class plus the list
  of children (`AgentOrchestrator(name, impl_cls, children=[...])`). It infers the variant by
  instantiating `impl_cls()`: an `AgentTeacher` gives `AgentOrchestrator`, an `AgentController`
  gives `AgentOrchestratorController` (`get_type_from_impl_cls`).
- `AgentOrchestratorController` exists only as a type string (`AgentDirector.ORCHESTRATOR_CONTROLLER`,
  `amesa_core/amesa_core/config/e_agent_type.py`). There is no Python class of that name — do not
  try to import or subclass it.

## Learned vs programmed

- **Teacher orchestrator**: a PPO policy over `Discrete(len(children))` learns when to switch.
  You write reward / success / termination like any teacher; its children must already be
  trained (they run frozen and greedy while the orchestrator trains).
- **Controller orchestrator**: `compute_action` returns the child index from explicit rules; no
  training of the orchestrator itself.

## Where it fits

Perceptors run first and add their outputs to the sensor dict; the orchestrator reads the
sensors, picks a child, and the child (teacher or controller skill) reads the same sensors and
acts. Orchestrators can be nested (a child can itself be an orchestrator). On the platform the
tree is built with `orchestration_workflow_deploy` (see `publishing.md`).

## Imports

```python
from amesa_core import AgentTeacher       # learned orchestrator
from amesa_core import AgentController    # programmed orchestrator
from amesa_core import AgentOrchestrator  # SDK-side wrapper node (local orchestration code only)
```

Long forms: `amesa_core.orchestration.agent.agent_teacher.AgentTeacher`,
`amesa_core.orchestration.agent.agent_controller.AgentController`,
`amesa_core.orchestration.agent.agent_orchestrator.AgentOrchestrator`.

Legacy names: `SkillSelector` / `Selector` / `SkillOrchestrator` → `AgentOrchestrator`;
`SkillSelectorController` / `SkillOrchestratorController` → `AgentOrchestratorController`
(`amesa_core/amesa_core/utils/legacy_import_rewrite.py`, `utils/v1_compat.py` `RENAME_TYPE_STRINGS`).
