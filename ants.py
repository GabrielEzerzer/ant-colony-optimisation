from typing import List, Tuple
from gridworld import GridWorld 
import random

def construct_random_path(world: GridWorld, max_steps: int = 100) -> List[Tuple[int, int]]:

    path = [world.start]
    current_position = world.start
    if current_position == world.goal:
        return path

    visited = set(path)
    for _ in range(max_steps):
        neighbors = world.neighbors(current_position)
        unvisited = [n for n in neighbors if n not in visited]
        candidates = unvisited if unvisited else neighbors
        if not candidates:
            break
        current_position = random.choice(candidates)
        path.append(current_position)
        visited.add(current_position)

        if current_position == world.goal:
            break
    return path