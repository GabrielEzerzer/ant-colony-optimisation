from dataclasses import dataclass
from typing import Tuple, List


@dataclass
class SimulationConfig:
    """Configuration for ant colony simulation."""
    
    # World dimensions
    world_width: int = 50
    world_height: int = 50
    start_pos: Tuple[int, int] = (0, 0)
    goal_pos: Tuple[int, int] = (49, 49)
    
    # Colony parameters
    n_ants: int = 50
    max_steps_per_ant: int = 100  # Reduced to force quick exploration, not 500 random steps
    
    # ACO parameters - tuned for dynamic pheromone deposition
    alpha: float = 2.5          # Pheromone importance (higher = follow trails more)
    beta: float = 2.0           # Heuristic importance (balance exploration/exploitation)
    rho: float = 0.03           # Evaporation rate (slower to preserve trails)
    Q: float = 100.0            # Pheromone strength (higher for stronger trails)
    tau0: float = 0.0           # Initial pheromone level (0 = pure learning)
    min_tau: float = 0.0        # Minimum pheromone level (allow full decay)
    epsilon_explore: float = 0.05  # Random exploration rate (keeps exploration > 0)
    visit_limit: int = 50          # Visits before a non-optimal cell gets restricted
    
    # Simulation control
    max_timesteps: int = 1000
    pheromone_update_interval: int = 10  # Update pheromones every N timesteps
    
    # Optional obstacles (list of (row, col) positions)
    obstacles: List[Tuple[int, int]] = None
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.obstacles is None:
            self.obstacles = []
        
        if not (0 <= self.alpha):
            raise ValueError("alpha must be >= 0")
        if not (0 <= self.beta):
            raise ValueError("beta must be >= 0")
        if not (0.0 <= self.rho <= 1.0):
            raise ValueError("rho must be between 0 and 1")
        if not (self.Q > 0):
            raise ValueError("Q must be > 0")
        if not (self.tau0 >= 0):
            raise ValueError("tau0 must be >= 0")


def _generate_maze_obstacles() -> List[Tuple[int, int]]:
    """Generate some sample obstacles for maze configuration."""
    obstacles = []
    # Vertical wall
    for i in range(10, 40):
        obstacles.append((i, 25))
    # Horizontal wall with gap
    for i in range(5, 25):
        if i != 15:  # Leave a gap
            obstacles.append((20, i))
    return obstacles


# Preset configurations
DEFAULT_CONFIG = SimulationConfig()

SMALL_WORLD = SimulationConfig(
    world_width=30,
    world_height=30,
    goal_pos=(29, 29),
    n_ants=30,
    max_timesteps=500
)

LARGE_WORLD = SimulationConfig(
    world_width=100,
    world_height=100,
    goal_pos=(99, 99),
    n_ants=100,
    max_timesteps=2000
)

COMPLEX_MAZE = SimulationConfig(
    world_width=50,
    world_height=50,
    goal_pos=(49, 49),
    n_ants=75,
    max_timesteps=1500,
    obstacles=_generate_maze_obstacles()
)
