# Perceptor Publishing

Portable perceptor package example (matches `amesa_cli/template/perceptor/pyproject.toml`):

```toml
[project]
name = "my-perceptor"
version = "0.1.0"
description = "What the perceptor computes"
dependencies = ["amesa-core"]

[amesa]
type = "perceptor"
entrypoint = "my_module.perceptor:MyPerceptor"
variables = ["derived_key1", "derived_key2"]   # outputs
inputs = ["sensor_a", "sensor_b"]              # optional: sensors compute() reads
```

## Requirements

- Use top-level `[amesa]` (not `[tool.amesa]`). The loader reads `[amesa]`, falling back to legacy `[composabl]` (`amesa_core/utils/plugin_util.py`, `_resolve_plugin_section`).
- `[project]` must have `name` and `version`; `[amesa]` must have `type` and `entrypoint` (`plugin_util.parse_plugin_toml`).
- `type` must be `"perceptor"` (`validate_util.PLUGIN_TYPES_BY_KIND["perceptor"]`).
- `entrypoint` must be `"module.path:ClassName"`, relative to the folder holding `pyproject.toml` (`plugin_util.load_cls_from_path`).
- `variables` is not checked by the SDK, but the MCP publish tools take the perceptor's `sensors` exclusively from `[amesa].variables`, and `perceptor_confirm_upload` reads outputs from `[amesa].outputs` (or `variables`) and inputs from `[amesa].inputs`. Keep `variables` equal to the keys `compute()` returns.
- `inputs` is checked by `amesa data perceive` against the dataset's sensor names before the rollout (`amesa_cli/dataset/perceive.py`, `declared_inputs`).

## CLI

```bash
amesa perceptor new --name my-perceptor --description "..." --location ./   # scaffold
amesa perceptor validate ./my-perceptor/          # structure, deps, entrypoint, abstract methods
amesa perceptor publish ./my-perceptor/           # or --path/-p; prompts for the project
amesa perceptor list
amesa perceptor delete                            # interactive
amesa data perceive <dataset> --use-case <uc> --perceptor <name> [--version N|latest] [--name out]
```

`publish` reuses an existing perceptor with the same `[project].name` and uploads the package as a new version (`amesa_cli/main/perceptor.py`).

## MCP tools

1. Navigate: `organization_list` → `use_case_list` (the use case id is the `projectId`).
2. Optionally `get_artifact_scaffold` (`artifactType: "perceptor"`) for the runtime contract.
3. First version: `perceptor_create` (`projectId`, `name`, `description`, `sensors` = `[amesa].variables`) → returns `implementationId` and a presigned `uploadUrl`. Later versions: `perceptor_implementation_publish` (`projectId`, `perceptorId`, `sensors`).
4. PUT the `.tar.gz` to `uploadUrl` with the returned headers, then `perceptor_confirm_upload` (`projectId`, `implementationId`, optional `perceptorSummary`).
   - Alternative to steps 3–4 for an existing perceptor: `submit_code_file` (`artifactType: "perceptor"`, `artifactId`, `files`, `perceptorSensors`) packages the files into a new version.
5. Validate: `amesa_perceptor_validate` (`organizationId`, `projectId`, `perceptorId`, optional `version`) → poll the returned jobId with `component_validation_status`.
6. Inspect/edit: `perceptor_list`, `perceptor_get`, `perceptor_update`.
7. Try it on data: `amesa_data_perceive` (`organizationId`, `datasetUuid`, `perceptorImplementationId`, `name` for the new dataset; optional `simulatorId`, `inputs`) writes the outputs as `p_<output>` columns of a new staged dataset.
