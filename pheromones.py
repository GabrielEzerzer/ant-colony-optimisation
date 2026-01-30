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


def init_pheromones(world: GridWorld, tau: float = 0.0) -> Dict[Tuple[Tuple[int, int], Tuple[int, int]], float]:
    """Initialize pheromones on all edges. Default to 0 for pure learning."""
    pheromones = {}
    edges = all_edges(world)
    for edge in edges:
        pheromones[edge] = tau
    return pheromones


def get_pheromone(pheromones: Dict[Tuple[Tuple[int, int], Tuple[int, int]], float], 
                  from_pos: Tuple[int, int], to_pos: Tuple[int, int]) -> float:
    """Retrieve pheromone level for an edge, default to 0.01 for exploration."""
    value = pheromones.get((from_pos, to_pos), 0.01)
    # Return small positive value if pheromone is 0 (allows exploration)
    return max(value, 0.01)


def get_pheromone_influence(pheromones: Dict[Tuple[Tuple[int, int], Tuple[int, int]], float],
                           from_pos: Tuple[int, int], to_pos: Tuple[int, int]) -> float:
    """Get pheromone influence including nearby trails for better trail following.
    
    This checks not just the direct edge, but also nearby edges to simulate
    pheromone diffusion and area-of-effect. Ants can sense trails even if they're
    not exactly on the path.
    """
    # Direct edge pheromone (strongest)
    direct = pheromones.get((from_pos, to_pos), 0.0)
    
    # Check nearby edges for influence (weaker)
    influence = direct
    
    # Look at edges FROM the target position (where the ant would go)
    # This helps ants sense if there's a strong trail continuing from the next position
    neighbors_of_target = [
        (to_pos[0] + dr, to_pos[1] + dc)
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]
    ]
    
    for neighbor in neighbors_of_target:
        edge_pheromone = pheromones.get((to_pos, neighbor), 0.0)
        influence += edge_pheromone * 0.3  # 30% influence from continuation paths
    
    # Also check edges TO the target position from nearby cells
    neighbors_of_current = [
        (from_pos[0] + dr, from_pos[1] + dc)
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]
        if (from_pos[0] + dr, from_pos[1] + dc) != to_pos
    ]
    
    for neighbor in neighbors_of_current:
        edge_pheromone = pheromones.get((neighbor, to_pos), 0.0)
        influence += edge_pheromone * 0.2  # 20% influence from parallel paths
    
    return max(influence, 0.01)


def set_pheromone(pheromones: Dict[Tuple[Tuple[int, int], Tuple[int, int]], float],
                  from_pos: Tuple[int, int], to_pos: Tuple[int, int], value: float) -> None:
    """Set pheromone level for an edge."""
    pheromones[(from_pos, to_pos)] = max(value, 0.0)


def get_total_pheromone(pheromones: Dict[Tuple[Tuple[int, int], Tuple[int, int]], float]) -> float:
    """Get total pheromone in the system."""
    return sum(pheromones.values())
