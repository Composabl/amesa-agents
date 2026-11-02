# AgentController Job JSON Schema

Controller agents are serialized by `AgentSchema.from_agent` (`amesa_core/amesa_core/config/agent_config.py`) with `type: "AgentController"` and an `AgentControllerOptions` config.

## Core shape

```json
{
  "name": "my-controller-agent",
  "type": "AgentController",
  "config": {
    "remote_address": null,
    "impl_cls": { "cls_name": "MyController", "cls_module": "my_orchestration.controller", "cls_src": "<base64 cloudpickle>", "cls_deps": [] },
    "model_io": {
      "sensor_space": null,
      "action_space": null,
      "custom_action_space": false,
      "custom_sensor_space": false,
      "filtered_sensor_space": [],
      "sim_action_space": null
    },
    "impl_cls_data": { "guidance": null, "goals": [], "constraints": null },
    "scenarios": [],
    "scenarios_current_idx": 0
  }
}
```

## Key meaning

- `impl_cls`: serialized controller class (`SerializerJson.serialize_cls`, cloudpickle + base64). Set only when `remote_address` is null.
- `remote_address`: URL of a published/remote controller; when set, `impl_cls` is null.
- `model_io`: sensor/action spaces and the filtered sensor list (`ModelIOConfig`, `config/trainer_config.py`).
- `impl_cls_data`, `scenarios`, `scenarios_current_idx`: present in the schema with defaults, but `from_agent` does not populate them for controllers, and controllers are instantiated without `impl_cls_data` (`agent.py` `get_impl_cls_instance`).
- No PPO training fields (`learning`, `resources`, `model`) exist on `AgentControllerOptions`.
