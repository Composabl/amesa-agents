# SkillTeacher Publishing

To publish a teacher as a portable component, package it with a `pyproject.toml`:

```toml
[project]
name = "my-teacher"
version = "0.1.0"
dependencies = ["amesa-core"]

[amesa]
type = "skill-teacher"
entrypoint = "my_module.teacher:MyTeacher"
```

## Requirements

- `type` must be `"skill-teacher"`.
- `entrypoint` must be `"module.path:ClassName"`.
- Use top-level `[amesa]` (not `[tool.amesa]`).
