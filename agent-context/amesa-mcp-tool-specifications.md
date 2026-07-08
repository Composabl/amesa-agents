# AMESA MCP Tool Specifications

## MCP Server Tools

### Navigation Tools (Discovery Flow)

| Tool | Input | Output |
|------|-------|--------|
| `org_list` | None | Array of organization names (strings) |
| `org_get` | `name` (string) | `{ uuid: string, name: string }` |
| `project_list` | `organizationId` (UUID) | Array of project names (strings) |
| `project_get` | `organizationId` (UUID), `name` (string) | `{ id: UUID, name: string }` |

---

### Agent Tools (Teacher & Controller variants)

| Tool | Input | Output |
|------|-------|--------|
| `agent_teacher_list` / `agent_controller_list` | `projectId` (UUID) | Array of `{ id, name, description, project_id, created_at, latest_version }` |
| `agent_teacher_publish_metadata` / `agent_controller_publish_metadata` | `projectId`, `folderPath`, `name`, `description?`, `version` | `{ agent: {...}, version, folderPath, next_step }` |
| `agent_teacher_publish_code` / `agent_controller_publish_code` | `projectId`, `agentId`, `folderPath` | `{ agent, implementation, uploadUrl, instructions }` |
| `agent_teacher_confirm_upload` / `agent_controller_confirm_upload` | `projectId`, `implementationId` | `{ status: 'confirmed', implementationId, dataUrl }` |

---

### Perceptor Tools

| Tool | Input | Output |
|------|-------|--------|
| `perceptor_list` | `projectId` (UUID) | Array of `{ id, name, description, project_id, created_at, latest_version }` |
| `perceptor_publish_metadata` | `projectId`, `folderPath`, `name`, `description?`, `version` | `{ perceptor, version, folderPath, next_step }` |
| `perceptor_publish_code` | `projectId`, `perceptorId`, `folderPath`, `sensors` (string[]) | `{ perceptor, implementation, uploadUrl, instructions }` |
| `perceptor_confirm_upload` | `projectId`, `implementationId` | `{ status: 'confirmed', implementationId, dataUrl }` |

---

### Orchestrator Tools (Teacher & Controller variants)

| Tool | Input | Output |
|------|-------|--------|
| `orchestrator_teacher_list` / `orchestrator_controller_list` | `projectId` (UUID) | Array of `{ id, name, description, project_id, created_at, latest_version }` |
| `orchestrator_teacher_publish_metadata` / `orchestrator_controller_publish_metadata` | `projectId`, `folderPath`, `name`, `description?`, `version` | `{ orchestrator, version, folderPath, next_step }` |
| `orchestrator_teacher_publish_code` / `orchestrator_controller_publish_code` | `projectId`, `orchestratorId`, `folderPath` | `{ orchestrator, implementation, uploadUrl, instructions }` |
| `orchestrator_teacher_confirm_upload` / `orchestrator_controller_confirm_upload` | `projectId`, `implementationId` | `{ status: 'confirmed', implementationId, dataUrl }` |

---

### Orchestration Tools (Training)

| Tool | Input | Output |
|------|-------|--------|
| `list_formations` | `projectId` (UUID) | Array of `{ id, name, description, project_id, created_at, updated_at }` |
| `start_training` | `projectId`, `orchestrationId`, `trainingCycles`, `numEpisodesPerScenario?`, `numStepsPerEpisode?`, `numWorkers?` | `{ id: jobId, status: 'startRequested' }` |
| `list_training_jobs` | `orchestrationId`, `limit?`, `status?` | Array of `{ id, status, plan, max_iterations, created_at, updated_at }` |
| `get_orchestration_metrics` | `orchestrationId`, `limit?`, `jobId?` | `{ orchestration_id, job_id, metrics: [...] }` |
| `get_historian_artifact_download_url` | `jobId` (UUID) | `{ job_id, type, download_url, file_url, instruction }` |
| `get_benchmark_artifact_download_url` | `jobId` (UUID) | `{ job_id, type, download_url, file_url, instruction }` |

---

### Simulator Tools

| Tool | Input | Output |
|------|-------|--------|
| `read_sim_sensors` | `projectId` (UUID) | `{ simulator_id, implementation_id, sensor_space, sensor_mappings, ranges }` |
| `read_sim_actions` | `projectId` (UUID) | `{ simulator_id, implementation_id, action_space, action_mappings }` |

---

### Documentation Tools

| Tool | Input | Output |
|------|-------|--------|
| `list_docs` | None | JSON string (manifest contents) |
| `fetch_doc` | `path` (string) | Markdown text content |