# AMESA MCP Tool Specifications

Every tool of the AMESA MCP server, grouped by the lifecycle stage it belongs to, with its input parameters. Use it to pick the right tool and to call it with the right arguments.

- **Inputs** come from each tool's input schema in the server catalog. Required inputs are listed first; optional inputs end in `?`. Types: `uuid` is a UUID string; `object` and `array` arguments have nested structure that the server's schema defines.
- **Before calling a tool you haven't used, read its full schema.** `mcp_tools_search` returns each match's description and complete input schema, including nested objects and field descriptions. This file doesn't copy those.
- **Outputs** are not listed: tool results are JSON documents described in each tool's description.
- The [README](../README.md) walks the stages in order and lists every tool with a one-line purpose.
- Tool availability depends on your organization's permissions, and the catalog can differ between the production and staging servers.

## Calling conventions

- **Find IDs first.** Most tools take an `organizationId` and/or `projectId` (a use case). Get them from `organization_list` and `use_case_list`.
- **Simulator jobs** (`amesa_data_*`, `amesa_sim_*`, `amesa_cluster_*`): a response without `next` already holds the finished job's result. A response with `next` is still running: poll each job ID in it with `simulator_job_status`, never with the training tools.
- **Validation jobs** (`amesa_*_validate`): poll the returned job ID with `component_validation_status`.
- **Training jobs**: `training_job_submit` returns a job ID; follow it with `training_session_get` and `training_job_logs_get`.
- **Publishing code**: `*_create` and `*_implementation_publish` return a short-lived upload URL. Upload the packaged `.tar.gz` there, then call the matching `*_confirm_upload`. `submit_code_file` publishes files as a new version in one call.
- **Datasets** must be staged on a connected compute node with `amesa data stage` before any data, simulator or clustering tool can use them.

## Getting started

Walkthrough: [Before you begin](../README.md#before-you-begin)

| Tool | Required inputs | Optional inputs | Purpose |
| --- | --- | --- | --- |
| `mcp_tools_search` | `query` string | `topK?` integer | Search the tool catalog by intent; returns names, descriptions and arguments. |
| `mcp_tools_read` | `calls` array of object |  | Run up to eight read-only tools in one round trip. |
| `mcp_tools_call` | `name` string<br>`arguments` object |  | Call a tool found through the catalog. |
| `platform_methodology_search` | none | `query?` string<br>`topic?` string<br>`topK?` integer | Search AMESA's platform and SDK documentation. |
| `platform_methodology_fetch` | `path` string |  | Read one methodology document in full. |
| `cluster_list` | none | `projectId?` uuid<br>`organizationId?` uuid | List your organization's compute clusters and whether each is connected. |
| `cluster_health_get` | `clusterId` uuid | `windowMinutes?` integer | Check whether a cluster is online and healthy. |
| `cluster_create_local` | none | `organizationId?` uuid<br>`projectId?` uuid<br>`name?` string | Issue a single-use code to enroll a local machine (same as compute_enrollment_issue). |
| `compute_enrollment_issue` | none | `organizationId?` uuid<br>`projectId?` uuid<br>`name?` string | Issue a single-use code that enrolls a new local compute node. |

## Set up

Walkthrough: [1. Set up the use case](../README.md#1-set-up-the-use-case)

| Tool | Required inputs | Optional inputs | Purpose |
| --- | --- | --- | --- |
| `organization_list` | none |  | List the organizations you belong to. |
| `organization_get` | `name` string |  | Find an organization's ID by its exact name. |
| `use_case_list` | `organizationId` uuid |  | List use cases (projects). |
| `use_case_get` | `projectId` uuid |  | Read a use case in full. |
| `use_case_brief_get` | `projectId` uuid |  | Read a short overview of a use case. |
| `use_case_update` | `projectId` uuid | `name?` string<br>`description?` string<br>`simulatorId?` uuid \| null<br>`teamId?` uuid \| null<br>`icon?` string<br>`iconColor?` string | Change a use case's name, description or settings. |
| `kpi_settings_get` | `projectId` uuid |  | Read the KPI and ROI settings training is measured against. |
| `kpi_settings_update` | `projectId` uuid<br>`kpiSettings` object |  | Set the KPI and ROI settings (replaces them as a whole). |
| `use_case_journey_get` | `projectId` uuid |  | See which lifecycle stage the use case is in. |
| `use_case_journey_advance` | `projectId` uuid<br>`stage` `setup` \| `data` \| `knowledge` \| `training` \| `complete` | `threadId?` uuid<br>`fromAssistantId?` string<br>`note?` string | Record that the use case moved to a new stage. |
| `assistant_handoff` | `toAssistantId` `data-engineer` \| `knowledge-engineer` \| `analyst` \| `communication-agent` \| `implementation-engineer` \| `amesa-brain` \| `amesa-monitor` \| `custom`<br>`summary` string | `threadId?` uuid<br>`fromAssistantId?` string<br>`stage?` `setup` \| `data` \| `knowledge` \| `training` \| `complete` | Hand the conversation to the assistant that leads another stage. |

## Data

Walkthrough: [2. Prepare the data](../README.md#2-prepare-the-data)

| Tool | Required inputs | Optional inputs | Purpose |
| --- | --- | --- | --- |
| `dataset_list` | `clusterId` uuid<br>`organizationId` uuid |  | List staged datasets with their columns and roles. |
| `amesa_data_stats` | `organizationId` uuid<br>`datasetUuid` uuid | `simulatorId?` uuid<br>`metrics?` array of string | Describe each column of a dataset. |
| `amesa_data_integrity` | `organizationId` uuid<br>`datasetUuid` uuid | `simulatorId?` uuid | Score empty, infinite, non-numeric, outlier and flat values. |
| `amesa_data_score` | `organizationId` uuid<br>`datasetUuid` uuid | `simulatorId?` uuid | Score how strongly the sensors respond to the actions. |
| `amesa_data_assign` | `organizationId` uuid<br>`datasetUuid` uuid | `simulatorId?` uuid<br>`roles?` object<br>`datetimeColumn?` string \| null<br>`apply?` boolean | Set columns as sensor, replica, action or ignored. |
| `amesa_data_suggest` | `organizationId` uuid<br>`datasetUuid` uuid | `simulatorId?` uuid<br>`action?` `suggest` \| `score` \| `apply`<br>`sensorVariables?` array of string<br>`actionVariables?` array of string<br>`name?` string | Rank columns by how much they respond and propose a focused set. |
| `amesa_data_prune` | `organizationId` uuid<br>`datasetUuid` uuid | `simulatorId?` uuid<br>`level?` `episode` \| `step`<br>`window?` integer<br>`threshold?` number<br>`keep?` number<br>`columns?` array of string<br>`score?` boolean<br>`apply?` boolean<br>`name?` string | Drop outlier values into a new copy of the dataset. |
| `amesa_data_split` | `organizationId` uuid<br>`datasetUuid` uuid | `simulatorId?` uuid<br>`action?` `list` \| `add` \| `remove` \| `apply`<br>`rules?` array of string<br>`numbers?` array of integer<br>`name?` string | Mark episode boundaries with rules and write the split dataset. |
| `amesa_data_perceive` | `organizationId` uuid<br>`datasetUuid` uuid<br>`perceptorImplementationId` uuid<br>`name` string | `simulatorId?` uuid<br>`inputs?` object | Run a perceptor over a dataset and write its outputs as new columns. |
| `amesa_data_kpi` | `organizationId` uuid<br>`datasetUuid` uuid<br>`kpiVariable` string | `simulatorId?` uuid<br>`lens?` `mean` \| `minimum` \| `maximum` | Derive a KPI benchmark from a data column and recommend the KPI. |

## Simulator

Walkthrough: [3. Fit a simulator](../README.md#3-fit-a-simulator)

| Tool | Required inputs | Optional inputs | Purpose |
| --- | --- | --- | --- |
| `amesa_sim_train` | `organizationId` uuid<br>`datasetUuid` uuid | `simulatorId?` uuid<br>`name?` string<br>`gpu?` boolean<br>`allowDuplicate?` boolean | Train a data-driven simulator from a dataset. |
| `amesa_sim_analyze` | `organizationId` uuid<br>`simulatorId` uuid<br>`datasetUuid` uuid | `episodes?` string \| array of integer<br>`compute?` `missing` \| `none` | Roll a trained simulator out over its dataset's episodes; the platform scores it. |
| `amesa_sim_validate` | `organizationId` uuid<br>`simulatorId` uuid | `clusterId?` uuid<br>`version?` number<br>`steps?` integer<br>`envInit?` object<br>`callTimeoutS?` integer | Validate a code simulator you published (not a data-driven one). |
| `simulator_list` | `organizationId` uuid |  | List simulators and their latest builds. |
| `simulator_retrieve` | `organizationId` uuid<br>`simulatorId` uuid | `versionId?` uuid | Get a simulator build's image reference and whether it is ready. |
| `simulator_score_get` | `organizationId` uuid<br>`simulatorId` uuid |  | Read a simulator's score. |
| `simulator_validation_get` | `projectId` uuid<br>`validationRunId` uuid |  | Read one simulator validation run. |
| `simulator_variable_fidelity_get` | `projectId` uuid<br>`validationRunId` uuid<br>`sensorMappingId` uuid | `includeSeries?` boolean | Read one variable's result from a validation run. |
| `simulator_relationship_get` | `projectId` uuid<br>`validationRunId` uuid<br>`actionMappingId` uuid<br>`sensorMappingId` uuid | `includeChart?` boolean | Read how one action relates to one sensor in a validation run (not causal). |
| `simulator_job_list` | `organizationId` uuid | `operation?` string<br>`status?` string<br>`datasetUuid?` uuid | List simulator, data and clustering jobs. |
| `simulator_job_status` | `jobId` uuid |  | Poll a running simulator job. |
| `sim_publish_metadata` | `organizationId` uuid<br>`folderPath` string<br>`name` string<br>`version` string | `projectId?` uuid<br>`description?` string | Register your own simulator. |
| `sim_publish_code` | `organizationId` uuid<br>`simulatorId` uuid<br>`folderPath` string |  | Get the upload URL for your simulator's code. |
| `sim_confirm_upload` | `organizationId` uuid<br>`implementationId` uuid |  | Confirm a simulator code upload and start its build. |
| `mapping_list` | `implementationId` uuid | `type?` `all` \| `sensor` \| `action`<br>`name?` string | List a simulator build's sensor and action mappings. |
| `mapping_update` | `implementationId` uuid<br>`updates` array of object |  | Rename variables (only the mapped name can change). |
| `mapping_dependents_list` | `implementationId` uuid<br>`name` string<br>`kind` `sensor` \| `action` |  | See what still uses a variable's name. |
| `amesa_cluster_create` | `organizationId` uuid<br>`datasetUuid` uuid | `simulatorId?` uuid<br>`useCase?` string<br>`lens?` `temporal` \| `aggregate` \| `categorical`<br>`categoricalVariable?` string<br>`nClusters?` integer | Find operating regimes in a dataset. |
| `amesa_cluster_convert` | `organizationId` uuid<br>`clusteringJobId` uuid |  | Turn found regimes into scenario definitions. |
| `amesa_cluster_sims` | `organizationId` uuid<br>`clusteringJobId` uuid | `name?` string<br>`gpu?` boolean<br>`allowDuplicate?` boolean | Train one simulator per regime. |
| `activity_cluster_get` | `simulatorId` uuid |  | Read the regimes of a variant simulator. |
| `activity_cluster_upload` | *not in the server catalog* | | Store clustering results as variant simulators and scenarios. |
| `use_case_simulator_assign` | `organizationId` uuid<br>`projectId` uuid<br>`simulatorIds` array of uuid |  | Attach a simulator to the use case. |
| `use_case_sensors_get` | `projectId` uuid |  | List the use case's sensors and actions. |

## Knowledge

Walkthrough: [4. Capture domain knowledge](../README.md#4-capture-domain-knowledge)

| Tool | Required inputs | Optional inputs | Purpose |
| --- | --- | --- | --- |
| `use_case_document_upload` | `projectId` uuid<br>`files` array of object |  | Upload a reference document. |
| `use_case_document_ingest` | `projectId` uuid<br>`documentIds` array of uuid |  | Read a document into the knowledge base. |
| `use_case_document_list` | `projectId` uuid |  | List the use case's documents. |
| `use_case_document_delete` | `projectId` uuid<br>`documentId` uuid |  | Remove a document. |
| `use_case_search` | `projectId` uuid<br>`query` string | `sources?` array of string<br>`limit?` integer<br>`since?` string<br>`assistant?` string<br>`includeSuperseded?` boolean | Search the use case's documents, knowledge and past conversations, with citations. |
| `use_case_graph_get` | `projectId` uuid | `entity?` string<br>`depth?` integer<br>`types?` array of string \| string<br>`status?` array of string<br>`changedSince?` integer | Read the domain graph, an entity's neighborhood, or its gaps. |
| `use_case_graph_query` | `projectId` uuid<br>`query` object \| object \| object | `question?` string | Ask targeted questions of the domain graph. |
| `use_case_graph_edit` | `projectId` uuid<br>`operations` array of object \| object \| object \| object \| object \| object \| object \| object \| object \| object \| object | `dryRun?` boolean<br>`requestId?` string<br>`source?` object \| object \| object \| object \| object \| object | Add, link, merge or correct entities and facts. |
| `use_case_graph_review` | `projectId` uuid | `items?` array of uuid<br>`decision?` `confirm` \| `retract`<br>`note?` string<br>`decisions?` array of object<br>`requestId?` string | Confirm or retract proposed items and settle contradictions. |

## Design

Walkthrough: [5. Design the agent system](../README.md#5-design-the-agent-system)

| Tool | Required inputs | Optional inputs | Purpose |
| --- | --- | --- | --- |
| `decomposition_create` | `projectId` uuid<br>`name` string | `goal?` string<br>`nodes?` array of object<br>`reason?` string | Draft the tree of orchestrators and skills. |
| `decomposition_edit` | `projectId` uuid<br>`decompositionId` uuid<br>`reason` string | `expectedRevision?` integer<br>`operations?` array of object \| object \| object \| object \| object<br>`name?` string<br>`goal?` string \| null | Refine a draft decomposition. |
| `decomposition_get` | `projectId` uuid | `decompositionId?` uuid<br>`revision?` integer<br>`includeHistory?` boolean | Read a decomposition and its warnings. |
| `decomposition_promote` | `projectId` uuid<br>`decompositionId` uuid<br>`requestId` uuid | `revision?` integer<br>`orchestrationName?` string | Create real components and an orchestration from an approved draft. |
| `orchestration_pattern_create` | `projectId` uuid<br>`name` string<br>`type` `skillGroup` \| `orchestratorSkills` \| `strategySet` \| `coordinatedSet`<br>`skills` array of object | `requestId?` uuid<br>`description?` string<br>`orchestratorImplementationId?` uuid<br>`populationAgentImplementationId?` uuid<br>`policyAgents?` array of object<br>`committed?` boolean | Save a reusable orchestration shape. |
| `orchestration_pattern_list` | `projectId` uuid | `committedOnly?` boolean<br>`limit?` integer<br>`offset?` integer | List saved patterns. |
| `orchestration_pattern_get` | `patternId` uuid<br>`projectId` uuid |  | Read one pattern. |
| `orchestration_pattern_update` | `patternId` uuid<br>`projectId` uuid | `requestId?` uuid<br>`name?` string<br>`description?` string<br>`type?` `skillGroup` \| `orchestratorSkills` \| `strategySet` \| `coordinatedSet`<br>`orchestratorImplementationId?` uuid \| null<br>`populationAgentImplementationId?` uuid \| null<br>`skills?` array of object<br>`policyAgents?` array of object<br>`committed?` boolean<br>`recommended?` boolean | Change a pattern. |
| `orchestration_pattern_apply` | `projectId` uuid<br>`orchestrationId` uuid<br>`patternId` uuid | `parentOrchestratorNodeId?` uuid<br>`requestId?` uuid | Apply a pattern to an orchestration. |

## Components

Walkthrough: [6. Build the components](../README.md#6-build-the-components)

| Tool | Required inputs | Optional inputs | Purpose |
| --- | --- | --- | --- |
| `submit_code_file` | `projectId` uuid<br>`artifactType` `skill` \| `simulator` \| `perceptor` \| `orchestrator` \| `project_file`<br>`artifactId` uuid<br>`files` array of object | `entrypoint?` string<br>`dependencies?` array of string<br>`skillType?` `teacher` \| `controller` \| `coach`<br>`perceptorSensors?` array of string<br>`orchestratorType?` `teacher` \| `controller` \| `code`<br>`capabilitySummaries?` object<br>`perceptorSummary?` string | Publish files the assistant wrote as a new version of a skill, perceptor or orchestrator. |
| `get_artifact_scaffold` | `artifactType` `skill` \| `orchestrator` \| `perceptor` | `skillType?` `teacher` \| `controller` \| `coach`<br>`orchestratorType?` `teacher` \| `controller`<br>`perceptorSensors?` array of string | Get the runtime contract and a minimal example for a component type. |
| `perceptor_list` | `projectId` uuid |  | List perceptors. |
| `perceptor_get` | `projectId` uuid<br>`perceptorId` uuid |  | Read a perceptor and its versions. |
| `perceptor_create` | `projectId` uuid<br>`name` string | `description?` string<br>`sensors?` array of string<br>`upload?` boolean<br>`realizes?` string | Create a perceptor and its first version. |
| `perceptor_update` | `projectId` uuid<br>`perceptorId` uuid | `name?` string<br>`description?` string | Rename or describe a perceptor. |
| `perceptor_implementation_publish` | `projectId` uuid<br>`perceptorId` uuid<br>`sensors` array of string |  | Publish a new perceptor version. |
| `perceptor_confirm_upload` | `projectId` uuid<br>`implementationId` uuid | `perceptorSummary?` string | Confirm a perceptor code upload. |
| `amesa_perceptor_validate` | `organizationId` uuid<br>`projectId` uuid<br>`perceptorId` uuid | `clusterId?` uuid<br>`version?` number | Validate a perceptor version. |
| `operational_agent_list` | `projectId` uuid | `type?` `all` \| `teacher` \| `controller`<br>`limit?` integer<br>`offset?` integer | List skills (teachers, controllers, coaches). |
| `operational_agent_get` | `projectId` uuid<br>`optimizationAgentId` uuid | `limit?` integer<br>`offset?` integer | Read a skill and its versions. |
| `operational_agent_retrieve` | `projectId` uuid<br>`optimizationAgentId` uuid<br>`versionId` uuid |  | Get every file of one skill version. |
| `operational_agent_create` | `projectId` uuid<br>`name` string<br>`type` `teacher` \| `controller` \| `coach` | `requestId?` uuid<br>`description?` string<br>`realizes?` string | Create a skill and its first version. |
| `operational_agent_create_template` | `projectId` uuid | `requestId?` uuid<br>`name?` string<br>`realizes?` string | Create a teacher from the blank template; no upload, review, approval or validation needed. |
| `operational_agent_update` | `projectId` uuid<br>`optimizationAgentId` uuid | `requestId?` uuid<br>`name?` string<br>`description?` string<br>`committed?` boolean | Rename or describe a skill. |
| `operational_agent_implementation_publish` | `projectId` uuid<br>`optimizationAgentId` uuid | `requestId?` uuid<br>`type?` `teacher` \| `controller` \| `coach` | Publish a new skill version. |
| `operational_agent_confirm_upload` | `projectId` uuid<br>`implementationId` uuid | `capabilitySummaries?` object | Confirm a skill code upload. |
| `amesa_agent_validate` | `organizationId` uuid<br>`projectId` uuid<br>`agentId` uuid | `clusterId?` uuid<br>`version?` number<br>`orchestrationId?` uuid<br>`steps?` integer<br>`script?` array of object | Validate a skill version, including a run against a mock simulator. |
| `orchestrator_list` | `projectId` uuid |  | List orchestrators. |
| `orchestrator_get` | `projectId` uuid<br>`orchestratorId` uuid |  | Read an orchestrator and its versions. |
| `orchestrator_create` | `projectId` uuid<br>`name` string<br>`type` `teacher` \| `controller` | `requestId?` uuid<br>`description?` string<br>`realizes?` string | Create an orchestrator and its first version. |
| `orchestrator_update` | `projectId` uuid<br>`orchestratorId` uuid | `requestId?` uuid<br>`name?` string<br>`description?` string | Rename or describe an orchestrator. |
| `orchestrator_implementation_publish` | `projectId` uuid<br>`orchestratorId` uuid | `requestId?` uuid<br>`expectedVersion?` integer<br>`type?` `teacher` \| `controller` | Publish a new orchestrator version. |
| `orchestrator_confirm_upload` | `projectId` uuid<br>`implementationId` uuid | `capabilitySummaries?` object | Confirm an orchestrator code upload. |
| `amesa_orchestrator_validate` | `organizationId` uuid<br>`projectId` uuid<br>`orchestratorId` uuid | `clusterId?` uuid<br>`version?` number | Validate an orchestrator version. |
| `component_validation_status` | `organizationId` uuid<br>`jobId` uuid |  | Follow a validation run started by an amesa_*_validate tool. |
| `component_source_get` | `projectId` uuid<br>`componentType` `skill` \| `perceptor` \| `orchestrator`<br>`implementationId` uuid |  | Read the code of a published version. |
| `guidance_list` | `projectId` uuid |  | List guidance items in the library. |
| `guidance_get` | `projectId` uuid<br>`guidanceId` uuid |  | Read one guidance item. |
| `guidance_create` | `projectId` uuid<br>`name` string<br>`type` `goal` \| `constraint` \| `successCriteria` \| `reward` | `createdBy?` string<br>`conditions?` object \| object \| array of object \| object<br>`dataUrl?` uri | Create a goal, constraint, success criterion or reward. |
| `guidance_update` | `projectId` uuid<br>`guidanceId` uuid | `name?` string<br>`conditions?` object \| object \| array of object \| object<br>`dataUrl?` uri | Change a guidance item. |
| `guidance_publish_to_agent` | `projectId` uuid<br>`optimizationAgentId` uuid | `versionId?` uuid<br>`guidanceId?` uuid<br>`name?` string<br>`type?` `goal` \| `constraint` \| `successCriteria`<br>`replaceClauseIds?` array of string<br>`conditions?` object \| object \| array of object \| object | Publish guidance to a teacher as a new version. |
| `guidance_agent_get` | `projectId` uuid<br>`optimizationAgentId` uuid | `versionId?` uuid | Read the guidance clauses on a skill version. |
| `guidance_remove_from_agent` | `projectId` uuid<br>`optimizationAgentId` uuid<br>`clauseIds` array of string<br>`reason` string | `versionId?` uuid | Remove guidance clauses from a skill in a new version. |

## Assemble

Walkthrough: [7. Assemble the orchestration](../README.md#7-assemble-the-orchestration)

| Tool | Required inputs | Optional inputs | Purpose |
| --- | --- | --- | --- |
| `scenario_list` | `projectId` uuid |  | List scenarios. |
| `scenario_get` | `projectId` uuid<br>`scenarioId` uuid |  | Read one scenario. |
| `scenario_create` | `projectId` uuid<br>`name` string | `conditions?` array of object<br>`clusterId?` uuid \| null<br>`committed?` boolean<br>`episodeSteps?` integer \| null<br>`baselineOverrideEnabled?` boolean<br>`baselineOverrideValue?` number \| null<br>`baselineOverrideVariableId?` uuid \| null<br>`realizes?` string | Define a training scenario. |
| `scenario_update` | `projectId` uuid<br>`scenarioId` uuid | `name?` string<br>`conditions?` array of object<br>`clusterId?` uuid \| null<br>`committed?` boolean<br>`episodeSteps?` integer \| null<br>`baselineOverrideEnabled?` boolean<br>`baselineOverrideValue?` number \| null<br>`baselineOverrideVariableId?` uuid \| null | Change a scenario. |
| `scenario_flow_get` | `projectId` uuid |  | Read the scenario flow graph. |
| `scenario_flow_member_add` | `projectId` uuid<br>`phaseId` uuid<br>`scenarioId` uuid |  | Add a scenario to the flow. |
| `scenario_flow_member_remove` | `projectId` uuid<br>`scenarioId` uuid |  | Remove a scenario from the flow. |
| `scenario_flow_edge_create` | `projectId` uuid<br>`fromScenarioId` uuid<br>`toScenarioId` uuid |  | Connect two scenarios in the flow. |
| `scenario_flow_graph_import` | `projectId` uuid<br>`phases` array of object | `edges?` array of object | Import a whole scenario flow at once. |
| `clustering_scenarios_publish` | `organizationId` uuid<br>`jobId` uuid<br>`projectId` uuid |  | Publish regime-based scenarios into the use case. |
| `orchestration_list` | `projectId` uuid | `limit?` integer<br>`offset?` integer | List orchestrations. |
| `orchestration_create` | `projectId` uuid | `requestId?` uuid<br>`name?` string<br>`description?` string<br>`graph?` object | Create an orchestration. |
| `orchestration_duplicate` | `projectId` uuid<br>`orchestrationId` uuid | `requestId?` uuid<br>`name?` string<br>`description?` string | Copy an orchestration exactly. |
| `orchestration_component` | `projectId` uuid<br>`orchestrationId` uuid<br>`kind` `optimization_agent` \| `policy_agent` \| `perceptor` \| `communication_agent`<br>`action` `add` \| `remove`<br>`implementationId` uuid | `requestId?` uuid<br>`orchestratorNodeId?` uuid<br>`selectedScenarios?` array of uuid \| null | Add or remove one component. |
| `orchestration_workflow_deploy` | `projectId` uuid<br>`orchestrationId` uuid<br>`orchestrators` array of object | `requestId?` uuid<br>`perceptors?` array of uuid<br>`communicationAgents?` array of uuid | Replace the whole workflow in one step. |
| `orchestration_get_workflow` | `projectId` uuid<br>`orchestrationId` uuid |  | Read the current workflow. |
| `orchestration_prepare_for_training` | `projectId` uuid<br>`orchestrationId` uuid | `requestId?` uuid<br>`dryRun?` boolean | Repair invalid scenario selections before training. |

## Train and evaluate

Walkthrough: [8. Train and evaluate](../README.md#8-train-and-evaluate)

| Tool | Required inputs | Optional inputs | Purpose |
| --- | --- | --- | --- |
| `training_capacity_probe` | `organizationUuid` uuid | `clusterId?` uuid<br>`workers?` integer<br>`resourcesOverrides?` object | Check whether the cluster can take a training run. |
| `training_cycle_allocation_get` | `projectId` uuid<br>`orchestrationId` uuid |  | Get the suggested training cycles for each agent. |
| `training_job_submit` | `organizationUuid` uuid<br>`projectId` uuid<br>`orchestrationId` uuid<br>`trainingCycles` integer | `workers?` integer<br>`numEpisodesPerScenario?` integer<br>`numStepsPerEpisode?` integer<br>`rolloutFragmentLength?` number<br>`trainingCyclesPerNode?` object<br>`resourcesOverrides?` object<br>`clusterId?` uuid<br>`jobId?` uuid | Start a training run. |
| `training_job_stop` | `jobId` uuid |  | Stop a training run. |
| `training_job_restart` | `organizationUuid` uuid<br>`projectId` uuid<br>`jobId` uuid |  | Start a failed run again with the same parameters. |
| `training_job_submission_get` | `organizationUuid` uuid<br>`projectId` uuid<br>`orchestrationId` uuid<br>`trainingCycles` integer | `workers?` integer<br>`numEpisodesPerScenario?` integer<br>`numStepsPerEpisode?` integer<br>`rolloutFragmentLength?` number<br>`trainingCyclesPerNode?` object<br>`resourcesOverrides?` object<br>`clusterId?` uuid<br>`jobId?` uuid | Dry-run a training submission without starting it. |
| `training_job_logs_get` | `jobId` uuid | `after?` string<br>`limit?` integer<br>`type?` `training` \| `controller` \| `simulator` | Read a run's logs. |
| `training_session_list` | none | `orchestrationId?` uuid<br>`agentId?` uuid<br>`projectId?` uuid<br>`limit?` integer | List training sessions. |
| `training_session_get` | `jobId` uuid |  | Read a session's progress and results. |
| `training_skill_result_get` | `projectId` uuid<br>`generationId` uuid<br>`skillKey` string | `pointLimit?` integer | Read one skill's generated training result. |
| `training_history_get` | `jobId` uuid<br>`skillKey` string | `attemptKey?` uuid<br>`scenarioIndex?` integer<br>`limit?` integer<br>`after?` string | Read the training curve. |
| `training_history_upload` | `organizationId` uuid<br>`projectId` uuid<br>`metrics` array of object |  | Upload training history recorded elsewhere. |
| `benchmark_list` | `jobId` uuid |  | List benchmarks. |
| `benchmark_summary` | `jobId` uuid | `artifactId?` uuid | Read a benchmark's episode, step and reward summary. |
| `benchmark_describe` | `jobId` uuid |  | Describe what a benchmark contains. |
| `benchmark_query` | `jobId` uuid<br>`sql` string |  | Query benchmark data in depth. |
| `benchmark_compare` | `baselineJobId` uuid<br>`candidateJobId` uuid |  | Compare two training runs' benchmarks per scenario. |
| `benchmark_episode_trace` | `jobId` uuid | `scenario?` string<br>`episode?` integer<br>`artifactId?` uuid<br>`episodeOffset?` integer<br>`episodeLimit?` integer | Page through a benchmark's episode rewards. |
| `benchmark_artifact_list` | `jobId` uuid |  | List a training run's artifacts (IDs and times only). |
| `benchmark_report_skill_get` | `projectId` uuid<br>`reportId` uuid<br>`generationId` uuid<br>`skillKey` string<br>`scenarioKey` string | `episodeOffset?` integer<br>`episodeLimit?` integer | Read one skill and scenario result from a benchmark report. |
| `historian_describe` | `jobId` uuid |  | List the columns of a run's recorded time series. |
| `historian_query` | `jobId` uuid<br>`sql` string |  | Query recorded time series. |
| `report_create` | `projectId` uuid<br>`type` `simulators` \| `benchmark` \| `training` \| `skills` \| `validation`<br>`title` string<br>`body` string | `sourceLabel?` string<br>`sourceUrl?` string<br>`reportDate?` date-time | Save a report the assistant wrote. |
| `report_generate` | `type` `training` \| `benchmark` \| `historian` \| `simulators` \| `skill` \| `skills`<br>`projectId` uuid | `jobId?` uuid<br>`datasetId?` uuid<br>`simulatorImplementationId?` uuid<br>`scenarioId?` uuid<br>`optimizationAgentId?` uuid<br>`orchestrationId?` uuid<br>`requestKey?` string | Make sure a generated report exists and read its status. |
| `report_list` | `projectId` uuid | `orchestrationId?` uuid<br>`types?` array of string<br>`query?` string<br>`sourceLabel?` string<br>`reportDateFrom?` date-time<br>`reportDateTo?` date-time<br>`createdFrom?` date-time<br>`createdTo?` date-time<br>`sortBy?` `reportDate` \| `createdAt` \| `updatedAt` \| `title`<br>`sortDirection?` `asc` \| `desc`<br>`offset?` integer<br>`limit?` integer<br>`includeBody?` boolean | List reports. |
| `report_get` | `projectId` uuid<br>`reportId` uuid | `includeHistorianDetail?` boolean<br>`includeSimulationDetail?` boolean<br>`includeTrainingDetail?` boolean<br>`includeBenchmarkDetail?` boolean<br>`includeSkillDetail?` boolean<br>`skillLimit?` integer<br>`variableLimit?` integer | Read a report. |
| `skill_report_candidates` | `projectId` uuid |  | List scenario and skill pairs a training report can cover. |

## Operate

Walkthrough: [9. Operate the agents](../README.md#9-operate-the-agents)

| Tool | Required inputs | Optional inputs | Purpose |
| --- | --- | --- | --- |
| `communication_agent_create` | `projectId` uuid<br>`name` string |  | Create a communication agent. |
| `communication_agent_get` | `projectId` uuid<br>`communicationAgentId` uuid |  | Read a communication agent. |
| `communication_agent_list` | `projectId` uuid |  | List communication agents. |
| `communication_agent_update` | `projectId` uuid<br>`communicationAgentId` uuid<br>`name` string |  | Change a communication agent. |
| `communication_agent_publish` | `projectId` uuid<br>`name` string<br>`prompt` string | `communicationAgentId?` uuid | Publish a communication agent's name and prompt as a new version. |
| `communication_agent_document_upload` | `action` `request_url` \| `confirm`<br>`projectId` uuid<br>`communicationAgentId` uuid | `organizationId?` uuid<br>`fileName?` string<br>`fileSize?` integer<br>`contentType?` string<br>`documentId?` uuid<br>`useLLM?` boolean | Upload a reference document. |
| `communication_agent_document_ingest` | `projectId` uuid<br>`communicationAgentId` uuid<br>`documentId` uuid |  | Read a document into the agent's knowledge. |
| `communication_agent_document_list` | `projectId` uuid<br>`communicationAgentId` uuid |  | List the agent's documents. |
| `policy_agent_create` | `projectId` uuid<br>`name` string |  | Create a policy agent. |
| `policy_agent_get` | `projectId` uuid<br>`policyAgentId` uuid |  | Read a policy agent. |
| `policy_agent_list` | `projectId` uuid |  | List policy agents. |
| `policy_agent_update` | `projectId` uuid<br>`policyAgentId` uuid<br>`name` string |  | Change a policy agent. |
| `policy_agent_document_upload` | `action` `request_url` \| `confirm`<br>`projectId` uuid<br>`policyAgentId` uuid | `organizationId?` uuid<br>`fileName?` string<br>`fileSize?` integer<br>`contentType?` string<br>`documentId?` uuid<br>`useLLM?` boolean | Upload a policy document (PDF). |
| `policy_agent_document_list` | `projectId` uuid<br>`policyAgentId` uuid |  | List a policy agent's documents. |
| `policy_agent_document_search` | `projectId` uuid<br>`policyAgentId` uuid<br>`query` string | `documentIds?` array of uuid<br>`topK?` integer | Search a policy agent's documents. |

## Autonomous loops

Walkthrough: [Autonomous loops](../README.md#autonomous-loops)

| Tool | Required inputs | Optional inputs | Purpose |
| --- | --- | --- | --- |
| `agent_loop_preview` | `projectId` uuid | `threadId?` uuid<br>`goalKind?` `training-kpi` \| `simulator-fit` \| `data-score` \| `agent-fix` \| `domain-graph` \| `training-recovery` \| `training-diagnostics`<br>`orchestrationId?` uuid<br>`simulatorId?` uuid<br>`scoreThreshold?` number<br>`datasetUuid?` uuid<br>`candidates?` `any` \| `all`<br>`maxVariableErrorPercent?` number<br>`variableErrorOverrides?` array of object<br>`minAnalyzedEpisodes?` integer<br>`componentId?` uuid<br>`orchestrationIds?` array of uuid<br>`autonomous?` boolean<br>`clusterId?` uuid \| null<br>`title?` string<br>`maxAttempts?` integer<br>`maxHours?` number<br>`mode?` `meet` \| `improve`<br>`policy?` object<br>`instructions?` string | Preview what a loop will do before it starts. |
| `agent_loop_start` | `projectId` uuid | `threadId?` uuid<br>`goalKind?` `training-kpi` \| `simulator-fit` \| `data-score` \| `agent-fix` \| `domain-graph` \| `training-recovery` \| `training-diagnostics`<br>`orchestrationId?` uuid<br>`simulatorId?` uuid<br>`scoreThreshold?` number<br>`datasetUuid?` uuid<br>`candidates?` `any` \| `all`<br>`maxVariableErrorPercent?` number<br>`variableErrorOverrides?` array of object<br>`minAnalyzedEpisodes?` integer<br>`componentId?` uuid<br>`orchestrationIds?` array of uuid<br>`autonomous?` boolean<br>`clusterId?` uuid \| null<br>`title?` string<br>`maxAttempts?` integer<br>`maxHours?` number<br>`mode?` `meet` \| `improve`<br>`policy?` object<br>`instructions?` string | Start a background loop toward a goal. |
| `agent_loop_list` | `projectId` uuid | `orchestrationId?` uuid | List loops. |
| `agent_loop_get` | `projectId` uuid<br>`loopId` uuid |  | Follow a loop's progress. |
| `agent_loop_message` | `projectId` uuid<br>`loopId` uuid<br>`text` string |  | Answer, steer or resume a loop. |
| `agent_loop_approve` | `projectId` uuid<br>`loopId` uuid<br>`approvalId` uuid<br>`decision` `approve` \| `reject` | `note?` string | Approve or reject a change a loop proposed. |
| `agent_loop_stop` | `projectId` uuid<br>`loopId` uuid |  | Pause a loop; a message resumes it. |
| `agent_loop_complete` | `projectId` uuid<br>`loopId` uuid |  | End a data, simulator or training loop and keep its result. |
| `agent_loop_kpi_interview` | `projectId` uuid<br>`orchestrationId` uuid | `clusterId?` string<br>`instructions?` string<br>`maxAttempts?` integer<br>`maxHours?` number<br>`mode?` `meet` \| `improve`<br>`threadId?` uuid | Ask for a missing KPI, then start the training loop. |
| `brain` | `projectId` uuid<br>`requestKey` string<br>`plan` object |  | Hand a whole multi-step plan to AMESA Brain. |
| `monitor` | `projectId` uuid<br>`orchestrationIds` array of uuid | `cyclesPerAgent?` integer<br>`clusterId?` uuid<br>`instructions?` string | Have the AMESA Monitor check that orchestrations run. |
| `training_diagnostic_batch_start` | `organizationUuid` uuid<br>`projectId` uuid<br>`orchestrationIds` array of uuid<br>`cyclesPerAgent` integer | `workers?` integer<br>`numEpisodesPerScenario?` integer<br>`numStepsPerEpisode?` integer<br>`rolloutFragmentLength?` number<br>`resourcesOverrides?` object<br>`clusterId?` uuid | Start short diagnostic jobs on several orchestrations (Monitor only). |

## Jobs and diagnostics

Walkthrough: [Jobs and diagnostics](../README.md#jobs-and-diagnostics)

| Tool | Required inputs | Optional inputs | Purpose |
| --- | --- | --- | --- |
| `job_diagnostics_get` | `jobId` uuid |  | Explain why a training job failed or struggles. |
| `job_container_logs_get` | `jobId` uuid<br>`role` enum (10 values) | `index?` integer<br>`tail?` integer<br>`grep?` string<br>`since?` date-time | Read one container's logs for a training job. |
| `job_speed_analyze` | `jobId` uuid |  | Find what is slowing a job. |
| `known_issue_match` | `text` string |  | Match an error against known issues and fixes. |

## Replaced legacy tools

Earlier versions of the AMESA MCP server used the tools below. They are not in the current catalog; use the replacement instead.

| Legacy tool | Use instead |
| --- | --- |
| `org_list`, `org_get` | `organization_list`, `organization_get` |
| `project_list`, `project_get` | `use_case_list`, `use_case_get` |
| `agent_teacher_list`, `agent_controller_list` | `operational_agent_list` |
| `agent_teacher_publish_metadata`, `agent_controller_publish_metadata` | `operational_agent_create` (creates the agent and its first version) |
| `agent_teacher_publish_code`, `agent_controller_publish_code` | `operational_agent_implementation_publish` (new version), or `submit_code_file` |
| `agent_teacher_confirm_upload`, `agent_controller_confirm_upload` | `operational_agent_confirm_upload` |
| `perceptor_publish_metadata` | `perceptor_create` |
| `perceptor_publish_code` | `perceptor_implementation_publish`, or `submit_code_file` |
| `orchestrator_teacher_*`, `orchestrator_controller_*` | `orchestrator_list`, `orchestrator_create`, `orchestrator_implementation_publish`, `orchestrator_confirm_upload` |
| `list_formations` | `orchestration_list` |
| `start_training` | `training_job_submit` (dry-run first with `training_job_submission_get`) |
| `list_training_jobs` | `training_session_list` |
| `get_orchestration_metrics` | `training_history_get`, `benchmark_summary` |
| `get_benchmark_artifact_download_url` | `benchmark_describe` + `benchmark_query`, `benchmark_artifact_list` |
| `get_historian_artifact_download_url` | `historian_describe` + `historian_query` |
| `read_sim_sensors`, `read_sim_actions` | `use_case_sensors_get`, `mapping_list` |
| `list_docs`, `fetch_doc` | `platform_methodology_search`, `platform_methodology_fetch` |
