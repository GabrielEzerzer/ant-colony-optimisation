import random
from typing import List, Tuple, Dict, Optional, Deque
from dataclasses import dataclass, field
from collections import deque
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
    recent_positions: Deque[Tuple[int, int]] = field(default_factory=lambda: deque(maxlen=8))
    
    def reset(self, start_pos: Tuple[int, int]) -> None:
        """Reset ant to initial state."""
        self.position = start_pos
        self.path = [start_pos]
        self.visited = {start_pos}
        self.has_food = False
        self.returning_home = False
        self.steps_taken = 0
        self.return_path = []
        self.recent_positions.clear()


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
    pheromones_food: Dict[Tuple[Tuple[int, int], Tuple[int, int]], float],
    pheromones_explore: Dict[Tuple[Tuple[int, int], Tuple[int, int]], float],
    alpha: float = 1.0,
    beta: float = 3.0,
    Q_food: float = 1.0,
    Q_explore: float = 0.2,
    epsilon_explore: float = 0.05,
    restricted_cells: Optional[set] = None,
) -> Tuple[bool, bool]:
    """
    Execute one step for an ant. 
    Returns (found_food, returned_home) tuple.
    - found_food: True if ant just reached objective
    - returned_home: True if ant just returned to colony with food
    """
    if ant.steps_taken >= ant.max_steps and not ant.returning_home:
        # Reset ant instead of freezing it (only during exploration)
        ant.reset(world.start)
        return (False, False)
    
    current_position = ant.position
    # Ensure path is initialized with the starting position
    if not ant.path:
        ant.path = [current_position]
        ant.visited = {current_position}
    
    # If ant is returning home with food
    if ant.returning_home:
        if current_position == world.start:
            # Reached home!
            ant.returning_home = False
            ant.has_food = False
            ant.steps_taken = 0  # Reset step counter for next trip
            ant.recent_positions.clear()
            # Path will be reset when ant starts next trip
            return (False, True)  # Returned home successfully
        
        # Return by retracing the exact path taken (stack of previous positions)
        if not ant.return_path:
            # Rebuild return path if it was cleared unexpectedly
            ant.return_path = ant.path[:-1]

        if not ant.return_path:
            # Fallback: move one step toward home to avoid stalling/disappearing
            neighbors = world.neighbors(current_position)
            if not neighbors:
                return (False, False)
            next_position = min(neighbors, key=lambda n: world.distance(n, world.start))
        else:
            next_position = ant.return_path.pop()
        
        # DYNAMIC PHEROMONE DEPOSITION: Deposit strong food pheromone as ant returns with food
        # Deposit on the forward edge (from start->goal direction) to reinforce the path
        edge = (next_position, current_position)
        # Reduce deposit near the start to avoid excessive buildup and looping
        dist_from_start = world.distance(current_position, world.start)
        start_dampen = min(1.0, dist_from_start / 5.0)  # 0.0..1.0 over first 5 steps
        deposit_amount = Q_food * start_dampen
        if edge in pheromones_food:
            pheromones_food[edge] += deposit_amount
        else:
            pheromones_food[edge] = deposit_amount
        # Cap pheromone to prevent runaway accumulation
        if pheromones_food[edge] > 500.0:
            pheromones_food[edge] = 500.0
        
        ant.position = next_position
        ant.recent_positions.append(next_position)
        ant.steps_taken += 1
        return (False, False)
    # Normal exploration mode
    # If ant just returned home and is starting a new trip, reset for exploration
    if current_position == world.start and len(ant.path) > 1:
        # Ant completed a trip and is starting fresh
        ant.path = [world.start]
        ant.return_path = []
        ant.steps_taken = 0
        ant.visited = {world.start}
        ant.recent_positions.clear()
    
    # Check if at goal
    if current_position == world.goal:
        ant.has_food = True
        ant.returning_home = True
        # Don't use return_path anymore - use pheromone-guided return
        ant.return_path = ant.path[:-1]
        ant.recent_positions.clear()
        ant.steps_taken = 0
        return (True, False)  # Found food!
    
    # Get all neighbors for pheromone-based selection
    all_neighbors = world.neighbors(current_position)
    restricted_cells = restricted_cells or set()
    if restricted_cells:
        # Filter out restricted cells unless it's the goal or start
        filtered_neighbors = [
            n for n in all_neighbors
            if n not in restricted_cells or n == world.goal or n == world.start
        ]
        if filtered_neighbors:
            all_neighbors = filtered_neighbors
    
    if not all_neighbors:
        # No moves available, reset to start to avoid stuck ants
        ant.reset(world.start)
        return (False, False)
    
    # If goal is reachable, go directly to it
    if world.goal in all_neighbors:
        ant.position = world.goal
        ant.path.append(ant.position)
        ant.visited.add(ant.position)
        ant.has_food = True
        ant.returning_home = True
        ant.return_path = ant.path[:-1]
        ant.recent_positions.clear()
        ant.steps_taken = 0
        return (True, False)  # Found food!
    
    # FIRST filter out recent positions to prevent loops
    candidates = [n for n in all_neighbors if n not in ant.recent_positions]
    
    # If all neighbors are recent, we need to allow revisiting (but still penalize)
    if not candidates:
        candidates = all_neighbors
    
    # Calculate weights based on pheromone and heuristic
    weights: List[float] = []
    for neighbor in candidates:
        # Combine food pheromone with exploration pheromone
        tau_food = get_pheromone(pheromones_food, current_position, neighbor)
        tau_explore = get_pheromone(pheromones_explore, current_position, neighbor)
        # Prevent ants from getting stuck at the start due to very high pheromones
        if current_position == world.start:
            tau_food = 0.01  # Small value instead of 0
            tau_explore = 0.01
        tau = (tau_food * 0.9) + (tau_explore * 0.1)
        e = eta(world, neighbor)
        
        # Calculate weight with normalization to prevent overflow
        tau_safe = max(min(tau, 100.0), 0.01)  # Clamp to [0.01, 100.0]
        weight = (tau_safe ** alpha) * (e ** beta)
        
        # Penalize previously visited positions (but not as much as recent)
        if neighbor in ant.visited:
            weight *= 0.3  # 70% penalty for revisiting
        
        # Note: recent positions are already filtered out above
        # Only apply this penalty if we were forced to include them
        if neighbor in ant.recent_positions:
            weight *= 0.001  # 99.9% penalty if forced to revisit recent positions
        
        weights.append(weight)
    
    # Normalize weights to prevent numerical issues
    max_weight = max(weights) if weights else 1.0
    if max_weight > 1e6:
        # If weights are too large, rescale them
        weights = [w / max_weight for w in weights]
    
    # Select next position probabilistically with epsilon exploration
    if epsilon_explore > 0.0 and random.random() < epsilon_explore:
        next_position = random.choice(candidates)
    else:
        next_position = weighted_choice(candidates, weights)
    
    # Deposit weak exploration pheromone as ants move (short-lived)
    edge = (current_position, next_position)
    if edge in pheromones_explore:
        pheromones_explore[edge] += Q_explore
    else:
        pheromones_explore[edge] = Q_explore
    
    ant.position = next_position
    ant.path.append(next_position)
    ant.visited.add(next_position)
    ant.recent_positions.append(next_position)
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
