import random
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass, field
from gridworld import GridWorld
from pheromones import get_pheromone


@dataclass
class Ant:
    """Represents a single ant in the colony."""
    id: int
    position: Tuple[int, int]
    path: List[Tuple[int, int]] = field(default_factory=list)
    visited: set = field(default_factory=set)
    has_food: bool = False
    steps_taken: int = 0
    max_steps: int = 200
    
    def reset(self, start_pos: Tuple[int, int]) -> None:
        """Reset ant to initial state."""
        self.position = start_pos
        self.path = [start_pos]
        self.visited = {start_pos}
        self.has_food = False
        self.steps_taken = 0


def eta(world: GridWorld, pos: Tuple[int, int]) -> float:
    """Heuristic desirability based on distance to goal."""
    return 1.0 / (world.heuristic(pos) + 1)


def weighted_choice(items: List[Tuple[int, int]], weights: List[float]) -> Tuple[int, int]:
    """Select item from list based on probability weights."""
    total = sum(weights)
    if total == 0:
        return random.choice(items)

    cum = 0.0
    u = random.random() * total
    for item, w in zip(items, weights):
        cum += w
        if cum >= u:
            return item

    return items[-1]


def step_ant(
    ant: Ant,
    world: GridWorld,
    pheromones: Dict[Tuple[Tuple[int, int], Tuple[int, int]], float],
    alpha: float = 1.0,
    beta: float = 3.0,
) -> bool:
    """Execute one step for an ant. Returns True if ant reached goal."""
    if ant.steps_taken >= ant.max_steps:
        return False
    
    current_position = ant.position
    
    # Check if at goal
    if current_position == world.goal:
        ant.has_food = True
        return True
    
    # Get candidates (unvisited neighbors, or all neighbors if all visited)
    neighbors = world.neighbors(current_position)
    unvisited = [n for n in neighbors if n not in ant.visited]
    candidates = unvisited if unvisited else neighbors
    
    if not candidates:
        return False
    
    # If goal is reachable, go directly to it
    if world.goal in candidates:
        ant.position = world.goal
        ant.path.append(ant.position)
        ant.visited.add(ant.position)
        ant.has_food = True
        ant.steps_taken += 1
        return True
    
    # Calculate weights based on pheromone and heuristic
    weights: List[float] = []
    for neighbor in candidates:
        tau = get_pheromone(pheromones, current_position, neighbor)
        e = eta(world, neighbor)
        weights.append((tau ** alpha) * (e ** beta))
    
    # Select next position probabilistically
    next_position = weighted_choice(candidates, weights)
    ant.position = next_position
    ant.path.append(next_position)
    ant.visited.add(next_position)
    ant.steps_taken += 1
    
    return False


def construct_path(
    world: GridWorld,
    max_steps: int = 100,
    pheromones: Dict[Tuple[Tuple[int, int], Tuple[int, int]], float] = None,
    alpha: float = 1.0,
    beta: float = 3.0,
) -> List[Tuple[int, int]]:
    """Build a complete path from start to goal (legacy function for compatibility)."""
    path = [world.start]
    current_position = world.start
    if current_position == world.goal:
        return path

    visited = {world.start}
    pheromones = pheromones or {}

    for _ in range(max_steps):
        neighbors = world.neighbors(current_position)
        unvisited = [n for n in neighbors if n not in visited]
        candidates = unvisited if unvisited else neighbors
        
        if not candidates:
            break

        if world.goal in candidates:
            current_position = world.goal
            path.append(current_position)
            break

        weights: List[float] = []
        for n in candidates:
            tau = get_pheromone(pheromones, current_position, n)
            e = eta(world, n)
            weights.append((tau ** alpha) * (e ** beta))

        current_position = weighted_choice(candidates, weights)
        path.append(current_position)
        visited.add(current_position)

        if current_position == world.goal:
            break
    
    return path
