# Perceptor Quirks

- `obs` values are numpy arrays, not Python scalars: a scalar sensor arrives as shape `(1,)` float32 in training, inference and `amesa data perceive` (`amesa_core/utils/space_utils.py`, `map_sim_sensors_to_amesa_sensors`; `amesa_core/utils/perceptor_rollout.py`, `_sensor_value`). Extract with `float(np.asarray(v).reshape(-1)[0])`; comparisons on the raw array return arrays.
- `obs` keys are the orchestration's (mapped) sensor names, not raw sim keys. In `amesa data perceive` the lookup is case-insensitive and unmapped `s_` dataset columns lose their prefix (`amesa_cli/dataset/perceive.py`).
- State is per episode automatically: `Perceptor.reset()` discards the instance and the next step builds a new one with `ImplClass()`; `amesa data perceive` also creates a fresh instance per episode. So `__init__` must take no required args, and you do not need your own reset detection.
- A returned key that already exists in the sensor dict raises at the first step (`space_utils.convert_sim_sensors_to_amesa_sensors`; `remote_perceptor/v2/perceptor_component.py`).
- In V2 training, perceptors run concurrently (`asyncio.gather`) on the same sensor dict and outputs are merged afterwards, so a perceptor must not depend on another perceptor's outputs. A perceptor that raises, returns `None` or returns a non-dict is logged and **skipped** — its keys are silently missing that step (`perceptor_component.py`).
- `filtered_sensor_space` is abstract and must be implemented, but no SDK perceptor path calls it; it does not limit what `compute` sees.
- `amesa data perceive` requires each output to be a single value (scalar, size-1 array or 1-element list); outputs named `__row`, two outputs mapping to the same `p_` name, or `p_` names clashing with role columns are rejected (`perceptor_rollout._cell`, `routes_ml.perceive`).
- `[tool.amesa]` is not read; use top-level `[amesa]` (legacy `[composabl]` still accepted).
