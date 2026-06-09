# SkillTeacher Job JSON Schema

Serialized teacher skills live under the skill config block (`SkillDRLOptions` style).

## Core fields

```json
{
  "name": "my-skill",
  "type": "SkillTeacher",
  "config": {
    "remote_address": null,
    "impl_cls": { "cls_name": "MyTeacher", "cls_module": "my_agent.teacher", "cls_src": "<base64-pickle>", "cls_deps": [] },
    "impl_cls_data": { "guidance": null, "goals": [], "constraints": null },
    "learning": { "training_cycles": 100, "train_batch_size": 4000, "rl_algo": "PPO" },
    "resources": { "workers": 1, "learner_workers": 0, "envs_per_worker": 1 },
    "model": { "checkpoint_uri": "/tmp/amesa", "fc_layers": [256, 256] },
    "model_io": {},
    "scenarios": []
  }
}
```

## Field intent

- `impl_cls`: serialized teacher implementation.
- `impl_cls_data.goals`: embedded goal config when using goal-based teachers.
- `learning/resources/model`: PPO and runtime resource settings.
- `model_io`: sensor/action-space override payloads.
- `scenarios`: scenario list cycled during training.
