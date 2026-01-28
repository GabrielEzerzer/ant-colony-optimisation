from typing import List, Tuple, Dict
from gridworld import GridWorld
from pheromones import init_pheromones, set_pheromone


def path_cost(path: List[Tuple[int, int]], world: GridWorld) -> float:
    """Calculate cost of a path. Returns inf if path doesn't reach goal."""
    if not path:
        return float("inf")
    if path[-1] != world.goal:
        return float("inf")
    return len(path) - 1


def edges_from_path(path: List[Tuple[int, int]]) -> List[Tuple[Tuple[int, int], Tuple[int, int]]]:
    """Extract edges from a path."""
    return [(path[i], path[i + 1]) for i in range(len(path) - 1)]


def evaporate(pheromones: Dict[Tuple[Tuple[int, int], Tuple[int, int]], float], 
              rho: float, min_tau: float = 1e-6) -> None:
    """Apply pheromone evaporation to all edges."""
    eps = 1e-6
    rho = max(0.0, min(rho, 1.0 - eps))
    if rho == 0.0:
        return
    
    for edge in list(pheromones.keys()):
        pheromones[edge] *= (1.0 - rho)
        if pheromones[edge] < min_tau:
            pheromones[edge] = min_tau


def deposit(
    pheromones: Dict[Tuple[Tuple[int, int], Tuple[int, int]], float],
    path_edges: List[Tuple[Tuple[int, int], Tuple[int, int]]],
    amount: float,
    default_tau: float = 1.0,
) -> None:
    """Deposit pheromone on edges of a path."""
    if amount is None or amount <= 0:
        return
    
    for edge in path_edges:
        # Initialize if missing; add deposit
        pheromones[edge] = pheromones.get(edge, default_tau) + amount


def run_aco(
    world: GridWorld,
    n_ants: int = 50,
    n_iterations: int = 100,
    rho: float = 0.1,
    Q: float = 1.0,
    alpha: float = 1.0,
    beta: float = 1.2,
    max_steps: int = 200,
    tau0: float = 1.0,
    min_tau: float = 1e-6,
):
    """Run Ant Colony Optimization algorithm and return best path and history."""
    pheromones = init_pheromones(world, tau=tau0)

    global_best_path = None
    global_best_cost = float("inf")
    best_cost_history: List[float] = []

    for it in range(n_iterations):
        iteration_best_path = None
        iteration_best_cost = float("inf")

        # Each ant constructs a path
        from ants import construct_path
        for _ in range(n_ants):
            path = construct_path(world, max_steps=max_steps, pheromones=pheromones, alpha=alpha, beta=beta)
            cost = path_cost(path, world)
            
            if cost < iteration_best_cost:
                iteration_best_cost = cost
                iteration_best_path = path
            
            if cost < global_best_cost:
                global_best_cost = cost
                global_best_path = path

        # Evaporation phase
        evaporate(pheromones, rho, min_tau=min_tau)

        # Pheromone deposition phase
        if iteration_best_path is not None and iteration_best_cost != float("inf"):
            amount = Q / iteration_best_cost if iteration_best_cost > 0 else Q
            deposit(pheromones, edges_from_path(iteration_best_path), amount, default_tau=tau0)

        best_cost_history.append(global_best_cost)

    return global_best_path, best_cost_history, pheromones
