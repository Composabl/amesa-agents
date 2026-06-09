# Selector Publishing

Use `amesa selector` commands for selector lifecycle: scaffold, package, and publish.

## Portable package config (`pyproject.toml`)

Teacher selector:

```toml
[project]
name = "my-selector"
version = "0.1.0"
dependencies = ["amesa-core"]

[amesa]
type = "selector-teacher"
entrypoint = "my_selector.teacher:Teacher"
```

Controller selector:

```toml
[project]
name = "my-selector"
version = "0.1.0"
dependencies = ["amesa-core"]

[amesa]
type = "selector-controller"
entrypoint = "my_selector.controller:Controller"
```

## Compliance checklist

- `[amesa].type` is exactly `selector-teacher` or `selector-controller`.
- `[amesa].entrypoint` is `module.path:ClassName`.
- Selector class implements the correct base interface (teacher/controller).
- Selector chooses valid child indices and is configured with at least one child.
