# Perceptor Publishing

Portable perceptor package example:

```toml
[project]
name = "my-perceptor"
version = "0.1.0"
dependencies = ["amesa-core"]

[amesa]
type = "perceptor"
variables = ["derived_key1", "derived_key2"]
entrypoint = "my_module.perceptor:MyPerceptor"
```

## Requirements

- `type` must be `"perceptor"`.
- `variables` must match emitted output keys.
- `entrypoint` must be `"module.path:ClassName"`.
- Use top-level `[amesa]` (not `[tool.amesa]`).
