# AgentController Job JSON Schema

Controller agents are serialized similarly to teachers, but with controller type metadata.

## Core shape

```json
{
  "name": "my-controller-agent",
  "type": "AgentController",
  "config": {
    "remote_address": null,
    "impl_cls": { "cls_name": "MyController", "cls_module": "my_orchestration.controller", "cls_src": "<base64-pickle>", "cls_deps": [] },
    "impl_cls_data": { "guidance": null, "goals": [], "constraints": null },
    "scenarios": []
  }
}
```

## Key meaning

- `impl_cls`: serialized controller class.
- `scenarios`: runtime scenario list for evaluation/execution contexts.
- No PPO training fields are required for purely rule-based controllers.
