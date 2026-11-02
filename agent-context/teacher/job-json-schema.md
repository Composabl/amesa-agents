# AgentTeacher Job JSON Schema

Serialized teacher agents live under the agent config block: `AgentSchema` with `config` of type
`AgentDRLOptions` (`amesa_core/config/agent_config.py`; nested models in `config/trainer_config.py`).

## Core fields

```json
{
  "name": "my-agent",
  "type": "AgentTeacher",
  "config": {
    "remote_address": null,
    "impl_cls": { "cls_name": "MyTeacher", "cls_module": "my_orchestration.teacher", "cls_src": "<base64-pickle>", "cls_deps": [] },
    "impl_cls_data": { "guidance": null, "goals": [], "constraints": null },
    "learning": { "training_cycles": 100, "train_batch_size": 4000, "rl_algo": "PPO" },
    "resources": { "workers": 1, "learner_workers": 0, "envs_per_worker": 1 },
    "model": { "checkpoint_uri": "/tmp/amesa", "fc_layers": [256, 256] },
    "model_io": {},
    "scenarios": [],
    "scenarios_current_idx": 0,
    "use_image_nn": false
  }
}
```

## Field intent

- `type`: `"AgentTeacher"` (code teacher, instantiated with no args) or `"AgentTeacherGoal"`
  (no-code, instantiated as `impl_cls(**impl_cls_data)`) — see `config/e_agent_type.py` `AgentDirector`
  and `orchestration/agent/agent.py` `get_impl_cls_instance`.
- `remote_address` / `impl_cls`: serialization sets one or the other — a published (remote) teacher
  has `remote_address` and `impl_cls: null`; a local class is serialized into `impl_cls`
  (`CLSSchema`: `cls_name`, `cls_module`, `cls_src`, `cls_deps`), or `impl_cls` may be a plain string.
- `impl_cls_data.goals`: embedded goal config for goal-based teachers. For a code teacher with
  `remote_address`, these goals are UI guidance that override `compute_reward` /
  `compute_success_criteria` / `compute_termination` (`orchestration/agent/guidance_overrides.py`).
- `learning.training_cycles` defaults to `null`; other `learning` keys: `replay_buffer_size`, `needs_warmup`,
  `gamma`, `learning_rate`, `train_batch_size_per_learner`, `grad_clip`, `grad_clip_by`.
- `learning/resources/model`: PPO and runtime resource settings.
- `model_io`: sensor/action-space override payloads.
- `scenarios`: scenario list cycled during training.
