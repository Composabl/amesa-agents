# Goals Publishing

Goals are **not** published as a standalone component type.

Publish them through a teacher package. The config table is top-level `[amesa]` (legacy `[composabl]` is still read), **not** `[tool.amesa]`; `[project]` needs `name` and `version`, `[amesa]` needs `type` and `entrypoint` (`amesa_core/utils/plugin_util.py:parse_plugin_toml`):

```toml
[project]
name = "my-goal-teacher"
version = "0.1.0"
dependencies = ["amesa-core"]

[amesa]
type = "agent-teacher"
entrypoint = "my_module.goal_teacher:MyGoalBasedTeacher"
```

If your class subclasses `Goal`/`CoordinatedGoal`, it is still published as `agent-teacher`. The entrypoint class must be constructible with no arguments.

An `AgentCoach` is published with `type = "agent-coach"`. The types `agent-coordinated-set` and `agent-coordinated-population` (what `amesa agent new` scaffolds for coordinated agents) pass `amesa agent validate` but `amesa agent publish` refuses them ("not supported yet", `amesa_cli/main/agent.py:UNSUPPORTED_PUBLISH_TYPES`).

## CLI

```bash
amesa login
amesa agent validate ./my-goal-teacher        # add --static to skip the mock-sim run (coaches never get one)
amesa agent publish ./my-goal-teacher          # prompts for the project; reuses an agent of the same name as a new version
```

## MCP tools

1. Navigate: `organization_list` → `use_case_list` (the use case is the `projectId`).
2. Optionally `get_artifact_scaffold` (`artifactType: "skill"`, `skillType: "teacher"` or `"coach"`) for the runtime contract.
3. First version: `operational_agent_create` (`type: "teacher"` or `"coach"`) creates the agent plus its first implementation and returns an upload URL. Later versions: `operational_agent_implementation_publish`. Upload the `.tar.gz`, then call `operational_agent_confirm_upload`.
   Alternatively `submit_code_file` (`artifactType: "skill"`, `skillType`, `entrypoint`, `files`) packages the files into a new version for you.
4. Validate: `amesa_agent_validate`, then poll `component_validation_status` with the returned job id.

The legacy tools (`agent_teacher_publish_metadata` / `_publish_code` / `_confirm_upload`, `project_get`, `org_get`, ...) are outdated.

## No-code goals (guidance)

A goal can also be published without code: `guidance_create` + `guidance_publish_to_agent` (CLI: `amesa guidance new`, `amesa guidance publish`). Teachers only (controllers are refused). On a teacher with uploaded code, reward clauses (Minimize/Maximize/Maintain/Approach/Avoid) replace `compute_reward`, Succeed replaces `compute_success_criteria`, Terminate replaces `compute_termination`; hooks without guidance keep the code (`amesa_core/orchestration/agent/guidance_overrides.py`).
