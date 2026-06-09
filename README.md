# AMESA Agent Orchestration Workspace

This is an AI-assisted workspace for building, publishing, and analyzing intelligent control agents using the **AMESA Agent Orchestration Studio**.

---

## Table of Contents

- [What Is This Repo?](#what-is-this-repo)
- [What Is AMESA?](#what-is-amesa)
- [The Squad AI Team](#the-squad-ai-team)
- [Prerequisites](#prerequisites)
- [Getting Started](#getting-started)
- [Core Capabilities](#core-capabilities)
- [Repo Structure](#repo-structure)
- [CLI Reference](#cli-reference)
  - [Setup](#setup)
  - [Skills](#skills)
  - [Selectors](#selectors)
  - [Perceptors](#perceptors)
- [Extending the Workspace](#extending-the-workspace)
- [Support](#support)

---

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

## The Squad AI Team

Four specialized agents power this workspace:

| Agent      | Role                    | You Ask Them To                                                  |
| ---------- | ----------------------- | ---------------------------------------------------------------- |
| **Hicks**  | Implementation Engineer | Build agents, write code, publish to AMESA                       |
| **Hudson** | Performance Analyst     | Analyze benchmarks, evaluate constraints, recommend improvements |
| **Scribe** | Session Logger          | Maintain project history and documentation                       |
| **Ralph**  | Work Monitor            | Track progress, manage task dependencies                         |

Use GitHub Copilot CLI to talk to any team member by name:

```
"Hicks, build a SkillTeacher for robotic arm control"
"Hudson, analyze ./benchmarks/run_001.json"
```

Each agent has specialized tools and knowledge. Be specific about what you need.

## Prerequisites

Before you start, ensure you have:

1. **AMESA account** — sign up at [amesa.com](https://amesa.com) to get access to the Agent Orchestration Studio.
2. **AMESA MCP connection** — the `.mcp.json` file in this repo is pre-configured to point at `https://api.amesa.com/v1/mcp`. The AMESA MCP server is the communication bridge between this workspace and the AMESA Agent Orchestration Studio.
3. **(Optional) GitHub Copilot CLI** — enables the Squad AI team in your workspace.

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

## Core Capabilities

### Build & Publish Agents

**Hicks** is the Implementation Engineer. Use Hicks to implement agents in Python, then publish to AMESA:

```
"Hicks, build a SkillTeacher that learns to optimize [control objective] given [sensor inputs]"
```

Hicks will:

1. Implement the appropriate class (`SkillTeacher`, `SkillController`, `SkillSelector`, `SkillSelectorController`, or `PerceptorImpl`)
2. Create a project folder with `pyproject.toml`, source code, and tests
3. Package as `.tar.gz` and publish to AMESA via the AMESA MCP server
4. Return a project ID and version for your records

You can also ask Hicks to publish a new version of an existing agent.

### Analyze Performance

**Hudson** is the Analyst. Use Hudson to analyze agent training or evaluate performance against benchmarks:

```
"Hudson, analyze this benchmark.json and tell me if we met our goals"
```

Hudson will:

1. Parse benchmark and historian data
2. Evaluate goal adherence (e.g., "Achieved 95% of target throughput")
3. Check constraint violations (e.g., "Latency exceeded 500ms in 3% of runs")
4. Generate actionable recommendations (e.g., "Reduce batch size to improve latency")

Hudson can also compare runs (v1 vs v2), identify bottlenecks, and suggest tuning parameters.

## Repo Structure

```
amesa-agents/
├── AGENTS.md                 # AI agent guidelines (read this if you're an AI agent)
├── README.md                 # This file
├── .mcp.json                 # AMESA MCP server config
├── .squad/                   # Squad AI team definitions (Hicks, Hudson, Scribe, Ralph)
├── agent-context/            # Component specs for AI agents to read before implementing
│   ├── teacher/              #   SkillTeacher interface, publishing, and quirks
│   ├── controller/           #   SkillController interface, publishing, and quirks
│   ├── selectors/            #   SkillSelector / SkillSelectorController specs
│   ├── perceptors/           #   PerceptorImpl specs
│   ├── goals/                #   Goal types and coordinated goals
│   └── analysis/             #   Benchmark JSON and historian data formats
├── agents/                   # Your implemented agent artifacts
│   ├── controllers/
│   ├── selectors/
│   └── teachers/
└── perceptors/               # Your implemented perceptor artifacts
```

## CLI Reference

The `amesa` CLI lets you scaffold, publish, list, and delete skills, selectors, and perceptors without going through the AI team. Use it when you want to review or modify generated artifacts before publishing, or when you prefer direct control over the publish lifecycle. All commands follow the pattern `amesa <resource> <subcommand>`.

> **AI agents:** The AMESA MCP tools in this workspace handle publishing automatically. The CLI is primarily for human operators.

### Setup

**Python:** 3.10–3.12 (prefer 3.11.8)

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install amesa-cli
```

**Authentication** — before any CLI operation, authenticate with your AMESA account:

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

### Add a New Agent Type

Ask Hicks to scaffold and publish any supported component:

```bash
copilot "Hicks, build a SkillSelectorController that switches between a heating skill and a cooling skill based on temperature thresholds."
```

### Add Benchmarking or Testing

Ask Hudson or Hicks to set up an analysis pipeline:

```bash
copilot "Hudson, let's set up automated benchmark analysis for every agent we publish. How would we do that?"
```

### Customize the Squad

Edit `.squad/agents/<name>/charter.md` to change how a team member behaves, what tools they use, or what they prioritize.

---

## Support

- **Agent implementation issues** — ask Hicks
- **Performance analysis questions** — ask Hudson
- **AI agent coding guidelines** — see [`AGENTS.md`](./AGENTS.md)
- **Component specs and interfaces** — see [`agent-context/`](./agent-context/)
