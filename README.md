# AMESA Agent Orchestration Workspace

This is an AI-assisted workspace for building, publishing, and analyzing intelligent control agents using the **AMESA Agent Orchestration Studio**.

## What Is This Repo?

`amesa-agents` is a collaborative development environment where you define control objectives and let the Squad AI team implement and deploy them. You write natural language specifications, and your AI team:

- Implements Python agents (`SkillTeacher`, `SkillController`, `PerceptorImpl`)
- Publishes to the AMESA Agent Orchestration Studio
- Analyzes performance against benchmarks
- Recommends improvements

This is not a library — it's your workspace.

## What Is AMESA?

**AMESA Agent Orchestration Studio** is a platform for:

- **Building** intelligent control agents that learn and adapt
- **Publishing** agents to managed environments with version control
- **Training** agents in simulation
- **Monitoring** performance with structured data (benchmarks, historian logs)

AMESA handles the infrastructure; your Squad AI team handles the implementation.

## Core Workflows

### Workflow 1: Build & Publish Agents

Hicks is the Implementation Engineer. Use Hicks to implement agents in Python, then publish to AMESA:

```
"Hicks, build a SkillTeacher that learns to optimize [control objective] given [sensor inputs]"
```

Hicks will:

1. Implement a `SkillTeacher` class (PyTorch + agent framework)
2. Create a project folder with `pyproject.toml`, source code, and tests
3. Package as `.tar.gz` and publish to AMESA via the AMESA MCP server
4. Return a project ID and version for your records

You can also ask Hicks to:

- Build a `SkillController` (deterministic or rule-based control logic)
- Implement a `PerceptorImpl` (sensor data parsing and interpretation)
- Publish a new version of an existing agent

### Workflow 2: Analyze Performance

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

## Your Squad AI Team

Four specialized agents power this workspace:

| Agent      | Role                    | You Ask Them To                                                  |
| ---------- | ----------------------- | ---------------------------------------------------------------- |
| **Hicks**  | Implementation Engineer | Build agents, write code, publish to AMESA                       |
| **Hudson** | Performance Analyst     | Analyze benchmarks, evaluate constraints, recommend improvements |
| **Scribe** | Session Logger          | Maintain project history and documentation                       |
| **Ralph**  | Work Monitor            | Track progress, manage task dependencies                         |

### How to Interact

Use GitHub Copilot CLI to talk to any Squad member:

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

1. **Python 3.8+** — installed and in your PATH
2. **AMESA Account** — with an organization and API token
3. **AMESA MCP connection** — configured in `.mcp.json`:
   ```json
   {
     "mcpServers": {
       "amesa": {
         "type": "http",
         "url": "https://api.amesa.com/v1/mcp",
         "tools": ["*"]
       }
     }
   }
   ```
4. **GitHub Copilot CLI** — with Squad enabled in your workspace

The AMESA MCP server is the communication bridge between your Python code and the AMESA Agent Orchestration Studio.

## Getting Started

### Example 1: Build Your First Agent

```bash
copilot "Hicks, build a SkillTeacher that learns to balance a CartPole given joint_angle, cart_position, and pole_velocity sensors. It should maximize stability over 100 timesteps. Publish to the CartPole use case in my organization."
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

## Project Structure

```
amesa-agents/
├── README.md                 # This file
├── .mcp.json                 # AMESA MCP server config
├── .squad/
│   ├── team.md              # Squad team definitions
│   ├── decisions.md          # Team decisions and governance
│   └── agents/
│       ├── hicks/           # Hicks's project context
│       ├── hudson/          # Hudson's project context
│       ├── scribe/          # Scribe's project context
│       └── ralph/           # Ralph's project context
├── projects/                # Your agent projects (created by Hicks)
│   └── [project-id]/
│       ├── pyproject.toml
│       ├── src/
│       └── tests/
└── benchmarks/              # Benchmark files (analyzed by Hudson)
    └── *.json
```

When Hicks builds an agent, it creates a subfolder in `projects/` with the implementation.

## Extending the Workspace

### Add a New Agent Type

If you need a different kind of agent (beyond SkillTeacher, SkillController, PerceptorImpl), ask Hicks:

```bash
copilot "Hicks, we need a [new agent type] that does [what]. Can you design and implement it?"
```

### Add Benchmarking or Testing

Ask Hudson or Hicks to set up a pipeline:

```bash
copilot "Hudson, let's set up automated benchmark analysis for every agent we publish. How would we do that?"
```

## Support

- **Agent implementation issues**: Ask Hicks
- **Performance analysis questions**: Ask Hudson
