# Perceptor Job JSON Schema

Perceptors are serialized in the orchestration JSON `perceptors` list. Each entry is a `PerceptorSchema` (`amesa_core/orchestration/perceptor/perceptor.py`).

## Core shape

```json
{
  "name": "kinematics",
  "description": "Velocity and acceleration from position",
  "impl": { "cls_name": "KinematicsPerceptor", "cls_module": "perceptors_example.perceptor", "cls_src": "<base64 cloudpickle>", "cls_deps": [] },
  "config": "{\"remote_address\": null, \"sensor_space\": null, \"action_space\": null}"
}
```

A published (platform-hosted) perceptor uses `"impl": { "url": "https://.../package.tar.gz" }` instead; `PerceptorSchema.from_json` then sets `config.remote_address` to that URL and the package is downloaded and loaded from its `[amesa].entrypoint`.

## Key meaning

- `name` / `description`: the `Perceptor(...)` wrapper's name and description.
- `impl`: either `CLSSchema` (`cls_name`, `cls_module`, `cls_src`, `cls_deps`; `amesa_core/config/trainer_config.py`) from `SerializerJson.serialize_cls`, or `{ "url": ... }` for a published package.
- `config`: a **JSON string** (not an object) of `PerceptorOptions` (`remote_address`, `sensor_space`, `action_space`).
- There is no `type` or `variables` field in the job JSON; output keys are whatever `compute()` returns at runtime. Declared outputs live in the package's `[amesa].variables` and the platform's perceptor record.
