# Goals Quirks

- Boundary checks (`is_in_boundary`) require both `boundary_left` and `boundary_right`; with either missing they return `False`, so `ApproachGoal` can never succeed and the Approach/Maintain bonus / Avoid penalty never applies (`goals/goal.py`).
- `ApproachGoal` success is "in boundary", not "within `tolerance`" — `tolerance` is effectively unused by the concrete goals (`goals/approach_goal.py`).
- `stop_steps` and `stop_value` do nothing on the concrete goals: every one overrides `compute_termination` (Approach/Maintain/Maximize/Minimize return `False`; Avoid checks the boundary only).
- `MaintainGoal`, `MaximizeGoal`, and `MinimizeGoal` never succeed and never terminate.
- `AvoidGoal` never succeeds; its boundary is the region to avoid. It terminates only with `should_terminate_in_boundary=True` (constructor default `False`, but `from_json` defaults to `True`).
- `AvoidGoal.is_compute_done` (and the `AgentTeacher` default) is success **AND** termination, so it is always `False` for Avoid; `AgentCoach.is_compute_done` is success **OR** termination.
- `MaximizeGoal`/`MinimizeGoal` rewards are a squashed transform (about 0.9–1.1 near zero), not the raw sensor value.
- In `CoordinatedGoal`, mismatched `weights` length raises `ValueError`; `OR` ignores weights and clips negative rewards to 0; `THEN` rewards the first goal that is currently *succeeding* and returns 0 if none is (`goals/coordinated_goal.py`).
- `CoordinatedGoal` success/termination only look at direct `ApproachGoal` / `AvoidGoal` children; with no `ApproachGoal`, the episode can never succeed.
- Goal chaining (`THEN`) with non-succeeding goals (Maintain/Maximize/Minimize) only logs a warning and stalls staged progress.
- The entrypoint class is instantiated with no arguments — configure goals inside a zero-arg `__init__` (`orchestration/agent/agent.py:get_impl_cls_instance`).
- `AgentCoach.compute_reward` must return a scalar; the trainer adds it to every child agent's reward (`amesa_train/agent_processors/agent_coordinated_set_processor.py`).
- The no-code `AgentTeacherJson.compute_success_criteria` always returns `False` (`orchestration/agent/agent_teacher_json.py`), so pure-JSON goals never report success; Succeed guidance on a code teacher goes through `guidance_overrides.py` instead.
