# Coordinated Quirks

- Reward dict key mismatches to child skill names break per-child training flow.
- Success/termination are global to the coordinated unit, not per-child.
- `THEN`/ordering-like logic should be encoded explicitly in coach logic; the runtime will not infer orchestration intent.
