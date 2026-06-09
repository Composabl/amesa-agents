# Goals Quirks

- `ApproachGoal`/`MaintainGoal` boundary bonuses require both boundaries.
- `MaintainGoal`, `MaximizeGoal`, and `MinimizeGoal` do not inherently produce success.
- `AvoidGoal` does not produce success; it contributes via reward/termination.
- In `CoordinatedGoal`, mismatched `weights` length raises an error.
- Goal chaining with non-terminating goals can stall staged progress.
