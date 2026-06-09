# Coordinated Publishing

Portable coordinated package example:

```toml
[project]
name = "my-coordinated-skill"
version = "0.1.0"
dependencies = ["amesa-core"]

[amesa]
type = "skill-coordinated-set"
entrypoint = "my_module.coach:MyCoach"
```

## Requirements

- `type` must be `"skill-coordinated-set"` or `"skill-coordinated-population"`.
- `entrypoint` points to the `SkillCoach` subclass.
- Use top-level `[amesa]` (not `[tool.amesa]`).
