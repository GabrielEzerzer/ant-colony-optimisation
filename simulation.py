from typing import List, Dict, Tuple, Optional
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
        
        # Initialize colony
        self.ants: List[Ant] = [
            Ant(id=i, position=world.start, max_steps=max_steps_per_ant)
            for i in range(n_ants)
        ]
        
        # Initialize pheromones
        self.pheromones: Dict[Tuple[Tuple[int, int], Tuple[int, int]], float] = init_pheromones(
            world, tau=tau0
        )
        
        # Statistics tracking
        self.statistics = ColonyStatistics()
        self.timestep = 0
        self.best_path_found: Optional[List[Tuple[int, int]]] = None
        self.best_path_cost = float("inf")
    
    def step(self) -> None:
        """Execute one timestep of the simulation."""
        self.timestep += 1
        
        # Move all ants
        for ant in self.ants:
            if ant.steps_taken < ant.max_steps and not ant.has_food:
                step_ant(ant, self.world, self.pheromones, self.alpha, self.beta)
        
        # Check for new best paths
        self._update_best_path()
        
        # Update statistics
        self.statistics.timestep = self.timestep
        update_statistics(
            self.statistics,
            self.ants,
            self.pheromones,
            best_path_length=len(self.best_path_found) if self.best_path_found else 0
        )
    
    def _update_best_path(self) -> None:
        """Update best path found so far."""
        for ant in self.ants:
            if ant.has_food:
                path_cost = len(ant.path) - 1
                if path_cost < self.best_path_cost:
                    self.best_path_cost = path_cost
                    self.best_path_found = ant.path.copy()
    
    def run_timesteps(self, n_timesteps: int) -> None:
        """Run simulation for n timesteps."""
        for _ in range(n_timesteps):
            self.step()
    
    def reset_ants(self) -> None:
        """Reset all ants to starting position."""
        for ant in self.ants:
            ant.reset(self.world.start)
    
    def apply_pheromone_update(self) -> None:
        """Apply evaporation and deposition based on best paths found."""
        # Evaporation
        self._evaporate_pheromones()
        
        # Deposition on best path
        if self.best_path_found and self.best_path_cost > 0:
            self._deposit_on_path(self.best_path_found)
    
    def _evaporate_pheromones(self) -> None:
        """Apply pheromone evaporation."""
        eps = 1e-6
        rho = max(0.0, min(self.rho, 1.0 - eps))
        if rho == 0.0:
            return
        
        for edge in list(self.pheromones.keys()):
            self.pheromones[edge] *= (1.0 - rho)
            if self.pheromones[edge] < self.min_tau:
                self.pheromones[edge] = self.min_tau
    
    def _deposit_on_path(self, path: List[Tuple[int, int]]) -> None:
        """Deposit pheromone on a path."""
        amount = self.Q / self.best_path_cost if self.best_path_cost > 0 else self.Q
        
        for i in range(len(path) - 1):
            edge = (path[i], path[i + 1])
            current_pheromone = self.pheromones.get(edge, self.tau0)
            self.pheromones[edge] = current_pheromone + amount
    
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
