"""
Main entry point for running ant colony simulations.
"""

from gridworld import GridWorld
from simulation import AntColonySimulation
from config import SimulationConfig, DEFAULT_CONFIG
from statistics import get_statistics_summary


def run_simulation(config: SimulationConfig = None) -> AntColonySimulation:
    """
    Run a complete ant colony simulation.
    
    Args:
        config: SimulationConfig object. Defaults to DEFAULT_CONFIG if None.
    
    Returns:
        AntColonySimulation object with completed simulation.
    """
    if config is None:
        config = DEFAULT_CONFIG
    
    # Create world
    world = GridWorld(
        width=config.world_width,
        height=config.world_height,
        start=config.start_pos,
        goal=config.goal_pos,
        obstacles=config.obstacles
    )
    
    # Create simulation
    sim = AntColonySimulation(
        world=world,
        n_ants=config.n_ants,
        alpha=config.alpha,
        beta=config.beta,
        rho=config.rho,
        Q=config.Q,
        tau0=config.tau0,
        min_tau=config.min_tau,
        max_steps_per_ant=config.max_steps_per_ant,
        epsilon_explore=config.epsilon_explore,
        visit_limit=config.visit_limit,
    )
    
    print(f"Starting simulation with {config.n_ants} ants...")
    print(f"World: {config.world_width}x{config.world_height}")
    print(f"Goal: {config.goal_pos}\n")
    
    # Run simulation
    for timestep in range(config.max_timesteps):
        sim.step()
        
        # Dynamic pheromone deposition already handled in sim.step()
        
        # Print status every 100 timesteps
        if (timestep + 1) % 100 == 0:
            print(sim.get_status_report())
    
    # Final report
    print("\n=== SIMULATION COMPLETE ===")
    print(sim.get_status_report())
    
    if sim.best_path_found:
        print(f"\nBest path found: {len(sim.best_path_found) - 1} steps")
        print(f"Path: {sim.best_path_found[:5]}... (showing first 5 positions)")
    else:
        print("\nNo path to goal found.")
    
    return sim


def run_multiple_simulations(
    n_runs: int,
    config: SimulationConfig = None
) -> list:
    """
    Run multiple simulations and compare results.
    
    Args:
        n_runs: Number of simulations to run.
        config: SimulationConfig object.
    
    Returns:
        List of AntColonySimulation objects.
    """
    results = []
    best_cost = float("inf")
    best_sim = None
    
    for run in range(n_runs):
        print(f"\n{'='*50}")
        print(f"Run {run + 1}/{n_runs}")
        print(f"{'='*50}")
        sim = run_simulation(config)
        results.append(sim)
        
        if sim.best_path_cost < best_cost:
            best_cost = sim.best_path_cost
            best_sim = sim
    
    # Summary
    print(f"\n{'='*50}")
    print("SUMMARY OF ALL RUNS")
    print(f"{'='*50}")
    
    costs = [sim.best_path_cost for sim in results]
    valid_costs = [c for c in costs if c != float("inf")]
    
    if valid_costs:
        print(f"Best cost: {min(valid_costs)}")
        print(f"Average cost: {sum(valid_costs) / len(valid_costs):.2f}")
        print(f"Worst cost: {max(valid_costs)}")
        print(f"Success rate: {len(valid_costs)}/{n_runs}")
    else:
        print("No successful paths found in any run.")
    
    return results


if __name__ == "__main__":
    # Run a single simulation with default config
    sim = run_simulation()
    
    # results = run_multiple_simulations(3, DEFAULT_CONFIG)
