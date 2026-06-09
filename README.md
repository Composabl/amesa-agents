# AMESA Agent Orchestration Workspace

This is an AI-assisted workspace for building, publishing, and analyzing intelligent control agents using the **AMESA Agent Orchestration Studio**.

## What Is This Repo?

`amesa-agents` is a development environment where you define control objectives and let the AMESA AI team implement and deploy them. You write natural language specifications, and your AI team:

- Implements AMESA components in Python — skills (`SkillTeacher`, `SkillController`, goal-based teachers, coordinated skills), selectors (`SkillSelector`, `SkillSelectorController`), and perceptors (`PerceptorImpl`)
- Publishes to the AMESA Agent Orchestration Studio
- Analyzes performance against benchmarks
- Recommends improvements

This workspace is all about flexibility. You can use your own coding agents to create artifacts that you can review, modify, then publish to the AMESA platform by connecting via the AMESA MCP server or publishing manually using the CLI.

## What Is AMESA?

**AMESA Agent Orchestration Studio** is a platform for:

- **Building** intelligent control agents that learn and adapt
- **Publishing** agents to managed environments with version control
- **Training** agents in simulation
- **Monitoring** performance with structured data (benchmarks, historian logs)

AMESA handles the infrastructure; your Squad AI team handles the implementation.

## Core Capabilities

### 1: Build & Publish Agents

Hicks is the Implementation Engineer. Use Hicks to implement agents in Python, then publish to AMESA:

```
"Hicks, build a SkillTeacher that learns to optimize [control objective] given [sensor inputs]"
```

Hicks will:

1. Implement a `SkillTeacher` class
2. Create a project folder with `pyproject.toml`, source code, and tests
3. Package as `.tar.gz` and publish to AMESA via the AMESA MCP server
4. Return a project ID and version for your records

You can also ask Hicks to publish a new version of an existing agent

### 2: Analyze Performance

Hudson is the Analyst. Use Hudson to analyze agent training or to evaluate performance against benchmarks:

```
"Hudson, analyze this benchmark.json and tell me if we met our goals"
```

Hudson will:

1. Parse benchmark and historian data
2. Evaluate goal adherence (e.g., "Achieved 95% of target throughput")
3. Check constraint violations (e.g., "Latency exceeded 500ms in 3% of runs")
4. Generate actionable recommendations (e.g., "Reduce batch size to improve latency")

You can ask Hudson to:

- Analyze a single benchmark file to understand agent performance
- Analyze a historian file to understand behavior during training
- Compare runs (e.g., v1 vs v2 of an agent)
- Identify performance bottlenecks
- Suggest tuning parameters

## The AMESA Assist Agents Team

Four specialized agents power this workspace:

| Agent      | Role                    | You Ask Them To                                                  |
| ---------- | ----------------------- | ---------------------------------------------------------------- |
| **Hicks**  | Implementation Engineer | Build agents, write code, publish to AMESA                       |
| **Hudson** | Performance Analyst     | Analyze benchmarks, evaluate constraints, recommend improvements |
| **Scribe** | Session Logger          | Maintain project history and documentation                       |
| **Ralph**  | Work Monitor            | Track progress, manage task dependencies                         |

### How to Interact

Use GitHub Copilot CLI to talk to any team member:

```bash
# Talk to Hicks (the Implementation Engineer)
copilot "Hicks, build a SkillTeacher for robotic arm control"

# Talk to Hudson (the Performance Analyst)
copilot "Hudson, analyze ./benchmarks/run_001.json"

# Talk to any team member by name
copilot "Ralph, what's the status of the agent publishing pipeline?"
```

Each agent has specialized tools and knowledge. Be specific about what you need.

## Prerequisites

Before you start, ensure you have:

1. **AMESA MCP connection** — configured in `.mcp.json`:
2. **(Optional) GitHub Copilot CLI** — enables Squad in your workspace

The AMESA MCP server is the communication bridge between your Python code and the AMESA Agent Orchestration Studio.

## Getting Started

### Example 1: Build Your First Agent

```bash
copilot "Hicks, build a SkillTeacher that learns to balance a CartPole given joint_angle, cart_position, and pole_velocity sensors. It should maximize stability over 100 timesteps. Publish to the CartPole use case in MyOrganization."
```

Hicks will create a folder in the workspace, implement the agent, and publish it to AMESA. You'll get back a project ID.

### Example 2: Build a Perceptor

```bash
copilot "Hicks, build a PerceptorImpl that reads raw_pressure and temperature from a hydraulic sensor and outputs normalized_pressure and normalized_temperature."
```

### Example 3: Analyze Agent Performance

```bash
copilot "Hudson, analyze ./benchmarks/agent_v1_run.json. Did we achieve our throughput target and stay within latency bounds?"
```

### Example 4: Compare Versions

```bash
copilot "Hudson, compare the benchmarks from agent_v1 and agent_v2. Which version better satisfies our constraints?"
```

## Repo Structure

```
amesa-agents/
├── README.md                 # This file
├── .mcp.json                 # AMESA MCP server config
├── .squad/                   # Squad team setup
├── agent-context/            # Documentation for agents
├── agents/                   # Examples and your agents
│   └── controllers/
│   └── selectors/
│   └── teachers/
├── perceptors/               # Examples and your perceptors
```

## CLI Reference (Human only)

Use the CLI to create and publish agents and perceptors. You can create new artifacts in code or your agents can create them so that you can review, modify and manually publish them to the AMESA Agent Orchestration Studio. The `amesa` CLI manages the full lifecycle of skills, selectors, and perceptors: scaffolding, publishing, listing, and deleting. All commands follow the pattern `amesa <resource> <subcommand>`.

### Setup Instructions

#### Environment Setup

Python versions allowed: 3.10 <= version < 3.13. Prefer Python 3.11.8.

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

#### Install AMESA

```bash
pip install amesa-cli
```

#### Authentication

Before any CLI operation, authenticate with your Amesa account:

```bash
amesa login
```

This opens your browser to complete the OAuth flow. On success, a token is saved to `~/.amesa/token` and used automatically for all subsequent commands.

---

### Skills

#### Create a new skill scaffold

```bash
amesa skill new \
  --name my-skill \
  --type teacher \
  --description "Short description of what this skill teaches" \
  --location ./
```

| Option          | Short | Default         | Description                                           |
| --------------- | ----- | --------------- | ----------------------------------------------------- |
| `--name`        | `-n`  | `my-skill`      | Name for the skill (used as the outer directory name) |
| `--type`        | `-t`  | _(interactive)_ | Skill type: `controller`, `teacher`                   |
| `--description` | `-d`  | `My demo skill` | Human-readable description                            |
| `--location`    | `-l`  | `./`            | Directory where the scaffold is created               |

If `--type` is omitted, the CLI presents an interactive menu to select the type.

#### Publish a skill

```bash
amesa skill publish ./my-skill/
```

#### List skills in a project

```bash
amesa skill list
```

#### Delete a skill

```bash
amesa skill delete
```

---

### Selectors

Selectors are the agent components that choose which skill to activate at each step. They follow the same artifact structure and lifecycle as skills.

#### Create a new selector scaffold

```bash
amesa selector new \
  --name my-selector \
  --type teacher \
  --description "Short description of what this selector does" \
  --location ./
```

| Option          | Short | Default            | Description                             |
| --------------- | ----- | ------------------ | --------------------------------------- |
| `--name`        | `-n`  | `my-selector`      | Name for the selector                   |
| `--type`        | `-t`  | _(interactive)_    | Selector type: `controller`, `teacher`  |
| `--description` | `-d`  | `My demo selector` | Human-readable description              |
| `--location`    | `-l`  | `./`               | Directory where the scaffold is created |

#### Publish a selector

```bash
amesa selector publish ./my-selector/
```

#### List selectors in a project

```bash
amesa selector list
```

#### Delete a selector

```bash
amesa selector delete
```

---

### Perceptors

#### Create a new perceptor scaffold

```bash
amesa perceptor new \
  --name my-perceptor \
  --description "Short description of what this perceptor computes" \
  --location ./
```

| Option          | Short | Default        | Description                             |
| --------------- | ----- | -------------- | --------------------------------------- |
| `--name`        | `-n`  | `my-perceptor` | Name for the perceptor                  |
| `--description` | `-d`  | _(prompted)_   | Human-readable description              |
| `--location`    | `-l`  | `./`           | Directory where the scaffold is created |

Perceptors have no `--type` option — all perceptors use the same `PerceptorImpl` base class.

#### Publish a perceptor

```bash
amesa perceptor publish ./my-perceptor/
```

#### List perceptors in a project

```bash
amesa perceptor list
```

#### Delete a perceptor

```bash
amesa perceptor delete
```

---

## Extending the Workspace

### Add Benchmarking or Testing

Ask Hudson or Hicks to set up a pipeline:

```bash
copilot "Hudson, let's set up automated benchmark analysis for every agent we publish. How would we do that?"
```

## Support

- **Agent implementation issues**: Ask Hicks
- **Performance analysis questions**: Ask Hudson

Each agent has specialized knowledge and tools.
