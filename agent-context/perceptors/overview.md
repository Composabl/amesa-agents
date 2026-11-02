# Perceptors Overview

Perceptors compute derived observation features from mapped sensor values.

They are implemented via `PerceptorImpl` (`amesa_core.orchestration.perceptor.perceptor_impl`, also exported as `from amesa_core import PerceptorImpl`), wrapped in a `Perceptor(name, ImplClass)` and added to the orchestration with `orchestration.add_perceptor(...)`. Each output key is added to the sensor dictionary, so agents receive it in `transformed_sensors` and can list it in their `filtered_sensor_space()`.

Use perceptors when:

- sensor values need feature engineering (derivatives, rolling stats, flags, composite metrics)
- you want reusable per-episode stateful feature transforms across orchestrations

Lifecycle (per SDK code):

- `Perceptor.perceive(obs_spec, obs)` calls `await impl.compute(obs_spec, obs)` once per step (`amesa_core/orchestration/perceptor/perceptor.py`).
- On every episode reset the wrapper drops its instance and builds a new one with `ImplClass()` (`Perceptor.reset`), so `__init__` is the per-episode reset.
- A published perceptor can be rolled over a staged dataset with `amesa data perceive` (MCP: `amesa_data_perceive`); each output is written as a `p_<output>` column of a new dataset (`amesa_compute/api/routes_ml.py`, `amesa_ml/data/loaders/roles.py`).
