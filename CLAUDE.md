# AMESA Build — Claude Instructions

## Agent Delegation

Spawn specialist subagents proactively when the task matches their domain — do not wait for the user to ask:

| Task | Agent |
|------|-------|
| Implementing `SkillTeacher`, `SkillController`, or `PerceptorImpl` in Python | `hicks` |
| Publishing agents/perceptors to AMESA Agent Orchestration Studio via MCP | `hicks` |
| Translating a control objective description into runnable Python | `hicks` |
| Analyzing benchmark.json or historian parquet files | `hudson` |
| Assessing goal/constraint adherence or training performance trends | `hudson` |
| Triaging GitHub issues or checking what needs attention on the board | `ralph` |

When a task clearly matches one of the above, spawn the agent first — don't build it inline.
