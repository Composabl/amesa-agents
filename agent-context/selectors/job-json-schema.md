# Selector Job JSON Schema

Serialized selectors use `SkillSelectorSchema`-style blocks.

## Teacher selector shape (`SkillSelector`)

```json
{
  "name": "my-selector",
  "type": "SkillSelector",
  "config": {
    "remote_address": null,
    "impl_cls": { "cls_name": "MySelectorTeacher", "cls_module": "my_selector.teacher", "cls_src": "<base64-pickle>", "cls_deps": [] },
    "impl_cls_data": { "guidance": null, "goals": [], "constraints": null },
    "order_type": "fixed",
    "repeat_type": "once",
    "children": ["child-skill-a", "child-skill-b"],
    "learning": { "training_cycles": 100, "train_batch_size": 4000, "rl_algo": "PPO" },
    "resources": { "workers": 1, "learner_workers": 0, "envs_per_worker": 1 },
    "model": { "checkpoint_uri": "/tmp/amesa", "fc_layers": [256, 256] },
    "model_io": {},
    "scenarios": []
  }
}
```

## Controller selector shape (`SkillSelectorController`)

```json
{
  "name": "my-selector",
  "type": "SkillSelectorController",
  "config": {
    "remote_address": null,
    "impl_cls": { "cls_name": "MySelectorController", "cls_module": "my_selector.controller", "cls_src": "<base64-pickle>", "cls_deps": [] },
    "impl_cls_data": { "guidance": null, "goals": [], "constraints": null },
    "order_type": "fixed",
    "repeat_type": "once",
    "children": ["child-skill-a", "child-skill-b"],
    "learning": { "needs_warmup": false },
    "resources": {},
    "model": {},
    "model_io": {},
    "scenarios": []
  }
}
```

## Field intent

- `type`: selector runtime type (`SkillSelector` or `SkillSelectorController`).
- `children`: ordered child skill names; selected index maps to this order.
- `order_type`: child selection ordering mode (`fixed` or `variable`).
- `repeat_type`: replay behavior (`once` or `repeat`).
- `impl_cls` / `remote_address`: local serialized implementation or remote plugin source.
