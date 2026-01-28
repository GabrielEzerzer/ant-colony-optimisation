# Ant Colony Simulator

A comprehensive ant colony optimization (ACO) simulation system built in Python.

## Usage

### Basic Simulation

```python
from main import run_simulation
from config import DEFAULT_CONFIG

# Run with default settings
sim = run_simulation()

# Access results
best_path = sim.best_path_found
cost = sim.best_path_cost
stats = sim.get_statistics()
```

### Custom Configuration

```python
from config import SimulationConfig
from main import run_simulation

config = SimulationConfig(
    world_width=100,
    world_height=100,
    n_ants=50,
    alpha=1.0,
    beta=1.5,
    max_timesteps=500
)

sim = run_simulation(config)
```

### Multiple Runs & Comparison

```python
from main import run_multiple_simulations

results = run_multiple_simulations(n_runs=5)
```

