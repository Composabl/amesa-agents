# SkillController Job JSON Schema

Controller skills are serialized similarly to teachers, but with controller type metadata.

## Core shape

```json
{
  "name": "my-controller-skill",
  "type": "SkillController",
  "config": {
    "remote_address": null,
    "impl_cls": { "cls_name": "MyController", "cls_module": "my_agent.controller", "cls_src": "<base64-pickle>", "cls_deps": [] },
    "impl_cls_data": { "guidance": null, "goals": [], "constraints": null },
    "scenarios": []
  }
}
```

## Key meaning

- `impl_cls`: serialized controller class.
- `scenarios`: runtime scenario list for evaluation/execution contexts.
- No PPO training fields are required for purely rule-based controllers.
