# Goals Job JSON Schema

Goals serialize inside a agent's teacher payload under `impl_cls_data.goals`.

## Example shape

```json
{
  "impl_cls_data": {
    "goals": [
      { "type": "ApproachGoal", "sensor_name": "position", "target": 0.0, "tolerance": 0.1 },
      { "type": "AvoidGoal", "sensor_name": "velocity", "boundary_left": -5.0, "boundary_right": 5.0 }
    ]
  }
}
```

Each goal entry includes a `type` discriminator and per-goal config fields.
