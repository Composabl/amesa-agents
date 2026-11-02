# AgentTeacher Publishing

To publish a teacher as a portable component, package it with a `pyproject.toml`:

```toml
[project]
name = "my-teacher"
version = "0.1.0"
dependencies = ["amesa-core"]

[amesa]
type = "agent-teacher"
entrypoint = "my_module.teacher:MyTeacher"
```

## Requirements

Checked by `amesa_core/utils/plugin_util.py` (`parse_plugin_toml`, `get_type`, `load_cls_from_path`):

- `[project]` must have `name` and `version` (`description` is optional, used as the agent description).
- `type` must be `"agent-teacher"`.
- `entrypoint` must be `"module.path:ClassName"`, and `module/path.py` must exist relative to the folder root.
- Use top-level `[amesa]` (not `[tool.amesa]`). The legacy `[composabl]` section is still read as a fallback.
- The entrypoint class must subclass `AgentTeacher` and implement its abstract methods as `async`
  (`amesa_core/utils/validate_util.py`, `validate_plugin`).
- The class must be constructible with no arguments (`impl_cls()`); the trainer re-creates it on
  episode resets.

## CLI (`amesa_cli/cli/cli_agent.py`)

```bash
amesa login
amesa agent new --name my-teacher --type teacher --description "..." --location ./   # scaffold
amesa agent validate ./my-teacher            # static checks + run against a mock of the project's sim
amesa agent validate ./my-teacher --static   # files/code only, no project needed
amesa agent publish ./my-teacher             # prompts for the project
amesa agent list | delete | retrieve
```

`publish` reuses the agent whose name equals `[project].name` in the selected project and uploads a
new version; it creates the agent only when none exists (`amesa_cli/main/agent.py`, `publish`).
`amesa agent new --normalize -o <org> -p <project>` scaffolds a teacher that normalizes sensors to
[-1, 1] from the sim's bounds.

## MCP tools

1. Navigate: `organization_list` → `use_case_list` (the use case id is the `projectId`).
2. Contract/scaffold: `get_artifact_scaffold` (`artifactType: "skill"`, `skillType: "teacher"`).
3. Publish, either:
   - **Upload a package:** `operational_agent_create` (`type: "teacher"`; creates the agent + first
     version and returns a short-lived upload URL) → upload the `.tar.gz` → `operational_agent_confirm_upload`.
     For later versions use `operational_agent_implementation_publish` instead of create.
   - **Submit files:** `submit_code_file` (`artifactType: "skill"`, `skillType: "teacher"`,
     `entrypoint`, `files`) packages the files as a new version of an existing agent.
4. Validate on compute: `amesa_agent_validate` → poll `component_validation_status` with the returned jobId.
5. Inspect: `operational_agent_list` / `operational_agent_get` / `operational_agent_retrieve`;
   edit metadata with `operational_agent_update`.
6. Add UI guidance to a code teacher: `guidance_publish_to_agent` (creates a new version).

Always pass a stable `requestId` to create/publish so retries do not create duplicate versions.
For a teacher with no code, `operational_agent_create_template` (`projectId`; optional `requestId`,
`name`, `realizes`) creates a blank guidance-driven teacher as its first version, with no upload or
validation; give it goals with the guidance tools. Legacy tools (`agent_teacher_publish_metadata`,
`agent_teacher_publish_code`, `agent_teacher_confirm_upload`, `agent_teacher_list`, `project_get`,
`org_get`) are deprecated.
