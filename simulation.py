from typing import List, Dict, Tuple, Optional, Set
from gridworld import GridWorld
from ants import Ant, step_ant
from pheromones import init_pheromones, get_pheromone, set_pheromone
from statistics import ColonyStatistics, update_statistics


class AntColonySimulation:
    """Main simulation orchestrator for ant colony behavior."""
    
    def __init__(
        self,
        world: GridWorld,
        n_ants: int = 50,
        alpha: float = 1.0,
        beta: float = 1.2,
        rho: float = 0.1,
        Q: float = 1.0,
        tau0: float = 1.0,
        min_tau: float = 1e-6,
        max_steps_per_ant: int = 200,
        epsilon_explore: float = 0.05,
        visit_limit: int = 50,
    ):
        """Initialize ant colony simulation."""
        self.world = world
        self.n_ants = n_ants
        self.alpha = alpha
        self.beta = beta
        self.rho = rho
        self.Q = Q
        self.tau0 = tau0
        self.min_tau = min_tau
        self.max_steps_per_ant = max_steps_per_ant
        self.epsilon_explore = epsilon_explore
        self.visit_limit = visit_limit
        
        # Initialize colony
        self.ants: List[Ant] = [
            Ant(id=i, position=world.start, max_steps=max_steps_per_ant)
            for i in range(n_ants)
        ]
        
        # Initialize pheromones (separate maps for food and exploration)
        self.pheromones_food: Dict[Tuple[Tuple[int, int], Tuple[int, int]], float] = init_pheromones(
            world, tau=tau0
        )
        self.pheromones_explore: Dict[Tuple[Tuple[int, int], Tuple[int, int]], float] = init_pheromones(
            world, tau=0.0
        )
        
        # Statistics tracking
        self.statistics = ColonyStatistics()
        self.timestep = 0
        self.best_path_found: Optional[List[Tuple[int, int]]] = None
        self.best_path_cost = float("inf")

        # Visitation tracking for restricting overused non-optimal cells
        self.visit_counts: Dict[Tuple[int, int], int] = {}
        self.restricted_cells: Set[Tuple[int, int]] = set()
        
        # Convergence tracking - route stability based
        self.iterations_with_same_best = 0
        self.convergence_threshold = 50  # Iterations of stability
        self.recent_paths: List[List[Tuple[int, int]]] = []  # Track recent successful paths
        self.path_stability_window = 20  # Check last N successful paths
        self.convergence_detected = False  # Flag when converged, but don't stop
    
    def step(self) -> None:
        """Execute one timestep of the simulation."""
        self.timestep += 1

        # Update restricted cells based on visit frequency and best path
        self._refresh_restricted_cells()
        
        # Move all ants and track food/return events
        ants_found_food = []
        ants_returned_home = []
        
        for ant in self.ants:
            found_food, returned_home = step_ant(
                ant,
                self.world,
                self.pheromones_food,
                self.pheromones_explore,
                self.alpha,
                self.beta,
                Q_food=self.Q,
                Q_explore=self.Q * 0.05,
                epsilon_explore=self.epsilon_explore,
                restricted_cells=self.restricted_cells,
            )
            if found_food:
                ants_found_food.append(ant)
            if returned_home:
                ants_returned_home.append(ant)

            # Track cell visits after movement
            pos = ant.position
            self.visit_counts[pos] = self.visit_counts.get(pos, 0) + 1
        
        # Handle pheromone updates for ants returning with food
        self._update_pheromones_from_returns(ants_returned_home)
        
        # Evaporate pheromones every timestep (standard ACO)
        self._evaporate_pheromones()
        
        # Check for new best paths
        self._update_best_path()
        
        # Update statistics
        self.statistics.timestep = self.timestep
        total_pheromone = sum(self.pheromones_food.values()) + sum(self.pheromones_explore.values())
        update_statistics(
            self.statistics,
            self.ants,
            self.pheromones_food,
            best_path_length=len(self.best_path_found) if self.best_path_found else 0,
            total_pheromone=total_pheromone,
        )
    
    def _update_pheromones_from_returns(self, returned_ants: List[Ant]) -> None:
        """Track successful paths for convergence detection."""
        for ant in returned_ants:
            # Track successful paths for convergence detection
            if ant.path and len(ant.path) > 1:
                self.recent_paths.append(ant.path.copy())
                if len(self.recent_paths) > self.path_stability_window:
                    self.recent_paths.pop(0)  # Keep only recent paths
                # Note: Pheromones are now deposited dynamically as ants move,
                # not in bulk after completion. This allows real-time trail formation.

    
    def _update_best_path(self) -> None:
        """Update best path found so far."""
        improved = False
        # Only consider successful paths (ants that have reached food)
        for ant in self.ants:
            if ant.path and len(ant.path) > 1 and (ant.returning_home or ant.has_food or ant.position == self.world.goal):
                path_cost = len(ant.path) - 1
                if path_cost < self.best_path_cost:
                    self.best_path_cost = path_cost
                    self.best_path_found = ant.path.copy()
                    improved = True
        
        # Only increment convergence counter once per timestep if no improvement
        if improved:
            self.iterations_with_same_best = 0
        else:
            self.iterations_with_same_best += 1

    def _refresh_restricted_cells(self) -> None:
        """Restrict overused cells that are not on the current best path."""
        if not self.visit_counts:
            self.restricted_cells.clear()
            return

        best_path_set = set(self.best_path_found) if self.best_path_found else set()
        self.restricted_cells = {
            pos for pos, count in self.visit_counts.items()
            if count >= self.visit_limit
            and pos not in best_path_set
            and pos != self.world.start
            and pos != self.world.goal
        }
    
    def is_converged(self) -> bool:
        """Check if routes have stabilized (high proportion using same path)."""
        # Need both: enough iterations AND path found AND stable route selection
        min_iterations = 20  # Minimum iterations before convergence can be declared
        
        if self.timestep < min_iterations or not self.best_path_found:
            return False
        
        # Check route stability: are most ants using the same path?
        if len(self.recent_paths) < self.path_stability_window * 0.5:
            return False  # Not enough data yet
        
        # Calculate how many recent paths match the best path
        matching_paths = 0
        for path in self.recent_paths:
            if self._paths_are_similar(path, self.best_path_found):
                matching_paths += 1
        
        # Convergence = >70% of ants using the same route
        stability_ratio = matching_paths / len(self.recent_paths)
        return stability_ratio > 0.7
    
    def _paths_are_similar(self, path1: List[Tuple[int, int]], path2: List[Tuple[int, int]]) -> bool:
        """Check if two paths are essentially the same route."""
        if len(path1) != len(path2):
            return False
        # Paths match if they visit the same positions
        return path1 == path2
    
    def get_convergence_status(self) -> Tuple[bool, float]:
        """Get convergence status and stability ratio."""
        if len(self.recent_paths) == 0:
            return False, 0.0
        
        matching_paths = sum(1 for path in self.recent_paths 
                           if self.best_path_found and self._paths_are_similar(path, self.best_path_found))
        stability_ratio = matching_paths / len(self.recent_paths)
        is_stable = stability_ratio > 0.7 and self.timestep >= 20
        return is_stable, stability_ratio
    
    def run_timesteps(self, n_timesteps: int) -> None:
        """Run simulation for n timesteps."""
        for _ in range(n_timesteps):
            self.step()
    
    def reset_ants(self) -> None:
        """Reset all ants to starting position."""
        for ant in self.ants:
            ant.reset(self.world.start)
    
    def apply_pheromone_update(self) -> None:
        """No-op: dynamic pheromone deposition is handled in step()."""
        return
    
    def _evaporate_pheromones(self) -> None:
        """Apply pheromone evaporation for both maps."""
        eps = 1e-6
        rho = max(0.0, min(self.rho, 1.0 - eps))
        if rho == 0.0:
            return
        
        # Evaporate food pheromones (slower)
        for edge in list(self.pheromones_food.keys()):
            self.pheromones_food[edge] *= (1.0 - rho)

        # Evaporate exploration pheromones (faster)
        explore_rho = min(0.6, rho * 3.0)
        for edge in list(self.pheromones_explore.keys()):
            self.pheromones_explore[edge] *= (1.0 - explore_rho)
    
    def _deposit_on_path(self, path: List[Tuple[int, int]]) -> None:
        """Deposit pheromone on a path."""
        amount = self.Q / self.best_path_cost if self.best_path_cost > 0 else self.Q
        
        for i in range(len(path) - 1):
            edge = (path[i], path[i + 1])
            current_pheromone = self.pheromones_food.get(edge, self.tau0)
            self.pheromones_food[edge] = current_pheromone + amount
    
    def get_ant_positions(self) -> List[Tuple[int, Tuple[int, int]]]:
        """Get current positions of all ants."""
        return [(ant.id, ant.position) for ant in self.ants]
    
    def get_ant_paths(self) -> List[List[Tuple[int, int]]]:
        """Get paths taken by all ants."""
        return [ant.path.copy() for ant in self.ants]
    
    def get_statistics(self) -> ColonyStatistics:
        """Get current statistics."""
        return self.statistics
    
    def get_status_report(self) -> str:
        """Get a formatted status report."""
        report = f"=== Ant Colony Simulation - Timestep {self.timestep} ===\n"
        report += f"World size: {self.world.width}x{self.world.height}\n"
        report += f"Colony size: {self.n_ants}\n"
        report += f"Active ants: {self.statistics.ants_active}\n"
        report += f"Ants with food: {self.statistics.ants_with_food}\n"
        report += f"Best path cost: {self.best_path_cost}\n"
        report += f"Average path length: {self.statistics.avg_path_length:.2f}\n"
        report += f"Total pheromone: {self.statistics.total_pheromone:.4f}\n"
        return report
