# Goals Job JSON Schema

Goals serialize inside an agent's config under `config.impl_cls_data.goals` (`AgentImplDataSchema` in `amesa_core/config/trainer_config.py`; `impl_cls_data` field in `amesa_core/config/agent_config.py`). This is how no-code teachers and guidance are delivered; a code teacher (`remote_address` set) gets its goals from its own Python, and any `impl_cls_data.goals` on it act as guidance overrides (`guidance_overrides.py`).

## Example shape

```json
{
  "agents": [
    {
      "name": "my-agent",
      "config": {
        "impl_cls_data": {
          "guidance": null,
          "goals": [
            {
              "type": "CoordinatedGoal",
              "goals_coordination_strategy": 1,
              "weights": [1, 1],
              "goals": [
                { "type": "ApproachGoal", "sensor_name": "position", "name": "reach", "target": 0.0,
                  "boundary_left": -0.1, "boundary_right": 0.1, "scale": 1.0 },
                { "type": "AvoidGoal", "sensor_name": "velocity", "name": "too fast",
                  "boundary_left": 5.0, "boundary_right": 100.0, "should_terminate_in_boundary": true }
              ]
            }
          ],
          "constraints": null
        }
      }
    }
  ]
}
```

(Shape matches `amesa_train/integration/v2/config/orchestration.json`, where the platform wraps goals in a `CoordinatedGoal`.)

## Fields

- `type` (required): `ApproachGoal`, `AvoidGoal`, `MaintainGoal`, `MaximizeGoal`, `MinimizeGoal`, or `CoordinatedGoal`; any other value raises `ValueError` (`goals/utils.py:from_json`).
- Leaf goals: `sensor_name` (not `sensor`), `name`, `target`, `tolerance`, `stop_value`, `stop_steps`, `boundary_left`, `boundary_right`, `boundary_is_relative`, `scale`, and `should_terminate_in_boundary` (Approach/Avoid).
- `CoordinatedGoal`: `goals` (list, may nest), `goals_coordination_strategy` (int: 1=AND, 2=OR, 3=THEN), `weights`.

## Deserialization gotchas

- `ApproachGoal.from_json` ignores `boundary_is_relative`; `MaximizeGoal`/`MinimizeGoal.from_json` ignore `target`.
- `MaintainGoal.from_json` defaults a missing `scale` to `5.0` (constructor default is `1.0`).
- `AvoidGoal.from_json` treats a missing/`null` `should_terminate_in_boundary` as **terminate** (constructor default is `False`).
- `CoordinatedGoal.from_json` defaults a missing strategy to `OR` (constructor default is `AND`).
- `AgentImplDataSchema` has no `AvoidGoalSchema` branch; Avoid JSON validates as `ApproachGoalSchema` and keeps its `type`, so it still deserializes as `AvoidGoal`.
