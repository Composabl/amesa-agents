# demo_sim

Demo simulator with multiple space types for testing and validation.

## Quick Start

```bash
# Install in development mode
pip install -e .[dev]

# Run the sim locally
amesa sim run demo_sim --host 0.0.0.0 --port 1337 --protocol grpc

# In another terminal, verify the sim
amesa sim info --address localhost:1337

# Run tests
pytest tests/
```

## Space Types Supported

- `discrete` - Discrete sensor/action spaces
- `multidiscrete` - MultiDiscrete sensor/action spaces
- `multibinary` - MultiBinary sensor/action spaces
- `box` - Box (continuous) sensor/action spaces
- `dictionary` - Dict sensor/action spaces
- `tuple` - Tuple sensor/action spaces
- `text` - Text sensor spaces

## Configuration

Set the space type via env_init:
```python
env_init = {"space_type": "discrete"}
```

Or pass via amesa sim run:
```bash
amesa sim run demo_sim --env-init '{"space_type": "box"}'
```