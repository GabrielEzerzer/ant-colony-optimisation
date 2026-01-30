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
    returning_home: bool = False  # True when ant found food and heading back
    steps_taken: int = 0
    max_steps: int = 200
    return_path: List[Tuple[int, int]] = field(default_factory=list)  # Path back to colony
    
    def reset(self, start_pos: Tuple[int, int]) -> None:
        """Reset ant to initial state."""
        self.position = start_pos
        self.path = [start_pos]
        self.visited = {start_pos}
        self.has_food = False
        self.returning_home = False
        self.steps_taken = 0
        self.return_path = []


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
) -> Tuple[bool, bool]:
    """
    Execute one step for an ant. 
    Returns (found_food, returned_home) tuple.
    - found_food: True if ant just reached objective
    - returned_home: True if ant just returned to colony with food
    """
    if ant.steps_taken >= ant.max_steps:
        return (False, False)
    
    current_position = ant.position
    
    # If ant is returning home with food
    if ant.returning_home:
        if current_position == world.start:
            # Reached home! Mark as returned but DON'T clear path yet
            # The simulation will handle pheromone deposition first
            ant.returning_home = False
            ant.has_food = False
            # Note: path is NOT cleared here - simulation needs it for pheromone deposition
            # The path will be reset when ant starts next trip
            return (False, True)  # Returned home successfully
        
        # Move towards home (reverse path)
        if ant.return_path:
            # Follow the return path backwards
            next_position = ant.return_path.pop(0)
            # Validate path - if obstacle was added, reroute!
            if not world.is_free(next_position):
                # Obstacle blocks path! Clear return path and find alternate
                ant.return_path = []
                neighbors = world.neighbors(current_position)
                home_neighbors = [n for n in neighbors if world.distance(n, world.start) < world.distance(current_position, world.start)]
                if home_neighbors:
                    next_position = home_neighbors[0]
                else:
                    next_position = random.choice(neighbors) if neighbors else current_position
        else:
            # If return path is empty, move to any neighbor closer to home
            neighbors = world.neighbors(current_position)
            home_neighbors = [n for n in neighbors if world.distance(n, world.start) < world.distance(current_position, world.start)]
            if home_neighbors:
                next_position = home_neighbors[0]
            else:
                next_position = random.choice(neighbors) if neighbors else current_position
        
        ant.position = next_position
        ant.steps_taken += 1
        return (False, False)
    
    # Normal exploration mode
    # If ant just returned home and is starting a new trip, reset for exploration
    if current_position == world.start and len(ant.path) > 1:
        # Ant completed a trip and is starting fresh

        ant.path = [world.start]
        ant.return_path = []
        ant.steps_taken = 0
    
    # Check if at goal
    if current_position == world.goal:
        ant.has_food = True
        ant.returning_home = True
        # Build return path as reverse of current path
        ant.return_path = list(reversed(ant.path[:-1]))  # Don't include goal itself at start of return
        ant.steps_taken += 1
        return (True, False)  # Found food!
    
    # Get all neighbors for pheromone-based selection
    # Don't restrict to unvisited - let pheromone trails guide path choice
    # (Real ACO doesn't forbid revisiting, it uses pheromone weight to discourage it)
    candidates = world.neighbors(current_position)
    
    if not candidates:
        return (False, False)
    
    # If goal is reachable, go directly to it
    if world.goal in candidates:
        ant.position = world.goal
        ant.path.append(ant.position)
        ant.visited.add(ant.position)
        ant.has_food = True
        ant.returning_home = True
        ant.return_path = list(reversed(ant.path[:-1]))
        ant.steps_taken += 1
        return (True, False)  # Found food!
    
    # Calculate weights based on pheromone and heuristic
    weights: List[float] = []
    for neighbor in candidates:
        # Direct edge pheromone (no area-based sensing to prevent spreading effect)
        tau = get_pheromone(pheromones, current_position, neighbor)
        e = eta(world, neighbor)
        
        # Calculate weight with normalization to prevent overflow
        tau_safe = max(min(tau, 100.0), 0.01)  # Clamp to [0.01, 100.0]
        weight = (tau_safe ** alpha) * (e ** beta)
        weights.append(weight)
    
    # Normalize weights to prevent numerical issues
    max_weight = max(weights) if weights else 1.0
    if max_weight > 1e6:
        # If weights are too large, rescale them
        weights = [w / max_weight for w in weights]
    
    # Select next position probabilistically
    next_position = weighted_choice(candidates, weights)
    ant.position = next_position
    ant.path.append(next_position)
    ant.visited.add(next_position)
    ant.steps_taken += 1
    
    return (False, False)


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
