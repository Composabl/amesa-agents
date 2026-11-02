# AgentController Overview

`AgentController` is for deterministic, hand-authored policies (non-ML).

Use controllers when action logic is explicit (PID/rules/state machine) and you do not want PPO training.

A published controller is an **operational agent** of type `controller` (the CLI strips the `agent-` prefix of the pyproject `type` when it uploads: `amesa_cli/amesa_cli/main/agent.py`, `publish`). Controllers take no guidance.
