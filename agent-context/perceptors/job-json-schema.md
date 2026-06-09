# Perceptor Job JSON Schema

Perceptors are serialized in the agent JSON perceptor list.

## Core shape

```json
{
  "name": "kinematics",
  "type": "Perceptor",
  "config": {
    "remote_address": null,
    "impl_cls": { "cls_name": "MyPerceptor", "cls_module": "my_agent.perceptor", "cls_src": "<base64-pickle>", "cls_deps": [] },
    "variables": ["velocity", "acceleration"]
  }
}
```

## Key meaning

- `variables` declares emitted keys.
- `impl_cls` stores portable implementation details for deployment.
