# AgentController Publishing

Portable controller package example:

```toml
[project]
name = "my-controller"
version = "0.1.0"
dependencies = ["amesa-core"]

[amesa]
type = "agent-controller"
entrypoint = "my_module.controller:MyController"
```

## Requirements

- `type` must be `"agent-controller"`.
- `entrypoint` must be `"module.path:ClassName"`.
- Use top-level `[amesa]` (not `[tool.amesa]`).
