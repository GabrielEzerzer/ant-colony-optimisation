# Ant Colony Simulator

A comprehensive ant colony optimization (ACO) simulation system with interactive visualization. This project simulates realistic ant colony behavior using swarm intelligence, pheromone trails, and collective problem-solving.

## Usage

### Interactive Visualization 

```bash
python renderer.py
```

**Controls:**
- **SPACE**: Pause/Resume simulation
- **R**: Reset simulation
- **P**: Toggle pheromone visualization
- **Left Click**: Add obstacles
- **Right Click**: Remove obstacles

### Non-Visual Simulation

```bash
python main.py
```

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

### Interactive Visualization with Custom Config

```python
from renderer import AntColonyVisualizer
from config import SimulationConfig

config = SimulationConfig(
    world_width=50,
    world_height=50,
    n_ants=75,
    obstacles=[(10, 10), (10, 11), (10, 12)]
)

viz = AntColonyVisualizer(config)
viz.run()
```


