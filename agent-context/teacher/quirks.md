# AgentTeacher Quirks

- `compute_success_criteria` can end episodes immediately: the V2 trainer ends the episode when success **or** termination is `True` (`amesa_train/v2/agent_processor_component.py`, `compute_step`).
- If success and termination are both `True` on the same step, the episode does **not** count as a success (`amesa_train/networking/episode_manager.py`: `teacher_success and not teacher_terminated`).
- `is_compute_done()` (base: success AND termination) is not used by the V2 training loop; do not rely on overriding it to end episodes.
- `compute_termination` defaults to `False` (unlike controllers where termination is required).
- Reward/success/termination receive the **previous** action (the one that produced the current observation), and are skipped on the reset step. `transform_sensors` is always called with `action=None`.
- Missing sensor keys plus permissive defaults can create false success.
- `self.action_space` in teacher code does not automatically become trainer action space.
- For trainer action-space override, implement `get_custom_action_space()` — it returns `None` by default (uses sim's action space). When a custom space is returned (a gymnasium space), `transform_action` must map policy output back to the sim's action space.
- `compute_reward` must return a finite real number. Numpy scalars and 1-element arrays are accepted, but `None`, NaN or inf fail `amesa agent validate` (`amesa_core/utils/validate_util.py`, `_is_finite_reward`). Returning `float(...)` is still the safest choice.
- `compute_success_criteria` / `compute_termination` must return a bool (numpy bool / 1-element array is unwrapped); the trainer coerces with `bool()`.
- `filtered_sensor_space()` returns names (`list[str]`), not `Sensor` objects.
- **`filtered_sensor_space()` keys must exist in the sim sensor space or a perceptor's outputs.** The observation space is built from the sensor space filtered by these keys, not from what `transform_sensors` returns. A key you only create inside `transform_sensors` is not a policy input and is reported as missing (`amesa_core/networking/remote_agent/v2/event_agent_processor.py`, `_missing_filter_keys_error`; mock-sim validation: "the sim has no sensors named ..."). Use a perceptor for derived policy inputs.
- `transform_sensors` must keep every filtered key and keep its value's shape consistent with the sensor space; values are flattened with `np.asarray(value).flatten()` (`amesa_core/spaces/box.py`), so plain floats are fine for scalar `Box` sensors.
- Sensors arrive as `np.ndarray` values (usually shape `(1,)`); use `float(x[0])` or `float(x)` when doing scalar math.
- The teacher class must be constructible with no arguments: training calls `impl_cls()` and re-creates the teacher on episode reset (`amesa_train/v2/agent_processor_component.py`, `reset`), so `self.*` state does not survive across episodes. Use `reset()` for per-episode state.
- `compute_scenario_advancement()` values that are invalid (unknown keys, rate outside (0, 1], non-positive window) are silently replaced with the defaults at training time; `amesa agent validate` reports them (`amesa_core/networking/remote_agent/curriculum.py`).
- UI guidance attached to a code teacher overrides the matching hook (`compute_reward`, `compute_success_criteria`, `compute_termination`) and the code's version of that hook is not called (`amesa_core/orchestration/agent/guidance_overrides.py`).
