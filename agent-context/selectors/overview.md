# Selector Overview

`SkillSelector` chooses one child skill per step and routes execution to that selected child.

## What a selector does

- Builds a selector action space of `Discrete(len(children))`.
- Produces a child index (0-based) via selector logic.
- Executes the selected child skill and returns the **child action**.

## Selector implementation modes

- **Teacher selector** (`SkillSelector`): ML policy learns which child to choose.
- **Controller selector** (`SkillSelectorController`): deterministic logic chooses child index.

## SDK compliance essentials

- Selector must have at least one child skill.
- `children` must be skill names that exist in the agent graph.
- Selector output must resolve to a valid child index (`0..len(children)-1`).
- Portable package type must be:
  - `selector-teacher` for teacher selectors
  - `selector-controller` for controller selectors
