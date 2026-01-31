from dataclasses import dataclass, field
from typing import List, Dict, Optional
from ants import Ant


@dataclass
class ColonyStatistics:
    """Tracks statistics of the ant colony over time."""
    timestep: int = 0
    ants_at_goal: int = 0
    ants_with_food: int = 0
    avg_path_length: float = 0.0
    total_pheromone: float = 0.0
    best_path_length: int = 0
    ants_active: int = 0
    
    history: Dict[str, List[float]] = field(default_factory=lambda: {
        'ants_at_goal': [],
        'ants_with_food': [],
        'avg_path_length': [],
        'total_pheromone': [],
        'best_path_length': [],
        'ants_active': [],
        'timesteps': []
    })


def update_statistics(
    stats: ColonyStatistics,
    ants: List[Ant],
    pheromones: Dict,
    best_path_length: int = None,
    total_pheromone: Optional[float] = None,
) -> None:
    """Update statistics based on current colony state."""
    stats.ants_at_goal = sum(1 for ant in ants if ant.position == ant.path[0].__class__)  # placeholder
    stats.ants_with_food = sum(1 for ant in ants if ant.has_food)
    stats.ants_active = sum(1 for ant in ants if ant.steps_taken < ant.max_steps)
    
    path_lengths = [len(ant.path) for ant in ants]
    stats.avg_path_length = sum(path_lengths) / len(path_lengths) if path_lengths else 0.0
    stats.total_pheromone = total_pheromone if total_pheromone is not None else sum(pheromones.values())
    
    if best_path_length is not None:
        stats.best_path_length = best_path_length
    
    # Append to history
    stats.history['ants_with_food'].append(stats.ants_with_food)
    stats.history['avg_path_length'].append(stats.avg_path_length)
    stats.history['total_pheromone'].append(stats.total_pheromone)
    stats.history['best_path_length'].append(stats.best_path_length)
    stats.history['ants_active'].append(stats.ants_active)
    stats.history['timesteps'].append(stats.timestep)


def get_statistics_summary(stats: ColonyStatistics) -> str:
    """Get a human-readable summary of colony statistics."""
    return (
        f"Timestep: {stats.timestep}\n"
        f"  Ants with food: {stats.ants_with_food}\n"
        f"  Ants active: {stats.ants_active}\n"
        f"  Avg path length: {stats.avg_path_length:.2f}\n"
        f"  Best path length: {stats.best_path_length}\n"
        f"  Total pheromone: {stats.total_pheromone:.2f}"
    )
