# Creating and Publishing Perceptors

This guide walks you through everything you need to build a Perceptor from scratch and publish it to Amesa Orchestration Studio using the `amesa` CLI. By the end, you will have a working perceptor packaged as an artifact and registered in the AMESA registry.

---

## What Is a Perceptor?

A **Perceptor** transforms raw sensor observations into derived, computed features. It sits between the sensor layer and your agents: it receives the raw sensor dictionary, computes new values from it, and injects those new keys into the observation namespace before any agent sees the data.

Agents can reference perceptor outputs the same way they reference sensor names — by listing the key in `filtered_sensor_space()`. Perceptors are registered on the Orchestration and run once per step, before any agent sees the observation.

**Common use cases:**

- Rate-of-change / derivative of a sensor value
- Running averages and sliding-window statistics
- Threshold flags (is this sensor in spec?)
- Composite metrics derived from two or more sensors

### Data Flow

```
Simulator
    │ raw observations
    ▼
Sensor mapping  →  { "temperature": 82.3, "pressure": 1.1, ... }
    │
    ▼
Perceptors  (each adds new keys; see note on ordering below)
    │  perceptor 1 adds { "efficiency_ratio": 0.91 }
    │  perceptor 2 adds { "quality_index": 0.87 }
    ▼
Agent teachers and controllers  (can reference all keys, including perceptor outputs)
```

---

## Step 1: Understand the Perceptor Methods

A Perceptor is a subclass of `PerceptorImpl` from `amesa_core`. You must implement exactly two methods.

### Required Methods

| Method                       | Sync/Async | What it does                                                                                           |
| ---------------------------- | ---------- | ------------------------------------------------------------------------------------------------------ |
| `compute(obs_spec, obs)`     | **async**  | Called every step. Returns a `dict` of new keys to inject into the observation namespace.              |
| `filtered_sensor_space(obs)` | **sync**   | Returns the list of sensor names this perceptor reads. Abstract (must exist), but not called by the SDK on perceptors today. |

> **`compute` must be async.** Declare it with `async def` — `amesa perceptor validate` rejects a sync `compute`.

> **`filtered_sensor_space` is sync** in the base class. Keep it a plain `def`.

### Method Signatures

```python
from amesa_core import PerceptorImpl

class MyPerceptor(PerceptorImpl):

    def __init__(self):
        # Must accept zero required arguments
        # A fresh instance is created at every episode reset
        pass

    async def compute(self, obs_spec, obs) -> dict:
        # obs is the sensor dict: { "sensor_name": np.array([value]), ... }
        # Return a dict of NEW keys to add to the observation namespace
        ...

    def filtered_sensor_space(self, obs) -> list:
        # Return the list of sensor names this perceptor reads
        # Note: sync, not async
        ...
```

### The `compute()` Parameters

| Parameter  | Type            | Description                                                                                                    |
| ---------- | --------------- | -------------------------------------------------------------------------------------------------------------- |
| `obs_spec` | `Space \| None` | The sim's sensor space. May be `None` (always `None` in `amesa data perceive`) — do not depend on it. |
| `obs`      | `dict`          | Orchestration sensor name → value after sensor mapping. Values are **numpy arrays** (a scalar sensor is shape `(1,)` float32), not Python floats. |

**Return value:** a `dict` of new `{ key: value }` pairs. Every key must:

1. **Not** already exist in the observation dict — a collision with an existing sensor name raises an error on the first step
2. **Match** the `variables` list declared in `pyproject.toml` (the platform registers these as the perceptor's sensors on publish)

Each value should be a single number (a size-1 array is fine).

> **Episode state:** on every episode reset the runtime discards the instance and calls `__init__` again (`Perceptor.reset()` in `amesa_core`). Do not rely on state persisting across episodes.

> **Ordering:** in training, perceptors run concurrently and their outputs are merged afterwards, so one perceptor must not read another perceptor's outputs. A perceptor that raises is logged and skipped for that step — its keys are silently missing.

---

## Step 2: Write Your Perceptor

The example below computes two derived metrics from raw process sensors: an `efficiency_ratio` (the running fraction of steps where throughput meets a threshold) and a `quality_index` (the ratio of output rate to input rate).

```python
# process_monitor/perceptor.py

import numpy as np

from amesa_core import PerceptorImpl


EFFICIENCY_THRESHOLD = 0.75


def _scalar(value) -> float:
    # Sensors arrive as numpy arrays of shape (1,)
    return float(np.asarray(value).reshape(-1)[0])


class ProcessMonitorPerceptor(PerceptorImpl):
    """
    Computes two derived metrics from raw process sensors.

    Reads:   throughput, output_rate, input_rate
    Outputs: efficiency_ratio, quality_index
    """

    def __init__(self):
        # __init__ must take no required arguments
        # State is reset at the start of every episode
        self._total_steps = 0
        self._efficient_steps = 0

    async def compute(self, obs_spec, obs) -> dict:
        throughput = _scalar(obs["throughput"])
        output_rate = _scalar(obs["output_rate"])
        input_rate = _scalar(obs["input_rate"])

        self._total_steps += 1
        if throughput >= EFFICIENCY_THRESHOLD:
            self._efficient_steps += 1

        efficiency_ratio = self._efficient_steps / self._total_steps
        quality_index = min(1.0, output_rate / input_rate) if input_rate > 0 else 0.0

        return {
            "efficiency_ratio": efficiency_ratio,
            "quality_index": quality_index,
        }

    def filtered_sensor_space(self, obs) -> list:
        # Sync — not async
        return ["throughput", "output_rate", "input_rate"]
```

### Common `compute()` Patterns

**Step-over-step delta (derivative):**

```python
async def compute(self, obs_spec, obs) -> dict:
    current = _scalar(obs["process_var"])
    delta = current - self._last if self._last is not None else 0.0
    self._last = current
    return {"process_var_delta": delta}
```

**Running average:**

```python
async def compute(self, obs_spec, obs) -> dict:
    self._window.append(_scalar(obs["temperature"]))
    if len(self._window) > self._window_size:
        self._window.pop(0)
    return {"temperature_avg": sum(self._window) / len(self._window)}
```

**Threshold flag:**

```python
async def compute(self, obs_spec, obs) -> dict:
    in_spec = 1.0 if 0.08 <= _scalar(obs["output_metric"]) <= 0.09 else 0.0
    return {"in_spec_flag": in_spec}
```

---

## Step 3: Create the Artifact Directory

### Using the CLI Scaffold (Recommended)

```bash
amesa perceptor new \
  --name process-monitor \
  --description "Computes efficiency_ratio and quality_index from process sensors" \
  --location ./
```

This creates:

```text
process-monitor/
  process_monitor/
    __init__.py
    perceptor.py       ← DemoPerceptor placeholder; replace with your class
  pyproject.toml
  README.md
```

Replace the placeholder `perceptor.py` with your implementation from Step 2, and update `entrypoint` and `variables` in `pyproject.toml` (the template points at `DemoPerceptor` and declares `counter_derived`).

### Creating Manually

```bash
mkdir -p process-monitor/process_monitor
touch process-monitor/process_monitor/__init__.py
touch process-monitor/process_monitor/perceptor.py
touch process-monitor/pyproject.toml
```

### Naming Rules

| Layer               | Convention    | Example           |
| ------------------- | ------------- | ----------------- |
| Outer directory     | kebab-case    | `process-monitor` |
| Inner Python module | snake_case    | `process_monitor` |
| Source file         | by convention | `perceptor.py`    |
| `__init__.py`       | required      | _(may be empty)_  |

The outer directory is used by the CLI only. The inner snake_case directory is the Python module referenced in `pyproject.toml`. Do not use the kebab-case outer name in your entrypoint — it is not a valid Python identifier.

---

## Step 4: Configure `pyproject.toml`

```toml
[project]
name = "process-monitor"
version = "0.1.0"
description = "Computes efficiency_ratio and quality_index from process sensors"
dependencies = [
    "amesa-core",
]

[amesa]
type = "perceptor"
entrypoint = "process_monitor.perceptor:ProcessMonitorPerceptor"
variables = ["efficiency_ratio", "quality_index"]
inputs = ["throughput", "output_rate", "input_rate"]
```

Use a top-level `[amesa]` table — **not** `[tool.amesa]`, which the loader does not read (legacy `[composabl]` is still accepted).

### Field Reference

| Field          | Where       | Required                  | Description                                                                    |
| -------------- | ----------- | ------------------------- | ------------------------------------------------------------------------------ |
| `name`         | `[project]` | Yes                       | Artifact name as it will appear in the registry. Kebab-case.                   |
| `version`      | `[project]` | Yes                       | Semantic version string.                                                       |
| `description`  | `[project]` | Recommended               | Short human-readable description (used as the registry description).          |
| `dependencies` | `[project]` | Recommended               | Include `"amesa-core"` plus anything `compute()` imports (installed at validation/run time). |
| `type`         | `[amesa]`   | Yes                       | Must be `"perceptor"`.                                                         |
| `entrypoint`   | `[amesa]`   | Yes                       | `inner_module.filename:ClassName`                                              |
| `variables`    | `[amesa]`   | **Yes — perceptors only** | List of output key names. Must exactly match the keys returned by `compute()`. |
| `inputs`       | `[amesa]`   | Optional                  | Sensor names `compute()` reads. `amesa data perceive` checks them against the dataset before running. |

> **`variables` is required for perceptors.** The SDK loader does not check it, but the platform publish tools (`perceptor_create`, `perceptor_implementation_publish`) take the perceptor's sensors exclusively from `[amesa].variables`. Keep it equal to the keys `compute()` returns — agents select perceptor outputs by name.

### Entrypoint Format

| Part           | Value in this example                           |
| -------------- | ----------------------------------------------- |
| `inner_module` | `process_monitor` (inner snake_case directory)  |
| `filename`     | `perceptor` (the `.py` file, without extension) |
| `ClassName`    | `ProcessMonitorPerceptor`                       |

**Full entrypoint:** `process_monitor.perceptor:ProcessMonitorPerceptor`

---

## Step 5: Verify Your Directory

```text
process-monitor/
├── process_monitor/
│   ├── __init__.py        ← must exist
│   └── perceptor.py       ← contains ProcessMonitorPerceptor class
└── pyproject.toml         ← contains [amesa] section with type, entrypoint, and variables
```

Checklist:

- [ ] `__init__.py` exists
- [ ] `pyproject.toml` is in the outer directory (same level as `process_monitor/`)
- [ ] `pyproject.toml` uses top-level `[amesa]`, not `[tool.amesa]`
- [ ] `type` in `[amesa]` is `"perceptor"`
- [ ] `variables` list matches the dict keys returned by `compute()`
- [ ] `entrypoint` uses the inner snake_case module name
- [ ] `compute` is declared `async def`
- [ ] `filtered_sensor_space` is implemented (plain `def`)
- [ ] sensor values are unwrapped from numpy arrays before scalar math
- [ ] `amesa perceptor validate ./process-monitor/` reports no issues
- [ ] `__init__` takes no required arguments
- [ ] All imports use `from amesa_core import ...`

---

## Step 6: Validate and Publish

```bash
amesa perceptor validate ./process-monitor/
```

This installs the declared dependencies in isolation, loads the entrypoint, and checks it subclasses `PerceptorImpl` with both methods implemented and `compute` async.

```bash
amesa perceptor publish ./process-monitor/
```

Or using the flag form:

```bash
amesa perceptor publish --path ./process-monitor/
```

The path must point to the **outer kebab-case directory** containing `pyproject.toml`. The CLI prompts for the project (use case). If a perceptor with the same `[project].name` already exists there, the upload becomes its next version.

### Publishing via the AMESA MCP tools

1. `organization_list` → `use_case_list` to get the `projectId`.
2. First version: `perceptor_create` with `name`, `description` and `sensors` = `[amesa].variables`. Later versions: `perceptor_implementation_publish` with `perceptorId` and `sensors`.
3. PUT the `.tar.gz` of the outer directory to the returned `uploadUrl` (with the returned headers), then call `perceptor_confirm_upload` with the `implementationId`.
   (Alternatively `submit_code_file` with `artifactType: "perceptor"` and `perceptorSensors` packages the files into a new version.)
4. `amesa_perceptor_validate` → poll the jobId with `component_validation_status`.
5. `perceptor_list` / `perceptor_get` to confirm and record the perceptor and implementation IDs.

---

## Step 7: Confirm the Publish

```bash
amesa perceptor list
```

This prints a table of all perceptors in the selected project:

| Name            | Version | Description                                    | UUID |
| --------------- | ------- | ---------------------------------------------- | ---- |
| process-monitor | 1       | Computes efficiency_ratio and quality_index... | ...  |

---

## Attaching a Perceptor to an Orchestration

Once published, a perceptor can also be used in-process (before packaging) while developing:

```python
from amesa_core import Orchestration, Sensor, Perceptor
from process_monitor.perceptor import ProcessMonitorPerceptor

orchestration = Orchestration()

orchestration.add_sensors([
    Sensor("throughput",  "Process throughput [0..1]"),
    Sensor("output_rate", "Output units per step"),
    Sensor("input_rate",  "Input units per step"),
])

# Pass the CLASS — not an instance
orchestration.add_perceptor(Perceptor("process-monitor", ProcessMonitorPerceptor))

# Agents can now reference "efficiency_ratio" and "quality_index"
# in their filtered_sensor_space()
```

Do not make one perceptor depend on another's outputs: in training perceptors run concurrently on the same sensor dict and outputs are merged after all finish (local inference runs them sequentially, so behavior would differ).

---

## Trying a Perceptor on a Dataset

```bash
amesa data perceive <dataset> --use-case <use-case> --perceptor process-monitor --version latest --name <new-dataset>
```

(MCP: `amesa_data_perceive`.) Rolls the published perceptor over a staged dataset, one fresh instance per episode, and writes each output as a `p_<output>` column of a new dataset; the source is untouched. `p_` columns hold no role: `amesa data score`, `integrity` and `stats` count them, training ignores them.

---

## Updating a Published Perceptor

Republish; the platform numbers the new version automatically (bumping `[project].version` is still good practice):

```bash
amesa perceptor publish ./process-monitor/
```

## Deleting a Perceptor

```bash
amesa perceptor delete
```

The CLI presents an interactive list. Select the perceptor to remove and confirm.

---

## Troubleshooting

### Output keys don't match `variables` in `pyproject.toml`

The `variables` list in `[amesa]` must exactly match the dict keys returned by `compute()`. The platform registers `variables` as the perceptor's sensors; an agent that selects a declared name `compute()` never returns trains without that input (unknown `filtered_sensor_space()` keys are reported as missing).

```toml
# pyproject.toml declares:
variables = ["efficiency_ratio", "quality_index"]
```

```python
# compute() must return exactly these keys:
return {
    "efficiency_ratio": 0.91,   # ✓ matches
    "quality_index": 0.87,      # ✓ matches
}

# NOT:
return {"efficiency": 0.91}     # ✗ wrong key name — agents won't find "efficiency_ratio"
```

### `compute` is not async — validation fails

`amesa perceptor validate` reports `does not mark method 'compute' as async as required by 'PerceptorImpl'`.

```python
# WRONG
def compute(self, obs_spec, obs) -> dict: ...

# CORRECT
async def compute(self, obs_spec, obs) -> dict: ...
```

### Math on sensor values behaves oddly

Sensor values are numpy arrays of shape `(1,)`. Unwrap them (`float(np.asarray(v).reshape(-1)[0])`) before comparisons, `min`/`max`, or appending to Python lists.

### Key collision with existing sensor name

If `compute()` returns a key that already exists in the sensor dict, AMESA raises `Perceptor X has a key Y that already exists in the sensor space dictionary!` on the first step. Choose output key names that are distinct from all sensor names registered on the Orchestration.

### Legacy import error

```python
# WRONG
from composabl import PerceptorImpl

# CORRECT
from amesa_core import PerceptorImpl
```
