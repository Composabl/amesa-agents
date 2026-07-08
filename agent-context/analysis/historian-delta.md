# Historian Delta Lake

The historian captures a stream of telemetry events emitted by the SDK during training and writes them to a [Delta Lake](https://delta.io/) table. Each run produces a folder named after the `run_id` containing Parquet data files and a `_delta_log/` transaction log. Delta Lake is an ACID-compliant storage layer built on Parquet — any tool that reads Delta Lake (Python `deltalake`, Spark, DuckDB, pandas via `deltalake.to_pyarrow_table()`) can query the data.

The historian container (`composabl/historian`) listens on an MQTT broker, batches incoming events, and writes them to the configured `STORAGE_PATH`. Events are sent from the SDK via the `TelemetryHistorian` singleton's `sink()` method.

---

## Starting the historian

```bash
amesa historian start [--output-path /path/to/output]
```

If `--output-path` is omitted, the current working directory is used. This command starts two Docker containers — an EMQX MQTT broker (`composabl-emqx`) and the historian sink (`composabl-historian`). The SDK connects to the broker automatically when the `moniker_mqtt` is set in the trainer configuration.

Check the status of running containers:

```bash
amesa historian status
```

Stop and clean up:

```bash
amesa historian stop
amesa historian clean
```

---

## Output directory layout

```
<output_path>/
  <run_id>/
    _delta_log/
      00000000000000000000.json   ← commit 0 (schema + first write)
      00000000000000000001.json   ← subsequent commits
      ...
    part-00000-<uuid>-c000.snappy.parquet
    part-00001-<uuid>-c000.snappy.parquet
    ...
```

Each `part-*.snappy.parquet` file contains a batch of rows. Files are Snappy-compressed Parquet. The `_delta_log/` directory contains one JSON commit file per write operation and is required for Delta Lake reads — do not delete it.

To read the table in Python:

```python
from deltalake import DeltaTable

dt = DeltaTable("/path/to/output/run-abc123")
table = dt.to_pyarrow_table()

# Filter to a specific category
import pyarrow.compute as pc
env_steps = table.filter(pc.equal(table["category"], "env-step"))
```

---

## Table schema

Every row represents one telemetry event emitted by the SDK.

| Column | Type | Description |
|---|---|---|
| `run_id` | `string` | Identifies the training run. Matches the `run_id` passed to `TelemetryHistorian.enable()`. Used to correlate events across workers and components. |
| `source` | `string` | Which component emitted the event. `"sdk"` for all standard SDK events. Remote agents or controllers may use a different source string. |
| `category` | `string` | High-level event category. See the [Event catalog](#event-catalog) section for all known values. |
| `category_sub` | `string` | Sub-category that narrows the event type within a `category`. Together with `category` this uniquely identifies the event type. |
| `data` | `string` | JSON-encoded payload for the event. The schema of this object varies by `category`/`category_sub`. Must be parsed with `json.loads()`. |
| `timestamp` | `string` | ISO 8601 timestamp of when the event was emitted (UTC). Format: `2026-05-27T09:00:01.000+00:00`. |

---

## Event catalog

### `trainer-lifecycle`

Emitted by the `Trainer` and `AgentTrainer` during initialization and training loop management.

| `category_sub` | When emitted | Notable `data` fields |
|---|---|---|
| `validation-start` | Before training begins; after the orchestration graph is validated. | `all_agent` (list of agent names), `training_order` (ordered list) |
| `validation-agent-result` | After each agent is validated. | `agent_name`, `agent_type`, validation errors if any |
| `validation-complete` | After full orchestration validation. | `success` (bool), `errors` (list) |
| `agent-transition` | When the trainer moves from one agent to the next in the training order. | `agent_name`, `agent_sequence_idx` |
| `initialized` | After `Trainer.__init__` completes. | `target` (target type: `"local"`, `"docker"`, etc.) |

### `agent-trainer`

Emitted by `AgentTrainer` (the per-agent PPO wrapper).

| `category_sub` | When emitted | Notable `data` fields |
|---|---|---|
| `checkpoint-check` | Before loading or initializing the policy. | `agent_name`, `checkpoint_uri`, `checkpoint_dir_exists`, `checkpoint_contents` (list of files) |
| `checkpoint-restored` | When a prior checkpoint is successfully loaded. | `agent_name`, `checkpoint_uri`, `restored: true` |
| `checkpoint-restore-failed` | When checkpoint loading throws. | `agent_name`, `checkpoint_uri`, `error` (exception message) |
| `checkpoint-dir-missing` | When a checkpoint URI is set but the directory is absent. | `agent_name`, `checkpoint_uri` |
| `checkpoint-none` | When no checkpoint is configured; training from scratch. | `agent_name`, `starting_from_scratch: true` |

### `env-lifecycle`

Emitted by the RLlib environment wrapper (`Env`) for each worker environment instance. One environment instance is created per rollout worker per parallel env.

| `category_sub` | When emitted | Notable `data` fields |
|---|---|---|
| `constructor` | When the environment object is instantiated. | `sim_id`, `run_id`, `agent_name`, `agent_type`, `is_orchestrator` |
| `sim-spaces-loaded` | After the sim's `sensor_space_info()` and `action_space_info()` have been retrieved. | `sim_id`, `address`, `sim_sensor_space` (string repr), `sim_action_space` (string repr) |
| `create-client-complete` | After a gRPC/WebSocket client connection to the sim is established. | `sim_id`, `address`, `agent_name`, `agent_type` |
| `reset-start` | At the beginning of each episode reset. | `sim_id`, `episode_number`, `agent_name`, `needs_warmup` |
| `reset-sim-returned` | After the sim's `reset()` call returns. | `sim_id`, `episode_number`, `sim_sensors` (raw obs), `info` |
| `reset-warmup-complete` | After warmup steps finish (if the agent has a warmup phase). | `sim_id`, `episode_number`, `warmup_retries`, `sim_sensors_post_warmup` |
| `reset-complete` | After the full reset pipeline completes, sensors transformed and filtered. | `sim_id`, `episode_number`, `amesa_sensors_filtered`, `unfiltered_obs` |

### `env-step`

Emitted by the RLlib environment wrapper for each step within an episode. Multiple sub-events fire per step.

| `category_sub` | When emitted | Notable `data` fields |
|---|---|---|
| `start` | At the beginning of each step before any processing. | `sim_id`, `episode_number`, `agent_name`, `step_number`, `is_orchestrator` |
| `orchestrator-pre-process` | For orchestrator agents: before the orchestrator resolves the child action. | `sim_id`, `orchestrator_action_from_ray`, `prev_sim_sensors`, `prev_amesa_obs` |
| `orchestrator-post-process` | For orchestrator agents: after the child action is resolved. | `sim_id`, `orchestrator_action_index`, `child_action_processed` |
| `orchestrator-validation-action` | For orchestrator agents in validation mode. | `sim_id`, `action_processed` |
| `action-processed` | After the teacher's `transform_action()` runs. | `sim_id`, `raw_action`, `action_processed` |
| `action-coerced` | After the action is coerced to the sim's action space. | `sim_id`, `action_before_coerce`, `action_after_coerce` |
| `sim-step-returned` | After the sim's `step()` call returns. | `sim_id`, `episode_number`, `sim_sensors`, `sim_reward`, `sim_terminated`, `sim_truncated`, `sensors_in_range`, `info` |
| `complete` | After the teacher has scored the step and terminal status is determined. | `sim_id`, `episode_number`, `agent_name`, `teacher_reward`, `teacher_success`, `teacher_terminated`, `sim_terminated`, `sensors_in_range`, `final_terminated`, `final_truncated`, `success_counter` |
| `episode-end` | Only emitted when the episode terminates or truncates. Includes reason breakdown. | `sim_id`, `episode_number`, `reason` (`teacher_terminated`, `teacher_success`, `sim_terminated`, `sensors_out_of_range`), `unfiltered_obs` |

### `training_result`

Emitted once per PPO training iteration by `training_callbacks.py`.

| `category_sub` | When emitted | Notable `data` fields |
|---|---|---|
| `training_result` | After each PPO iteration completes. | `result.training_iteration`, `result.episode_reward_mean`, `result.episode_reward_min`, `result.episode_reward_max`, `result.episodes_this_iter`, `result.timesteps_total` |
| `evaluation_metrics` | When evaluation is configured and runs after a training iteration. | `result.evaluation.episode_reward_mean` (and other eval metrics) |

### `Training`

Emitted by the multi-agent environment wrapper at episode boundaries.

| `category_sub` | When emitted | Notable `data` fields |
|---|---|---|
| `episode_end` | At the end of each episode in a multi-agent environment. | One key per sensor name, with the final observation value for that episode. |

### `orchestration`

Emitted by the `Orchestration` class.

| `category_sub` | When emitted | Notable `data` fields |
|---|---|---|
| `export` | When `orchestration.export()` is called. | `json` (the full serialized orchestration JSON as a string) |
| `agent-training` | When an agent begins its training phase. | `name` (agent name), `type` (agent class type) |

### `trainer`

Emitted by `TrainerBase`.

| `category_sub` | When emitted | Notable `data` fields |
|---|---|---|
| `initialized` | After the trainer is initialized. | `target` (target configuration type) |

### Render frames

At episode termination, the environment attempts to call `sim.get_render()`. If the sim supports rendering, the frame is sunk with:

| `category` | `category_sub` | `data` |
|---|---|---|
| `f{episode_number}` (e.g. `f0`, `f1`) | `end_frame` | The rendered frame as a numpy array string or raw base64 string, depending on the sim's `get_render()` implementation. |

---

## What to look for

### Training convergence

Use `training_result / training_result` events to plot the learning curve. Key signals:

- **`episode_reward_mean` trending upward** — the policy is improving.
- **`episode_reward_mean` plateau with high `episode_reward_max`** — some rollouts succeed but others fail; the policy has not generalized. Check scenario diversity.
- **`episode_reward_mean` flat from iteration 1** — the reward signal is likely degenerate. Cross-reference with `env-step / complete` to check `teacher_reward` values.
- **`episodes_this_iter` is very low** — episodes may be terminating very quickly due to early `teacher_terminated` or `sim_terminated`. Check `env-step / episode-end` for the reason breakdown.

### Episode termination reasons

Filter `env-step / episode-end` rows and inspect the `reason` field:

```python
import json
from deltalake import DeltaTable

dt = DeltaTable("/path/to/run-abc123")
t = dt.to_pyarrow_table()

import pyarrow.compute as pc
ends = t.filter(
    pc.and_(pc.equal(t["category"], "env-step"),
            pc.equal(t["category_sub"], "episode-end"))
)

for row in ends.to_pylist():
    reason = json.loads(row["data"])["reason"]
    print(reason)
```

| Reason field | What it means |
|---|---|
| `teacher_terminated: true` | `compute_termination()` fired — unsafe or out-of-bounds state. |
| `teacher_success: true` | `compute_success_criteria()` fired — goal achieved. |
| `sim_terminated: true` | The sim itself signaled done, independent of the teacher. |
| `sensors_out_of_range: true` | One or more sensor values fell outside the declared space bounds. |

Frequent `sensors_out_of_range` terminations indicate the sim is producing observations outside its declared space, or the space definition is too tight.

### Sensor space loading

Query `env-lifecycle / sim-spaces-loaded` to verify all workers loaded the correct spaces:

```python
spaces = t.filter(
    pc.and_(pc.equal(t["category"], "env-lifecycle"),
            pc.equal(t["category_sub"], "sim-spaces-loaded"))
)
for row in spaces.to_pylist():
    d = json.loads(row["data"])
    print(d["address"], d["sim_sensor_space"], d["sim_action_space"])
```

Inconsistent addresses across workers indicate misconfigured sim pool routing.

### Reward per step

Query `env-step / complete` and plot `teacher_reward` over time. Warning signs:

- **`teacher_reward` is `0.0` on every step** — the teacher's reward function is returning zero (possibly a missing sensor key defaulting to 0.0 in `dict.get()`).
- **`success_counter` never increases** — `teacher_success` is never `True`. The policy has not learned to meet success criteria.
- **`success_counter` at `0` because it is decremented on `teacher_terminated`** — the orchestration is getting penalized frequently. Check how often `teacher_terminated` is `True` in step-complete events.

### Checkpoint health

Query `agent-trainer / checkpoint-*` events to confirm checkpoints are being saved and loaded correctly:

- `checkpoint-restored` should appear at training resumption.
- `checkpoint-restore-failed` or `checkpoint-dir-missing` at the start of a resumed run means the model is training from scratch despite a prior run existing. Check `checkpoint_uri` in the event payload against the actual filesystem path.

### Action fidelity

Compare `action-processed` (teacher's `transform_action()` output) with `action-coerced` (after `sim_action_space.coerce_sample()`). If these differ significantly, the teacher is producing out-of-space actions that are being silently clamped. This may indicate a mismatch between `get_custom_action_space()` and the sim's native action space.

---

## Querying patterns

### Reward curve per iteration

```python
import json
from deltalake import DeltaTable
import pyarrow.compute as pc

dt = DeltaTable("/path/to/run-abc123")
t = dt.to_pyarrow_table()

results = t.filter(
    pc.and_(pc.equal(t["category"], "training_result"),
            pc.equal(t["category_sub"], "training_result"))
).to_pylist()

for row in sorted(results, key=lambda r: r["timestamp"]):
    d = json.loads(row["data"])["result"]
    print(
        f"iter {d['training_iteration']:3d} | "
        f"mean_reward={d['episode_reward_mean']:.2f} | "
        f"timesteps={d['timesteps_total']}"
    )
```

### Episode end reason breakdown

```python
ends = t.filter(
    pc.and_(pc.equal(t["category"], "env-step"),
            pc.equal(t["category_sub"], "episode-end"))
).to_pylist()

from collections import Counter
reasons = Counter()
for row in ends:
    r = json.loads(row["data"])["reason"]
    reasons[next((k for k, v in r.items() if v), "unknown")] += 1

print(reasons)
```

### Count steps per episode

```python
starts = t.filter(
    pc.and_(pc.equal(t["category"], "env-step"),
            pc.equal(t["category_sub"], "start"))
).to_pylist()

from collections import defaultdict
steps_per_episode = defaultdict(int)
for row in starts:
    d = json.loads(row["data"])
    steps_per_episode[(d["sim_id"], d["episode_number"])] += 1

print(sorted(steps_per_episode.values()))
```

---

## Differences from benchmark.json

| | `benchmark.json` | Historian Delta Lake |
|---|---|---|
| **Purpose** | Inference-time evaluation of a trained orchestration. | Real-time capture of the full training process. |
| **Format** | Plain JSON file. | Delta Lake (Parquet + transaction log). |
| **Contents** | Per-step teacher state, actions, rewards, success flags. | All lifecycle, step, reward, and training result events across the entire run. |
| **When written** | Once, after training, during `postprocess()`. | Continuously throughout training, flushed in batches. |
| **State representation** | Teacher-filtered sensor dict (named keys). | Raw sim sensors (array) in step events, filtered sensors in reset-complete events. |
| **Aggregate stats** | Pre-computed per-scenario in the file. | Must be computed by querying the table. |
| **Replay support** | Yes — `replay_export_with_benchmark.py` can feed steps back through the policy. | No — the historian is append-only. |
| **Multi-worker** | Single sequential rollout per episode. | Events from all parallel rollout workers are interleaved. Use `sim_id` to separate workers. |

---

## ⚠️ Quirks

**Events from parallel workers are interleaved** — when `workers > 1` in the agent configuration, multiple RLlib rollout workers each emit their own `env-lifecycle` and `env-step` events simultaneously. Use `sim_id` (present in most event payloads) to group events belonging to the same environment instance. Do not assume that rows with consecutive timestamps belong to the same episode.

**`data` is always a JSON string** — even for numeric payloads. Always call `json.loads(row["data"])` before accessing fields. The value is never a raw int or dict directly in the column.

**`category` for render frames is dynamic** — render frame events use `f{episode_number}` as the category (e.g. `f0`, `f7`). They do not follow the `category / category_sub` pattern used by other events. Filter them with a prefix match (`category.startswith("f")` or a regex) rather than an equality check.

**Historian batches events in groups of 10** — the `TelemetryHistorian._run()` loop dequeues up to 10 events per publish. This means the Delta Lake write lag is up to 10 events behind real time. During high-throughput training (many workers, many environments), event delivery is best-effort; events may be dropped if the MQTT connection is lost.

**`episode_number` resets per `sim_id`, not globally** — each environment instance tracks its own `episode_number` starting from 0. Two rows with `episode_number: 3` and different `sim_id` values are from different workers, not the same episode.

**`sensors_in_range` silently stops the episode** — when a sim returns a sensor observation outside the declared space bounds, `sensors_in_range` is set to `False` and the episode terminates via `final_terminated: true`. This does not raise an exception and may not appear in training logs. If episodes are ending unexpectedly, check `env-step / episode-end` for `sensors_out_of_range: true`.

**`training_result` `result` is a nested dict** — the full RLlib training result dict is stored under the `result` key. Its schema changes across RLlib versions. Access `result.episode_reward_mean` rather than top-level `episode_reward_mean`.

**Delta Lake requires the `_delta_log/` directory** — reading the Parquet files directly without the Delta Lake reader (e.g. `pyarrow.parquet.read_table()`) will succeed but may include partially-committed or vacuumed data if the table has multiple commits. Always use `DeltaTable(path).to_pyarrow_table()` to read correctly.
