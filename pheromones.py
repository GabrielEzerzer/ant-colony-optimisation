from typing import List, Tuple, Dict
from gridworld import GridWorld


def all_edges(world: GridWorld) -> List[Tuple[Tuple[int, int], Tuple[int, int]]]:
    """Generate all valid edges in the grid world."""
    edges = []
    for r in range(world.height):
        for c in range(world.width):
            pos = (r, c)
            if world.is_free(pos):
                for neighbor in world.neighbors(pos):
                    edges.append((pos, neighbor))
    return edges


def init_pheromones(world: GridWorld, tau: float = 1.0) -> Dict[Tuple[Tuple[int, int], Tuple[int, int]], float]:
    """Initialize pheromones on all edges with initial value tau."""
    pheromones = {}
    edges = all_edges(world)
    for edge in edges:
        pheromones[edge] = tau
    return pheromones


def get_pheromone(pheromones: Dict[Tuple[Tuple[int, int], Tuple[int, int]], float], 
                  from_pos: Tuple[int, int], to_pos: Tuple[int, int]) -> float:
    """Retrieve pheromone level for an edge, default to 1.0 if not found."""
    return pheromones.get((from_pos, to_pos), 1.0)


def set_pheromone(pheromones: Dict[Tuple[Tuple[int, int], Tuple[int, int]], float],
                  from_pos: Tuple[int, int], to_pos: Tuple[int, int], value: float) -> None:
    """Set pheromone level for an edge."""
    pheromones[(from_pos, to_pos)] = max(value, 0.0)


def get_total_pheromone(pheromones: Dict[Tuple[Tuple[int, int], Tuple[int, int]], float]) -> float:
    """Get total pheromone in the system."""
    return sum(pheromones.values())
