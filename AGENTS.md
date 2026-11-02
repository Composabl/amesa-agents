# AGENTS.md — AI Agent Guidelines for amesa-agents

## From a dataset to autonomous operational agents

The AMESA MCP server lets an AI assistant such as Claude run the whole AMESA platform for you. It turns plant data into a simulator, builds and trains agents against that simulator, and leaves you with agents that run your process.

The platform's work follows nine lifecycle stages, each with its own set of MCP tools:

| # | Stage | Produces |
| - | ----- | -------- |
| 1 | Set up the use case | A use case with a KPI and a journey stage |
| 2 | Prepare the data | A scored dataset with clear column roles |
| 3 | Fit a simulator | A validated data-driven model (DDM) |
| 4 | Capture domain knowledge | A domain graph |
| 5 | Design the agent system | A decomposition of orchestrators and skills |
| 6 | Build the components | Validated skills, perceptors and orchestrators |
| 7 | Assemble the orchestration | An orchestration ready for training |
| 8 | Train and evaluate | Trained agents with benchmark evidence against the KPI |
| 9 | Operate the agents | Agents in service |

The AMESA MCP server is configured as `amesa` in [`.mcp.json`](./.mcp.json). The [README](./README.md) walks each stage and names its tools; [`doc/tools.md`](./doc/tools.md) lists every tool with its purpose. When unsure which tool fits a task, search the catalog with `mcp_tools_search`.

This file provides guidance for AI coding agents (GitHub Copilot, Codex, Claude, etc.) working in this repository. Read this file first, then consult the resources below before writing any code.

---

## Key References

| Resource                             | Purpose                                                                                             |
| ------------------------------------ | --------------------------------------------------------------------------------------------------- |
| [`README.md`](./README.md)           | AMESA MCP tools: lifecycle stage walkthrough, autonomous loops, jobs and diagnostics                |
| [`doc/tools.md`](./doc/tools.md)     | Index of every AMESA MCP tool, grouped by lifecycle stage                                           |
| [`agent-context/`](./agent-context/) | Detailed specs for every AMESA component type — **read the relevant subfolder before implementing** |

### agent-context subfolders

| Folder                                                     | When to read it                                           |
| ---------------------------------------------------------- | --------------------------------------------------------- |
| [`agent-context/teacher/`](./agent-context/teacher/)       | Implementing `AgentTeacher` or goal-based teachers        |
| [`agent-context/controller/`](./agent-context/controller/) | Implementing `AgentController`                            |
| [`agent-context/orchestrators/`](./agent-context/orchestrators/)   | Implementing an orchestrator (an `AgentTeacher` or `AgentController` subclass that picks the child skill) |
| [`agent-context/perceptors/`](./agent-context/perceptors/) | Implementing `PerceptorImpl`                              |
| [`agent-context/goals/`](./agent-context/goals/)           | Using goal types and coordinated goals                    |
| [`agent-context/analysis/`](./agent-context/analysis/)     | Parsing benchmark JSON and historian data                 |

Each subfolder contains: `overview.md`, `reference.md`, `publishing.md`, `job-json-schema.md`, and `quirks.md`. Always read `quirks.md` — it documents non-obvious behavior that will cause silent failures if ignored.

The `goals/` subfolder also includes `goal-types.md` (covers `MaximizeGoal`, `ApproachGoal`, `AvoidGoal`) and `coordinated-goal.md` (covers `CoordinatedGoal` and `AgentCoach`).

---

## Repo Structure

```
amesa-agents/
├── AGENTS.md                 # This file
├── README.md                 # AMESA MCP tools guide
├── .mcp.json                 # AMESA MCP server config
├── agent-context/            # Component specs for agents to read before implementing
│   ├── teacher/
│   ├── controller/
│   ├── orchestrators/
│   ├── perceptors/
│   ├── goals/
│   └── analysis/
├── agents/                   # Implemented agent artifacts
│   ├── controllers/
│   │   ├── creating-and-publishing-controllers.md
│   │   └── controller-example/
│   ├── orchestrators/
│   │   ├── creating-and-publishing-orchestrators.md
│   │   └── orchestrator-example/
│   └── teachers/
│       ├── creating-and-publishing-teachers.md
│       ├── teacher-example/
│       ├── coordinated-example/
│       └── goals-example/
├── datasets/                 # Sample CSV datasets (concrete, fusion, mixer) to stage with `amesa data stage`
├── doc/                      # tools.md: index of every AMESA MCP tool
└── perceptors/               # Implemented perceptor artifacts
    ├── creating-and-publishing-perceptors.md
    └── perceptors-example/
```

---

## Coding Conventions

### Python

- **Python version:** 3.10–3.11 (prefer 3.11.8)
- Use a virtual environment: `python -m venv .venv && source .venv/bin/activate`
- Install AMESA (includes AMESA Compute and the `amesa` CLI): `pip install amesa`
- Dependency declarations go in `pyproject.toml` — do not use bare `requirements.txt` for new artifacts

### Project layout (per artifact)

Each agent, orchestrator, or perceptor lives in its own folder with:

```
my-artifact/
├── pyproject.toml      # top-level [amesa] section required — type, entrypoint
└── my_artifact/
    └── ...             # Implementation
```

The top-level `[amesa]` section in `pyproject.toml` is required for publishing (not `[tool.amesa]`, which the SDK does not read). It holds `type` and `entrypoint`; the name, version and description go in `[project]`. The `type` field must match the artifact type (e.g., `"agent-teacher"`, `"agent-controller"`, `"orchestrator-teacher"`, `"orchestrator-controller"`).

### Implementing components

- Read the matching `agent-context/<type>/reference.md` for the exact base class and method signatures
- Read `agent-context/<type>/quirks.md` before finalizing any implementation
- Do not guess interface details — the specs in `agent-context/` are authoritative

### Publishing

- Use the AMESA MCP tools or the `amesa` CLI (`amesa agent publish ./my-artifact/`)
- Authenticate first: `amesa login`
- After publishing, confirm the upload and record the returned project/implementation IDs

---

## Testing & Validation

- Run existing tests with whatever test runner is already configured in the artifact's `pyproject.toml`; do not introduce new test frameworks
- Validate the `pyproject.toml` `[amesa]` section is complete before attempting a publish
- Check `agent-context/<type>/job-json-schema.md` to validate job payload structure before submitting

---

## Do Not

- Do not modify `.mcp.json` unless explicitly asked
- Do not commit secrets or credentials
- Do not create new artifacts outside `agents/` or `perceptors/` unless directed
- Do not invent interface signatures — always check `agent-context/<type>/reference.md`
