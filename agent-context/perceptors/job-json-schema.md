# Perceptor Job JSON Schema

Perceptors are serialized in the orchestration JSON perceptor list.

## Core shape

```json
{
  "name": "kinematics",
  "type": "Perceptor",
  "config": {
    "remote_address": null,
    "impl_cls": { "cls_name": "MyPerceptor", "cls_module": "my_orchestration.perceptor", "cls_src": "<base64-pickle>", "cls_deps": [] },
    "variables": ["velocity", "acceleration"]
  }
}
```

## Key meaning

- `variables` declares emitted keys.
- `impl_cls` stores portable implementation details for deployment.
