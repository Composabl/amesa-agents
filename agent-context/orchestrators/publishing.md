# Orchestrator Publishing

Package example (matches the CLI scaffolds `amesa_cli/amesa_cli/template/orchestrator_controller/pyproject.toml`
and `orchestrator_teacher/pyproject.toml`):

```toml
[project]
name = "my-orchestrator"
version = "0.1.0"
description = "Picks a child skill by rule"
dependencies = ["amesa-core"]

[amesa]
type = "orchestrator-controller"   # or "orchestrator-teacher"
entrypoint = "my_orchestrator.controller:MyOrchestrator"
```

```text
my-orchestrator/
├── pyproject.toml
└── my_orchestrator/
    ├── __init__.py
    └── controller.py      # or teacher.py
```

## Requirements

Checked by `plugin_util.parse_plugin_toml` / `get_type` (`amesa_core/amesa_core/utils/plugin_util.py`)
and `validate_util.validate_plugin`:

- `[project]` must have `name` and `version` (`description` is used as the orchestrator description).
- `[amesa]` must have `type` and `entrypoint`. Use top-level `[amesa]` (not `[tool.amesa]`);
  only `[amesa]` and the legacy `[composabl]` are read.
- `type` must be `"orchestrator-teacher"` or `"orchestrator-controller"`. Legacy
  `"selector-teacher"` / `"selector-controller"` are normalized to these
  (`utils/legacy_import_rewrite.py`, `_LEGACY_PLUGIN_TYPE_ALIASES`). A bare `"selector"` is not
  a valid type. `"agent-teacher"` / `"agent-controller"` are rejected by `amesa orchestrator validate`.
- `entrypoint` is `"module.path:ClassName"` and `module/path.py` must exist relative to the folder
  holding `pyproject.toml` (the first segment is the snake_case package, not the kebab-case folder).
- The class must subclass `AgentTeacher` (teacher) or `AgentController` (controller), implement
  every abstract method as `async`, and be constructible with no arguments.

## Validate

```bash
amesa orchestrator validate ./my-orchestrator
```

`validate` takes only the positional `PATH` (default `./`) — no `--static`, `--organization`,
`--project` or `--max-steps` flags (`amesa_cli/amesa_cli/cli/cli_orchestrator.py`, `validate`).
It is **static only**: pyproject, dependency install, entrypoint import, base class, async
abstract methods, and (teacher) `compute_scenario_advancement` thresholds. It does not run the
orchestrator against a mock sim (no `mock_sim` is passed; `validate_util.MOCK_SIM_TYPES` lists
agent types only).

## Publish with the CLI

```bash
amesa login
amesa orchestrator new --name my-orchestrator --type controller --description "..." --location ./   # scaffold; --type controller|teacher
amesa orchestrator publish ./my-orchestrator          # or: amesa orchestrator publish --path ./my-orchestrator  (-p = path)
amesa orchestrator list
amesa orchestrator delete                              # interactive selection
```

`publish` prompts for the project, reuses the orchestrator whose name equals `[project].name`
(otherwise creates it), and uploads the package as a new version with type `controller` or
`teacher` (the `orchestrator-` prefix is stripped) (`amesa_cli/amesa_cli/main/orchestrator.py`, `publish`).
You do not need to bump `version` to publish a new version.

## Publish with the AMESA MCP tools

1. `organization_list` → `use_case_list` to get `organizationId` / `projectId`.
2. Optional: `get_artifact_scaffold` with `artifactType: "orchestrator"`, `orchestratorType: "teacher" | "controller"`.
3. New orchestrator: `orchestrator_create` (`projectId`, `name`, `type: "teacher" | "controller"`;
   optional `requestId`, `description`, `realizes`) → creates the orchestrator and its first
   version and returns a short-lived upload URL. New version of an existing one:
   `orchestrator_implementation_publish` (`projectId`, `orchestratorId`; optional `requestId`,
   `expectedVersion`, `type`).
4. Upload the `.tar.gz` of the package to the returned URL, then `orchestrator_confirm_upload`
   (`projectId`, `implementationId`; optional `capabilitySummaries`).
   - Alternative to 3–4 for an existing orchestrator: `submit_code_file` with `projectId`,
     `artifactType: "orchestrator"`, `artifactId` (the orchestrator id), `files`, and optional
     `orchestratorType`, `entrypoint`, `dependencies`.
5. `amesa_orchestrator_validate` (`organizationId`, `projectId`, `orchestratorId`; optional
   `clusterId`, `version`) → poll the returned job with `component_validation_status`
   (`organizationId`, `jobId`).
6. Inspect with `orchestrator_list` (`projectId`) / `orchestrator_get` (`projectId`,
   `orchestratorId`); read published code with `component_source_get`
   (`componentType: "orchestrator"`); rename/describe with `orchestrator_update`. Record the
   orchestrator and implementation IDs.

Pass a stable `requestId` to create/publish so retries do not create duplicate versions.

## Wire it into an orchestration

- `orchestration_workflow_deploy` (`projectId`, `orchestrationId`, `orchestrators`; optional
  `requestId`, `perceptors`, `communicationAgents`) replaces the whole workflow. Each
  `orchestrators[]` item: `id` (orchestrator **implementation** UUID, required), `skills`
  (skill implementation UUIDs, or `{id, selectedScenarios}`; their order is the child index),
  `children` (nested orchestrator items), `sequenceType` (`"fixed"` | `"variable"`, default
  `"variable"`), `selectedScenarios`, `coordinated`, `policyAgents`. `orchestration_create`
  accepts the same tree as `graph`.
- Read the current tree (including orchestrator node IDs) with `orchestration_get_workflow`
  before replacing it.
- `orchestration_component` adds/removes one skill, perceptor, policy agent or communication
  agent (`kind` does not include orchestrators); use `orchestratorNodeId` to attach a skill
  under a specific orchestrator node.

Legacy MCP tools `orchestrator_teacher_*` and `orchestrator_controller_*` (`*_publish_metadata`,
`*_publish_code`, `*_confirm_upload`, `*_list`) are deprecated: use `orchestrator_create`,
`orchestrator_implementation_publish`, `orchestrator_confirm_upload`, `orchestrator_list`.
