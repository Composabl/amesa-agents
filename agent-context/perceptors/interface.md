# Perceptor Interface

`PerceptorImpl` transforms raw observations into derived features consumed by skills.

## Full scaffold

```python
from amesa_core.agent.perceptor.perceptor_impl import PerceptorImpl

class MyPerceptor(PerceptorImpl):
    # REQUIRED: Produce derived variables from raw observations.
    async def compute(self, obs_spec, obs) -> dict:
        return {
            "derived_value": float(obs["a"]) - float(obs["b"]),
        }

    # REQUIRED: Declare which raw sensor keys this perceptor depends on.
    def filtered_sensor_space(self, obs) -> list[str]:
        return ["a", "b"]
```

## Methods and intended use

### `compute(self, obs_spec, obs) -> dict` (required)

Use this to calculate perceptor outputs from simulator observations. Capabilities include combining sensors, applying normalization, feature engineering, and exposing stable keys that downstream teachers/controllers consume.

### `filtered_sensor_space(self, obs) -> list[str]` (required)

Use this to declare the raw sensor keys the perceptor reads. This acts as the perceptor's dependency contract and helps keep observation usage explicit and minimal.

## Optional methods

`PerceptorImpl` has no optional lifecycle methods you must implement.

## Method contracts

- `compute(...)` returns a dict of derived keys/values.
- `filtered_sensor_space(...)` returns the raw input sensor keys this perceptor reads.
- Returned keys should be stable and documented in component metadata (`variables` in publish config).
