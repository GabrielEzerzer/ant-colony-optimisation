from gridworld import GridWorld
from typing import List, Tuple

def all_edges(world: GridWorld) -> List[Tuple[Tuple[int, int], Tuple[int, int]]]:
    edges = []
    for r in range(world.height):
        for c in range(world.width):
            pos = (r, c)
            if world.is_free(pos):
                for neighbor in world.neighbors(pos):
                    edges.append((pos, neighbor))
    return edges

def init_pheromones(world: GridWorld, tau: float = 1.0) -> dict:
    pheromones = {}
    edges = all_edges(world)
    for edge in edges:
        pheromones[edge] = tau
    return pheromones

def get_pheromone(pheromones: dict, from_pos: Tuple[int, int], to_pos: Tuple[int, int]) -> float:
    return pheromones.get((from_pos, to_pos), 1.0)