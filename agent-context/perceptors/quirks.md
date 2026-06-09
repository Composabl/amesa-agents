# Perceptor Quirks

- Some sims return list/array observations; normalize to dict inside `compute(...)` when needed.
- Stateful perceptors must manage reset behavior explicitly.
