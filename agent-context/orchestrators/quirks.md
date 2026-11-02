# Orchestrator Quirks

- **There is no `AgentOrchestratorController` class.** It is only a type string
  (`amesa_core/amesa_core/config/e_agent_type.py`). Programmed orchestrators subclass
  `AgentController`; learned ones subclass `AgentTeacher`. `AgentOrchestrator` is a wrapper node,
  never a base class (`orchestration/agent/agent_orchestrator.py`).
- **The action is a child index.** It must be a scalar or one-element list/array in
  `0..len(children)-1`; anything else raises `ValueError` at runtime
  (`amesa_core/amesa_core/utils/space_util.py`, `child_index`). The CLI scaffold controller
  returns `[3]` for three children — out of range; don't copy it
  (`amesa_cli/amesa_cli/template/orchestrator_controller/{{NAME_MODULE}}/controller.py`).
- **Index order = children order.** Index `i` is `children[i]` — the `children` list of the
  `AgentOrchestrator` / the order of `skills` in the deployed workflow (`agent_orchestrator.py`,
  `get_children`; `agent_processor_component.py` `_initialize_orchestrator_child_processors`).
- **Default is fixed order.** `AgentOrchestratorOptions` defaults to `order_type="fixed"`,
  `repeat_type="once"` (`config/agent_config.py`). For a teacher orchestrator this adds a mask:
  first step only child 0; afterwards only the previous child or the next one; no wrap from the
  last child back to 0 unless `repeat` (`utils/space_utils.py`, `compute_orchestrator_action_mask`).
  Pass `fixed_order=False` to `AgentOrchestrator(...)` (or `sequenceType: "variable"` in
  `orchestration_workflow_deploy`, whose default is `"variable"`) for free switching. The mask is
  AND-combined with your `compute_action_mask` (`agent_processor_component.py` `compute_action_mask`).
  Controller orchestrators are not masked — `compute_action` can return any valid index.
- **`previous action` is the child index**, not the child's sim action, for both variants
  (`networking/remote_agent/v2/event_agent_processor.py`, `_record_sent_action`). `compute_action_mask`
  receives the previous child index (`None` on the first step).
- **Teacher orchestrator: `get_custom_action_space` is ignored.** The trainer overwrites the
  action space with `Discrete(len(children))` after resolving it
  (`agent_processor_component.py` `_initialize_orchestrator_child_processors`). `transform_action`
  receives a sampled index; if it returns a tuple, element `[1]` is used
  (`_compute_orchestrator_child_action`).
- **Controller orchestrator: its own success/termination do not end episodes during training.**
  `_compute_controller_step` never calls `compute_success_criteria` / `compute_termination`; it copies
  `teacher_success` / `teacher_terminated` from the selected child's step, which runs with
  `previous_action=None`, so a teacher child's scoring is skipped (`agent_processor_component.py`,
  `_compute_controller_step` and `compute_step`). Episodes then end on sim termination/truncation.
  The methods are still abstract and must return `bool` for validation.
- **Controller orchestrator: `transform_sensors` is never called**; `compute_action` gets the raw
  AMESA sensors (sim + perceptor outputs) as scalar-shaped arrays, same as any controller
  (`_compute_controller_step`).
- **Children must be trained first** when they are teachers: each teacher child needs a
  `checkpoint_uri` or init raises `Orchestrator child agent '<name>' is missing checkpoint_uri`.
  Children run with `is_training=False` and `explore=False` (greedy)
  (`_initialize_orchestrator_child_processors`, `_compute_orchestrator_child_action`).
- **An orchestrator needs at least one child** (`AgentOrchestrator.init`: "A orchestrator agent
  requires atleast 1 child").
- **`AgentOrchestrator(...)` instantiates `impl_cls()` at construction** to decide the variant
  (`get_type_from_impl_cls`), and the runtime re-instantiates it with no arguments at every
  episode reset (`agent.py` `get_impl_cls_instance`; `agent_processor_component.py` `reset`).
  `__init__` must take no required arguments; state does not survive episodes.
- **`children` is keyword-only.** `AgentOrchestrator(name, cls, [a, b])` passes the list as
  `config` and fails; use `children=[...]` (`agent_orchestrator.py`, `__init__` / `process_kwargs`).
- `add_orchestrator_agent(..., fixed_order=False, needs_warmup=True)` raises; and its
  `fixed_order` / `repeat` arguments are only applied when it wraps a plain `Agent`, not an
  existing `AgentOrchestrator` (`orchestration/orchestration.py`, `add_orchestrator_agent`).
- **`amesa orchestrator validate` is static only** — it does not run against a mock sim and
  has no `--static` / `--project` flags (`amesa_cli/amesa_cli/cli/cli_orchestrator.py`;
  `validate_util.MOCK_SIM_TYPES` excludes orchestrators). Out-of-range indices or wrong-shaped
  returns are only caught at runtime. `validate_util.validate_component` can run an orchestrator
  against a mock sim with `Discrete(<children>)` (`component_action_space`); whether
  `amesa_orchestrator_validate` does so is unverified.
- **Orchestrator `type` values differ from skill types**: `orchestrator-teacher` /
  `orchestrator-controller`, not `agent-*` (`utils/plugin_util.py` `get_type`;
  `validate_util.PLUGIN_TYPES_BY_KIND["orchestrator"]`). `selector-*` is accepted as a legacy alias.
- The CLI scaffolds' `__init__` overrides do not call `super().__init__()` and declare
  `transform_sensors(self, sensors, action)` / `transform_action` on the controller, which are not
  part of the `AgentController` interface (`amesa_cli/amesa_cli/template/orchestrator_controller/`).
