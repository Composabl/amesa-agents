# Goals Overview

Goals are reusable `AgentTeacher` subclasses (via the abstract base `Goal`) that package reward, success, and termination behavior into reusable scaffolding.

All goal classes live in `amesa_core.orchestration.agent.goals` (also re-exported from `amesa_core`):

- `ApproachGoal`
- `AvoidGoal`
- `MaintainGoal`
- `MaximizeGoal`
- `MinimizeGoal`
- `CoordinatedGoal` (composition wrapper, with `GoalCoordinationStrategy`)
- `Goal` (abstract base; subclass it only for a brand-new goal type)

Use goals when you want strong default reward scaffolding and only need to customize the surrounding teacher interface methods.

`AgentCoach` (`amesa_core.orchestration.agent.agent_coach`) is not a goal: it is the coordinator of an `AgentCoordinatedSet` / `AgentCoordinatedPopulation`. See [`coordinated-goal.md`](./coordinated-goal.md).

## No-code alternative: guidance

Simple goals can be expressed without code as **guidance** clauses (MCP `guidance_create` + `guidance_publish_to_agent`, or `amesa guidance new` / `amesa guidance publish`). The platform turns clauses into the same goal classes (`goals/utils.py:from_json`). On a teacher (not a controller), reward clauses (Minimize/Maximize/Maintain/Approach/Avoid) replace `compute_reward`, Succeed replaces `compute_success_criteria`, and Terminate replaces `compute_termination`; hooks without guidance keep using code (`orchestration/agent/guidance_overrides.py`).
