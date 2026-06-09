# Creating and Publishing Perceptors

This guide walks you through everything you need to build a Perceptor from scratch and publish it to Amesa Orchestration Studio using the `amesa` CLI. By the end, you will have a working perceptor packaged as an artifact and registered in the AMESA registry.

---

## What Is a Perceptor?

A **Perceptor** transforms raw sensor observations into derived, computed features. It sits between the sensor layer and your skills: it receives the raw sensor dictionary, computes new values from it, and injects those new keys into the observation namespace before any skill sees the data.

Skills can reference perceptor outputs the same way they reference sensor names — by listing the key in `filtered_sensor_space()`. Perceptors are registered on the Agent and run for every skill.

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
Perceptor pipeline  (registered order; each adds new keys)
    │  perceptor 1 adds { "efficiency_ratio": 0.91 }
    │  perceptor 2 adds { "quality_index": 0.87 }
    ▼
Skill teachers and controllers  (can reference all keys, including perceptor outputs)
```

---

## Step 1: Understand the Perceptor Methods

A Perceptor is a subclass of `PerceptorImpl` from `amesa_core`. You must implement exactly two methods.

### Required Methods

| Method                       | Sync/Async | What it does                                                                                           |
| ---------------------------- | ---------- | ------------------------------------------------------------------------------------------------------ |
| `compute(obs_spec, obs)`     | **async**  | Called every step. Returns a `dict` of new keys to inject into the observation namespace.              |
| `filtered_sensor_space(obs)` | **sync**   | Returns the list of raw sensor names this perceptor reads. Used for shape inference at initialization. |

> **`filtered_sensor_space` must be sync.** Do **not** declare it `async`. Declaring it async will break space construction at training initialization.

> **`compute` must be async.** Declare it with `async def`.

### Method Signatures

```python
from amesa_core import PerceptorImpl

class MyPerceptor(PerceptorImpl):

    def __init__(self):
        # Must accept zero required arguments
        # All self.* state is wiped at every episode reset
        pass

    async def compute(self, obs_spec, obs) -> dict:
        # obs is the full sensor dict: { "sensor_name": value, ... }
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
| `obs_spec` | `Space \| None` | Gymnasium Space spec. May be `None` in some call paths — do not depend on it being a valid Space object.       |
| `obs`      | `dict`          | The full named sensor dict after lambda extraction, plus outputs from any perceptors that ran before this one. |

**Return value:** a `dict` of new `{ key: value }` pairs. Every key must:

1. **Not** already exist in the observation dict — a collision with an existing sensor name raises an error at training initialization
2. **Match** the `variables` list declared in `pyproject.toml`

> **Episode state:** `__init__` is called fresh at the start of each episode. All `self.*` state is wiped at every episode reset. Do not rely on state persisting across episodes.

---

## Step 2: Write Your Perceptor

The example below computes two derived metrics from raw process sensors: an `efficiency_ratio` (the running fraction of steps where throughput meets a threshold) and a `quality_index` (the ratio of output rate to input rate).

```python
# process_monitor/perceptor.py

from amesa_core import PerceptorImpl


EFFICIENCY_THRESHOLD = 0.75


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
        throughput = obs["throughput"]
        output_rate = obs["output_rate"]
        input_rate = obs["input_rate"]

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
    current = obs["process_var"]
    delta = current - self._last if self._last is not None else 0.0
    self._last = current
    return {"process_var_delta": delta}
```

**Running average:**

```python
async def compute(self, obs_spec, obs) -> dict:
    self._window.append(obs["temperature"])
    if len(self._window) > self._window_size:
        self._window.pop(0)
    return {"temperature_avg": sum(self._window) / len(self._window)}
```

**Threshold flag:**

```python
async def compute(self, obs_spec, obs) -> dict:
    in_spec = 1.0 if 0.08 <= obs["output_metric"] <= 0.09 else 0.0
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
    __init__.py        ← empty; required
    perceptor.py       ← your PerceptorImpl subclass goes here
  pyproject.toml
```

Replace the placeholder `perceptor.py` with your implementation from Step 2.

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
| `__init__.py`       | always empty  | _(no content)_    |

The outer directory is used by the CLI only. The inner snake_case directory is the Python module referenced in `pyproject.toml`. Do not use the kebab-case outer name in your entrypoint — it is not a valid Python identifier.

---

## Step 4: Configure `pyproject.toml`

```toml
[build-system]
requires = ["setuptools"]
build-backend = "setuptools.backends.legacy:build"

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
```

### Field Reference

| Field          | Where       | Required                  | Description                                                                    |
| -------------- | ----------- | ------------------------- | ------------------------------------------------------------------------------ |
| `name`         | `[project]` | Yes                       | Artifact name as it will appear in the registry. Kebab-case.                   |
| `version`      | `[project]` | Yes                       | Semantic version string.                                                       |
| `description`  | `[project]` | Yes                       | Short human-readable description.                                              |
| `dependencies` | `[project]` | Yes                       | Must include `"amesa-core"`.                                                   |
| `type`         | `[amesa]`   | Yes                       | Must be `"perceptor"`.                                                         |
| `entrypoint`   | `[amesa]`   | Yes                       | `inner_module.filename:ClassName`                                              |
| `variables`    | `[amesa]`   | **Yes — perceptors only** | List of output key names. Must exactly match the keys returned by `compute()`. |

> **`variables` is required for perceptors.** This is what the AMESA registry uses to know what named outputs the perceptor exposes. Missing or mismatched `variables` causes publish validation to fail or training initialization to fail.

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
│   ├── __init__.py        ← must exist; must be empty
│   └── perceptor.py       ← contains ProcessMonitorPerceptor class
└── pyproject.toml         ← contains [amesa] section with type, entrypoint, and variables
```

Checklist:

- [ ] `__init__.py` exists and is empty
- [ ] `pyproject.toml` is in the outer directory (same level as `process_monitor/`)
- [ ] `type` in `[amesa]` is `"perceptor"`
- [ ] `variables` list matches the dict keys returned by `compute()`
- [ ] `entrypoint` uses the inner snake_case module name
- [ ] `filtered_sensor_space` is declared `def`, **not** `async def`
- [ ] `compute` is declared `async def`
- [ ] `__init__` takes no required arguments
- [ ] All imports use `from amesa_core import ...`

---

## Step 6: Publish

```bash
amesa perceptor publish ./process-monitor/
```

Or using the flag form:

```bash
amesa perceptor publish --path ./process-monitor/
```

The path must point to the **outer kebab-case directory** containing `pyproject.toml`.

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

## Attaching a Perceptor to an Agent

Once published, a perceptor can also be used in-process (before packaging) while developing:

```python
from amesa_core import Agent, Sensor, Perceptor
from process_monitor.perceptor import ProcessMonitorPerceptor

agent = Agent(id="process-agent")

agent.add_sensors([
    Sensor("throughput",  "Process throughput [0..1]"),
    Sensor("output_rate", "Output units per step"),
    Sensor("input_rate",  "Input units per step"),
])

# Pass the CLASS — not an instance
agent.add_perceptor(Perceptor("process-monitor", ProcessMonitorPerceptor))

# Skills can now reference "efficiency_ratio" and "quality_index"
# in their filtered_sensor_space()
```

Perceptors run in registration order. Each receives the full observation dict including outputs from perceptors that ran before it.

---

## Updating a Published Perceptor

Increment the `version` in `pyproject.toml` and republish:

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

The `variables` list in `[amesa]` must exactly match the dict keys returned by `compute()`. A mismatch causes training initialization to fail when the agent tries to resolve perceptor outputs by name.

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
return {"efficiency": 0.91}     # ✗ wrong key name — training init will fail
```

### `filtered_sensor_space` is async — training fails at init

`filtered_sensor_space` must be a regular synchronous method. Making it `async` breaks the space construction step that runs before training starts.

```python
# WRONG
async def filtered_sensor_space(self, obs) -> list:
    return ["throughput"]

# CORRECT
def filtered_sensor_space(self, obs) -> list:
    return ["throughput"]
```

### Key collision with existing sensor name

If `compute()` returns a key that already exists in the sensor dict, AMESA raises an error at training initialization. Choose output key names that are distinct from all sensor names registered on the Agent.

### Legacy import error

```python
# WRONG
from composabl import PerceptorImpl

# CORRECT
from amesa_core import PerceptorImpl
```
