# Perceptor Interface

`PerceptorImpl` transforms mapped sensor observations into derived features consumed by agents.

Source: `amesa_core/amesa_core/orchestration/perceptor/perceptor_impl.py`. Both methods below are `@abc.abstractmethod`; `compute` is async, `filtered_sensor_space` is sync. `amesa perceptor validate` checks the entrypoint subclasses `PerceptorImpl`, implements both, and that `compute` is async (`amesa_core/utils/validate_util.py`, `validate_abstract_class_implementation`).

## Full scaffold

```python
import numpy as np

from amesa_core import PerceptorImpl  # same class as amesa_core.orchestration.perceptor.perceptor_impl.PerceptorImpl


class MyPerceptor(PerceptorImpl):
    def __init__(self):
        """Must be callable with no arguments: the runtime instantiates ``MyPerceptor()``
        and builds a fresh instance at every episode reset."""
        pass

    # required
    async def compute(self, obs_spec, obs) -> dict:
        """Produce derived variables from the sensor dict.

        :param obs_spec: The sim's sensor space. May be ``None`` (always ``None``
            in ``amesa data perceive`` rollouts) — do not rely on it.
        :param obs: Dict of orchestration sensor name -> value. In training and
            inference each value is a numpy array (a scalar sensor has shape
            ``(1,)``, float32), not a Python float.
        :returns: Dict of new output key -> value.
        :rtype: dict
        :raises Exception: if a returned key collides with a key already present
            in the sensor dict (``"Perceptor X has a key Y that already exists
            in the sensor space dictionary!"``, ``amesa_core/utils/space_utils.py``).
        :note: Returned keys should be stable and listed in ``[amesa].variables``
            of ``pyproject.toml`` (the platform registers them as the perceptor's
            sensors on publish).
        """
        a = float(np.asarray(obs["a"]).reshape(-1)[0])
        b = float(np.asarray(obs["b"]).reshape(-1)[0])
        return {"derived_value": a - b}

    # required (abstract), sync
    def filtered_sensor_space(self, obs) -> list[str]:
        """Declare which sensor keys this perceptor depends on.

        :note: Required by the ABC, but no SDK training/inference path calls it on
            perceptors today. For the platform-side input check, declare inputs in
            ``[amesa].inputs`` of ``pyproject.toml`` as well.
        """
        return ["a", "b"]
```

## Wrapper and registration

```python
from amesa_core import Orchestration, Perceptor

orchestration = Orchestration()
orchestration.add_perceptor(Perceptor("my-perceptor", MyPerceptor))  # pass the class, not an instance
```

`Perceptor(perceptor_name, impl_cls, description=None, config=PerceptorOptions())` — `impl_cls` may also be a local plugin path or an `http(s)` package URL (`amesa_core/orchestration/perceptor/perceptor.py`). `PerceptorOptions` fields: `remote_address`, `sensor_space`, `action_space` (all optional strings).
