# AgentController Publishing

Portable controller package example (matches the CLI scaffold `amesa_cli/amesa_cli/template/agent_controller/pyproject.toml`):

```toml
[project]
name = "my-controller"
version = "0.1.0"
description = "My controller"
dependencies = ["amesa-core"]

[amesa]
type = "agent-controller"
entrypoint = "my_module.controller:MyController"
```

## Requirements

Checked by `plugin_util.parse_plugin_toml` / `get_type` (`amesa_core/amesa_core/utils/plugin_util.py`):

- `[project]` must have `name` and `version`.
- `[amesa]` must have `type` and `entrypoint`.
- `type` must be `"agent-controller"`.
- `entrypoint` must be `"module.path:ClassName"`, and `module/path.py` must exist relative to the folder holding `pyproject.toml`.
- Use top-level `[amesa]` (not `[tool.amesa]`). Only `[amesa]` and the legacy `[composabl]` are read.
- The entrypoint class must subclass `AgentController` and implement every abstract method as `async` (`validate_util.validate_abstract_class_implementation`).

## Validate

```bash
amesa agent validate ./my-controller            # static checks + run against a mock of the project's sim (default)
amesa agent validate ./my-controller --static   # files/code only, no platform login needed
```

Runtime flags: `--organization/-o`, `--project/-p`, `--max-steps` (default 50), `--log-file` (`amesa_cli/amesa_cli/cli/cli_agent.py`, `validate`). Older CLI releases run static by default and use `--runtime` instead.

## Publish with the CLI

```bash
amesa login
amesa agent publish ./my-controller     # or: amesa agent publish --path ./my-controller
```

The CLI prompts for the project, reuses the agent with the same `[project].name` if one exists (otherwise creates it), and uploads the code as a new version of type `controller`.

## Publish with the AMESA MCP tools

1. `organization_list` → `use_case_list` to get the `organizationId` / `projectId`.
2. Optional: `get_artifact_scaffold` with `artifactType: "skill"`, `skillType: "controller"` for the runtime contract.
3. New controller: `operational_agent_create` with `projectId`, `name`, `description`, `type: "controller"`, `requestId` → creates the agent and its first implementation and returns a short-lived upload URL. New version of an existing controller: `operational_agent_implementation_publish` with `projectId`, `optimizationAgentId`, `type: "controller"`, `requestId`.
4. Upload the `.tar.gz` of the package to the returned URL, then call `operational_agent_confirm_upload` with `projectId` and `implementationId`.
   - Alternative to steps 3–4 for an existing agent: `submit_code_file` with `artifactType: "skill"`, `skillType: "controller"`, `artifactId`, `entrypoint`, and the files.
5. `amesa_agent_validate` (`organizationId`, `projectId`, `agentId`) → poll the returned job with `component_validation_status`.
6. Check with `operational_agent_list` (`type: "controller"`) / `operational_agent_get`; record the agent and implementation IDs.

Controllers do **not** accept guidance — do not call the `guidance_*` tools for them.
