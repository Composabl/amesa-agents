# Goals Publishing

Goals are **not** published as a standalone component type.

Publish them through a teacher package:

```toml
[amesa]
type = "agent-teacher"
entrypoint = "my_module.goal_teacher:MyGoalBasedTeacher"
```

If your class subclasses `Goal`/`CoordinatedGoal`, it is still published as `agent-teacher`.
