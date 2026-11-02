# Orchestrator Job JSON Schema

Orchestrators are serialized by `AgentOrchestrator.to_json` into an `AgentOrchestratorSchema`
with an `AgentOrchestratorOptions` config (`amesa_core/amesa_core/config/agent_config.py`; nested
models in `config/trainer_config.py`). In the orchestration JSON they are listed under
`agent_orchestrators` (`OrchestrationSchema`, `amesa_core/amesa_core/orchestration/orchestration.py`);
children are referenced by name and must appear under `agents` (or `agent_orchestrators` for a
nested orchestrator).

## Core shape

Generated with `AgentOrchestrator("my-orchestrator", MyOrchestrator, children=[...]).to_json()`
(controller variant):

```json
{
  "name": "my-orchestrator",
  "type": "AgentOrchestratorController",
  "config": {
    "remote_address": null,
    "impl_cls": { "cls_name": "MyOrchestrator", "cls_module": "my_orchestrator.controller", "cls_src": "<base64 cloudpickle>", "cls_deps": [] },
    "impl_cls_data": { "guidance": null, "goals": [], "constraints": null },
    "order_type": "fixed",
    "repeat_type": "once",
    "learning": { "training_cycles": null, "train_batch_size": 4000, "replay_buffer_size": 50000, "needs_warmup": false, "rl_algo": "PPO", "...": "..." },
    "resources": { "workers": 1, "learner_workers": 0, "envs_per_worker": 1, "...": "..." },
    "model": { "checkpoint_uri": "/tmp/amesa", "fc_layers": [256, 256] },
    "model_io": {
      "sensor_space": null, "action_space": null,
      "custom_action_space": false, "custom_sensor_space": false,
      "filtered_sensor_space": [], "sim_action_space": null
    },
    "scenarios": [],
    "scenarios_current_idx": 0,
    "children": ["startup", "steady", "recovery"]
  }
}
```

## Key meaning

- `type`: `"AgentOrchestrator"` (teacher impl) or `"AgentOrchestratorController"` (controller impl)
  (`config/e_agent_type.py`, `AgentDirector`). `"AgentOrchestratorGoal"` also exists and is
  loaded with `AgentTeacherJson` (`agent_orchestrator.py`, `from_json`). Legacy
  `SkillSelector*` / `SkillOrchestrator*` strings are renamed on load (`utils/v1_compat.py`,
  `RENAME_TYPE_STRINGS`).
- `children`: list of child **names**; the list index is the action value that selects the child.
- `order_type`: `"fixed"` (default) | `"variable"`; `repeat_type`: `"once"` (default) | `"repeat"`.
  They drive the fixed-order action mask for teacher orchestrators (see `quirks.md`).
- `impl_cls` / `remote_address`: one or the other — a published orchestrator has
  `remote_address` (URL) and `impl_cls: null`; a local class is serialized into `impl_cls`
  (`CLSSchema`).
- `learning`, `resources`, `model`: PPO settings, present for both variants (the controller
  variant is never trained; `process_kwargs` skips `train_batch_size` / `training_cycles` /
  `fc_layers` for it). Warm-up is `learning.needs_warmup`.
- The policy's action space is not stored here; it is always `Discrete(len(children))`.
- Orchestration-level legacy alias: `OrchestrationSchema.from_orchestration` also writes
  `skill_selectors` with the same content as `agent_orchestrators`.
- `AgentOrchestratorController` entries are treated as having no learned weights when a job
  bundle is staged (`orchestration/job_bundle.py`, `_CONTROLLER_TYPES`).
