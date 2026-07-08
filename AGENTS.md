# AGENTS.md — AI Agent Guidelines for amesa-agents

This file provides guidance for AI coding agents (GitHub Copilot, Codex, Claude, etc.) working in this repository. Read this file first, then consult the resources below before writing any code.

---

## Key References

| Resource                             | Purpose                                                                                             |
| ------------------------------------ | --------------------------------------------------------------------------------------------------- |
| [`README.md`](./README.md)           | Full project overview, CLI reference, and getting-started examples                                  |
| [`agent-context/`](./agent-context/) | Detailed specs for every AMESA component type — **read the relevant subfolder before implementing** |

### agent-context subfolders

| Folder                                                     | When to read it                                           |
| ---------------------------------------------------------- | --------------------------------------------------------- |
| [`agent-context/teacher/`](./agent-context/teacher/)       | Implementing `AgentTeacher` or goal-based teachers        |
| [`agent-context/controller/`](./agent-context/controller/) | Implementing `AgentController`                            |
| [`agent-context/orchestrators/`](./agent-context/orchestrators/)   | Implementing `AgentOrchestrator` or `AgentOrchestratorController` |
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
├── README.md                 # Project overview and CLI reference
├── .mcp.json                 # AMESA MCP server config
├── .squad/                   # AI team definitions (Hicks, Hudson, Scribe, Ralph)
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
│       ├── goals-example/
│       └── quality-rating-teacher/
└── perceptors/               # Implemented perceptor artifacts
    ├── creating-and-publishing-perceptors.md
    └── perceptors-example/
```

---

## AI Team

This workspace uses a AMESA assist agents (Squad). Address them by name:

| Agent      | Role                    | What to ask them                                        |
| ---------- | ----------------------- | ------------------------------------------------------- |
| **Hicks**  | Implementation Engineer | Write Python code, scaffold artifacts, publish to AMESA |
| **Hudson** | Performance Analyst     | Parse benchmarks, evaluate constraints, compare runs    |
| **Scribe** | Session Logger          | Maintain project history and documentation              |
| **Ralph**  | Work Monitor            | Track task progress and dependencies                    |

---

## Coding Conventions

### Python

- **Python version:** 3.10–3.12 (prefer 3.11.8)
- Use a virtual environment: `python -m venv .venv && source .venv/bin/activate`
- Install the AMESA CLI: `pip install amesa-cli`
- Dependency declarations go in `pyproject.toml` — do not use bare `requirements.txt` for new artifacts

### Project layout (per artifact)

Each agent, orchestrator, or perceptor lives in its own folder with:

```
my-artifact/
├── pyproject.toml      # [tool.amesa] section required — name, version, description, type
└── my_artifact/
    └── ...             # Implementation
```

The `[tool.amesa]` section in `pyproject.toml` is required for publishing. The `type` field must match the artifact type (e.g., `"agent-teacher"`, `"agent-controller"`, `"orchestrator-teacher"`, `"orchestrator-controller"`).

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
- Validate the `pyproject.toml` `[tool.amesa]` section is complete before attempting a publish
- Check `agent-context/<type>/job-json-schema.md` to validate job payload structure before submitting

---

## Do Not

- Do not modify `.mcp.json` unless explicitly asked
- Do not commit secrets or credentials
- Do not create new artifacts outside `agents/` or `perceptors/` unless directed
- Do not invent interface signatures — always check `agent-context/<type>/reference.md`
