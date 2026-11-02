# AMESA MCP tool index

All 181 tools of the AMESA MCP server, grouped by the lifecycle stage they belong to. Each group links back to the stage walkthrough in the [README](../README.md). Tool availability depends on your organization's permissions.

Use your browser's find (Ctrl+F / Cmd+F) to look up a tool by name or purpose.

## Contents

| Group | Tools |
| --- | ---: |
| [Getting started](#getting-started) | 9 |
| [Set up](#set-up) | 11 |
| [Data](#data) | 10 |
| [Simulator](#simulator) | 24 |
| [Knowledge](#knowledge) | 9 |
| [Design](#design) | 9 |
| [Components](#components) | 34 |
| [Assemble](#assemble) | 17 |
| [Train and evaluate](#train-and-evaluate) | 27 |
| [Operate](#operate) | 15 |
| [Autonomous loops](#autonomous-loops) | 12 |
| [Jobs and diagnostics](#jobs-and-diagnostics) | 4 |
| **Total** | **181** |

## Getting started

Walkthrough: [Before you begin](../README.md#before-you-begin)

| Tool | Purpose |
| --- | --- |
| `mcp_tools_search` | Search the tool catalog by intent; returns names, descriptions and arguments. |
| `mcp_tools_read` | Run up to eight read-only tools in one round trip. |
| `mcp_tools_call` | Call a tool found through the catalog. |
| `platform_methodology_search` | Search AMESA's platform and SDK documentation. |
| `platform_methodology_fetch` | Read one methodology document in full. |
| `cluster_list` | List your organization's compute clusters and whether each is connected. |
| `cluster_health_get` | Check whether a cluster is online and healthy. |
| `cluster_create_local` | Issue a single-use code to enroll a local machine (same as compute_enrollment_issue). |
| `compute_enrollment_issue` | Issue a single-use code that enrolls a new local compute node. |

## Set up

Walkthrough: [1. Set up the use case](../README.md#1-set-up-the-use-case)

| Tool | Purpose |
| --- | --- |
| `organization_list` | List the organizations you belong to. |
| `organization_get` | Find an organization's ID by its exact name. |
| `use_case_list` | List use cases (projects). |
| `use_case_get` | Read a use case in full. |
| `use_case_brief_get` | Read a short overview of a use case. |
| `use_case_update` | Change a use case's name, description or settings. |
| `kpi_settings_get` | Read the KPI and ROI settings training is measured against. |
| `kpi_settings_update` | Set the KPI and ROI settings (replaces them as a whole). |
| `use_case_journey_get` | See which lifecycle stage the use case is in. |
| `use_case_journey_advance` | Record that the use case moved to a new stage. |
| `assistant_handoff` | Hand the conversation to the assistant that leads another stage. |

## Data

Walkthrough: [2. Prepare the data](../README.md#2-prepare-the-data)

| Tool | Purpose |
| --- | --- |
| `dataset_list` | List staged datasets with their columns and roles. |
| `amesa_data_stats` | Describe each column of a dataset. |
| `amesa_data_integrity` | Score empty, infinite, non-numeric, outlier and flat values. |
| `amesa_data_score` | Score how strongly the sensors respond to the actions. |
| `amesa_data_assign` | Set columns as sensor, replica, action or ignored. |
| `amesa_data_suggest` | Rank columns by how much they respond and propose a focused set. |
| `amesa_data_prune` | Drop outlier values into a new copy of the dataset. |
| `amesa_data_split` | Mark episode boundaries with rules and write the split dataset. |
| `amesa_data_perceive` | Run a perceptor over a dataset and write its outputs as new columns. |
| `amesa_data_kpi` | Derive a KPI benchmark from a data column and recommend the KPI. |

## Simulator

Walkthrough: [3. Fit a simulator](../README.md#3-fit-a-simulator)

| Tool | Purpose |
| --- | --- |
| `amesa_sim_train` | Train a data-driven simulator from a dataset. |
| `amesa_sim_analyze` | Roll a trained simulator out over its dataset's episodes; the platform scores it. |
| `amesa_sim_validate` | Validate a code simulator you published (not a data-driven one). |
| `simulator_list` | List simulators and their latest builds. |
| `simulator_retrieve` | Get a simulator build's image reference and whether it is ready. |
| `simulator_score_get` | Read a simulator's score. |
| `simulator_validation_get` | Read one simulator validation run. |
| `simulator_variable_fidelity_get` | Read one variable's result from a validation run. |
| `simulator_relationship_get` | Read how one action relates to one sensor in a validation run (not causal). |
| `simulator_job_list` | List simulator, data and clustering jobs. |
| `simulator_job_status` | Poll a running simulator job. |
| `sim_publish_metadata` | Register your own simulator. |
| `sim_publish_code` | Get the upload URL for your simulator's code. |
| `sim_confirm_upload` | Confirm a simulator code upload and start its build. |
| `mapping_list` | List a simulator build's sensor and action mappings. |
| `mapping_update` | Rename variables (only the mapped name can change). |
| `mapping_dependents_list` | See what still uses a variable's name. |
| `amesa_cluster_create` | Find operating regimes in a dataset. |
| `amesa_cluster_convert` | Turn found regimes into scenario definitions. |
| `amesa_cluster_sims` | Train one simulator per regime. |
| `activity_cluster_get` | Read the regimes of a variant simulator. |
| `activity_cluster_upload` | Store clustering results as variant simulators and scenarios. |
| `use_case_simulator_assign` | Attach a simulator to the use case. |
| `use_case_sensors_get` | List the use case's sensors and actions. |

## Knowledge

Walkthrough: [4. Capture domain knowledge](../README.md#4-capture-domain-knowledge)

| Tool | Purpose |
| --- | --- |
| `use_case_document_upload` | Upload a reference document. |
| `use_case_document_ingest` | Read a document into the knowledge base. |
| `use_case_document_list` | List the use case's documents. |
| `use_case_document_delete` | Remove a document. |
| `use_case_search` | Search the use case's documents, knowledge and past conversations, with citations. |
| `use_case_graph_get` | Read the domain graph, an entity's neighborhood, or its gaps. |
| `use_case_graph_query` | Ask targeted questions of the domain graph. |
| `use_case_graph_edit` | Add, link, merge or correct entities and facts. |
| `use_case_graph_review` | Confirm or retract proposed items and settle contradictions. |

## Design

Walkthrough: [5. Design the agent system](../README.md#5-design-the-agent-system)

| Tool | Purpose |
| --- | --- |
| `decomposition_create` | Draft the tree of orchestrators and skills. |
| `decomposition_edit` | Refine a draft decomposition. |
| `decomposition_get` | Read a decomposition and its warnings. |
| `decomposition_promote` | Create real components and an orchestration from an approved draft. |
| `orchestration_pattern_create` | Save a reusable orchestration shape. |
| `orchestration_pattern_list` | List saved patterns. |
| `orchestration_pattern_get` | Read one pattern. |
| `orchestration_pattern_update` | Change a pattern. |
| `orchestration_pattern_apply` | Apply a pattern to an orchestration. |

## Components

Walkthrough: [6. Build the components](../README.md#6-build-the-components)

| Tool | Purpose |
| --- | --- |
| `submit_code_file` | Publish files the assistant wrote as a new version of a skill, perceptor or orchestrator. |
| `get_artifact_scaffold` | Get the runtime contract and a minimal example for a component type. |
| `perceptor_list` | List perceptors. |
| `perceptor_get` | Read a perceptor and its versions. |
| `perceptor_create` | Create a perceptor and its first version. |
| `perceptor_update` | Rename or describe a perceptor. |
| `perceptor_implementation_publish` | Publish a new perceptor version. |
| `perceptor_confirm_upload` | Confirm a perceptor code upload. |
| `amesa_perceptor_validate` | Validate a perceptor version. |
| `operational_agent_list` | List skills (teachers, controllers, coaches). |
| `operational_agent_get` | Read a skill and its versions. |
| `operational_agent_retrieve` | Get every file of one skill version. |
| `operational_agent_create` | Create a skill and its first version. |
| `operational_agent_create_template` | Create a teacher from the blank template; no upload, review, approval or validation needed. |
| `operational_agent_update` | Rename or describe a skill. |
| `operational_agent_implementation_publish` | Publish a new skill version. |
| `operational_agent_confirm_upload` | Confirm a skill code upload. |
| `amesa_agent_validate` | Validate a skill version, including a run against a mock simulator. |
| `orchestrator_list` | List orchestrators. |
| `orchestrator_get` | Read an orchestrator and its versions. |
| `orchestrator_create` | Create an orchestrator and its first version. |
| `orchestrator_update` | Rename or describe an orchestrator. |
| `orchestrator_implementation_publish` | Publish a new orchestrator version. |
| `orchestrator_confirm_upload` | Confirm an orchestrator code upload. |
| `amesa_orchestrator_validate` | Validate an orchestrator version. |
| `component_validation_status` | Follow a validation run started by an amesa_*_validate tool. |
| `component_source_get` | Read the code of a published version. |
| `guidance_list` | List guidance items in the library. |
| `guidance_get` | Read one guidance item. |
| `guidance_create` | Create a goal, constraint, success criterion or reward. |
| `guidance_update` | Change a guidance item. |
| `guidance_publish_to_agent` | Publish guidance to a teacher as a new version. |
| `guidance_agent_get` | Read the guidance clauses on a skill version. |
| `guidance_remove_from_agent` | Remove guidance clauses from a skill in a new version. |

## Assemble

Walkthrough: [7. Assemble the orchestration](../README.md#7-assemble-the-orchestration)

| Tool | Purpose |
| --- | --- |
| `scenario_list` | List scenarios. |
| `scenario_get` | Read one scenario. |
| `scenario_create` | Define a training scenario. |
| `scenario_update` | Change a scenario. |
| `scenario_flow_get` | Read the scenario flow graph. |
| `scenario_flow_member_add` | Add a scenario to the flow. |
| `scenario_flow_member_remove` | Remove a scenario from the flow. |
| `scenario_flow_edge_create` | Connect two scenarios in the flow. |
| `scenario_flow_graph_import` | Import a whole scenario flow at once. |
| `clustering_scenarios_publish` | Publish regime-based scenarios into the use case. |
| `orchestration_list` | List orchestrations. |
| `orchestration_create` | Create an orchestration. |
| `orchestration_duplicate` | Copy an orchestration exactly. |
| `orchestration_component` | Add or remove one component. |
| `orchestration_workflow_deploy` | Replace the whole workflow in one step. |
| `orchestration_get_workflow` | Read the current workflow. |
| `orchestration_prepare_for_training` | Repair invalid scenario selections before training. |

## Train and evaluate

Walkthrough: [8. Train and evaluate](../README.md#8-train-and-evaluate)

| Tool | Purpose |
| --- | --- |
| `training_capacity_probe` | Check whether the cluster can take a training run. |
| `training_cycle_allocation_get` | Get the suggested training cycles for each agent. |
| `training_job_submit` | Start a training run. |
| `training_job_stop` | Stop a training run. |
| `training_job_restart` | Start a failed run again with the same parameters. |
| `training_job_submission_get` | Dry-run a training submission without starting it. |
| `training_job_logs_get` | Read a run's logs. |
| `training_session_list` | List training sessions. |
| `training_session_get` | Read a session's progress and results. |
| `training_skill_result_get` | Read one skill's generated training result. |
| `training_history_get` | Read the training curve. |
| `training_history_upload` | Upload training history recorded elsewhere. |
| `benchmark_list` | List benchmarks. |
| `benchmark_summary` | Read a benchmark's episode, step and reward summary. |
| `benchmark_describe` | Describe what a benchmark contains. |
| `benchmark_query` | Query benchmark data in depth. |
| `benchmark_compare` | Compare two training runs' benchmarks per scenario. |
| `benchmark_episode_trace` | Page through a benchmark's episode rewards. |
| `benchmark_artifact_list` | List a training run's artifacts (IDs and times only). |
| `benchmark_report_skill_get` | Read one skill and scenario result from a benchmark report. |
| `historian_describe` | List the columns of a run's recorded time series. |
| `historian_query` | Query recorded time series. |
| `report_create` | Save a report the assistant wrote. |
| `report_generate` | Make sure a generated report exists and read its status. |
| `report_list` | List reports. |
| `report_get` | Read a report. |
| `skill_report_candidates` | List scenario and skill pairs a training report can cover. |

## Operate

Walkthrough: [9. Operate the agents](../README.md#9-operate-the-agents)

| Tool | Purpose |
| --- | --- |
| `communication_agent_create` | Create a communication agent. |
| `communication_agent_get` | Read a communication agent. |
| `communication_agent_list` | List communication agents. |
| `communication_agent_update` | Change a communication agent. |
| `communication_agent_publish` | Publish a communication agent's name and prompt as a new version. |
| `communication_agent_document_upload` | Upload a reference document. |
| `communication_agent_document_ingest` | Read a document into the agent's knowledge. |
| `communication_agent_document_list` | List the agent's documents. |
| `policy_agent_create` | Create a policy agent. |
| `policy_agent_get` | Read a policy agent. |
| `policy_agent_list` | List policy agents. |
| `policy_agent_update` | Change a policy agent. |
| `policy_agent_document_upload` | Upload a policy document (PDF). |
| `policy_agent_document_list` | List a policy agent's documents. |
| `policy_agent_document_search` | Search a policy agent's documents. |

## Autonomous loops

Walkthrough: [Autonomous loops](../README.md#autonomous-loops)

| Tool | Purpose |
| --- | --- |
| `agent_loop_preview` | Preview what a loop will do before it starts. |
| `agent_loop_start` | Start a background loop toward a goal. |
| `agent_loop_list` | List loops. |
| `agent_loop_get` | Follow a loop's progress. |
| `agent_loop_message` | Answer, steer or resume a loop. |
| `agent_loop_approve` | Approve or reject a change a loop proposed. |
| `agent_loop_stop` | Pause a loop; a message resumes it. |
| `agent_loop_complete` | End a data, simulator or training loop and keep its result. |
| `agent_loop_kpi_interview` | Ask for a missing KPI, then start the training loop. |
| `brain` | Hand a whole multi-step plan to AMESA Brain. |
| `monitor` | Have the AMESA Monitor check that orchestrations run. |
| `training_diagnostic_batch_start` | Start short diagnostic jobs on several orchestrations (Monitor only). |

## Jobs and diagnostics

Walkthrough: [Jobs and diagnostics](../README.md#jobs-and-diagnostics)

| Tool | Purpose |
| --- | --- |
| `job_diagnostics_get` | Explain why a training job failed or struggles. |
| `job_container_logs_get` | Read one container's logs for a training job. |
| `job_speed_analyze` | Find what is slowing a job. |
| `known_issue_match` | Match an error against known issues and fixes. |
