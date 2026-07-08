# Goals Overview

Goals are reusable `AgentTeacher` subclasses that package reward, success, and termination behavior into reusable scaffolding.

Common goals:

- `ApproachGoal`
- `AvoidGoal`
- `MaintainGoal`
- `MaximizeGoal`
- `MinimizeGoal`
- `CoordinatedGoal` (composition wrapper)

Use goals when you want strong default reward scaffolding and only need to customize the surrounding teacher interface methods.
