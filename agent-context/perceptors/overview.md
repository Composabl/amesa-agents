# Perceptors Overview

Perceptors compute derived observation features from raw simulator outputs.

They are implemented via `PerceptorImpl` and registered on the orchestration so agents can consume additional keys in `transformed_sensors`.

Use perceptors when:

- raw sim observations need feature engineering
- you want reusable stateful feature transforms across orchestrations
