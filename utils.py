"""
Utility functions for analysis and debugging ant colony simulations.
"""

from typing import List, Tuple, Dict
from gridworld import GridWorld
from ants import Ant
from pheromones import get_pheromone


def analyze_pheromone_distribution(pheromones: Dict) -> Dict[str, float]:
    """
    Analyze the distribution of pheromones in the system.
    
    Returns:
        Dictionary with statistics about pheromone levels.
    """
    if not pheromones:
        return {"total": 0, "max": 0, "min": 0, "average": 0, "count": 0}
    
    values = list(pheromones.values())
    return {
        "total": sum(values),
        "max": max(values),
        "min": min(values),
        "average": sum(values) / len(values),
        "count": len(values),
        "std_dev": (sum((x - sum(values) / len(values)) ** 2 for x in values) / len(values)) ** 0.5
    }


def get_strongest_edges(
    pheromones: Dict[Tuple[Tuple[int, int], Tuple[int, int]], float],
    n: int = 10
) -> List[Tuple[Tuple[Tuple[int, int], Tuple[int, int]], float]]:
    """
    Get the n edges with the highest pheromone levels.
    
    Args:
        pheromones: Pheromone dictionary.
        n: Number of top edges to return.
    
    Returns:
        List of (edge, pheromone_level) tuples sorted by pheromone level.
    """
    sorted_edges = sorted(pheromones.items(), key=lambda x: x[1], reverse=True)
    return sorted_edges[:n]


def get_weakest_edges(
    pheromones: Dict[Tuple[Tuple[int, int], Tuple[int, int]], float],
    n: int = 10
) -> List[Tuple[Tuple[Tuple[int, int], Tuple[int, int]], float]]:
    """
    Get the n edges with the lowest pheromone levels.
    
    Args:
        pheromones: Pheromone dictionary.
        n: Number of bottom edges to return.
    
    Returns:
        List of (edge, pheromone_level) tuples sorted by pheromone level.
    """
    sorted_edges = sorted(pheromones.items(), key=lambda x: x[1])
    return sorted_edges[:n]


def analyze_ant_performance(ants: List[Ant], world: GridWorld) -> Dict:
    """
    Analyze performance metrics for all ants.
    
    Returns:
        Dictionary with performance statistics.
    """
    successful_ants = [ant for ant in ants if ant.has_food]
    all_path_lengths = [len(ant.path) for ant in ants]
    successful_path_lengths = [len(ant.path) for ant in successful_ants]
    
    return {
        "total_ants": len(ants),
        "successful_ants": len(successful_ants),
        "success_rate": len(successful_ants) / len(ants) if ants else 0,
        "avg_path_length": sum(all_path_lengths) / len(all_path_lengths) if all_path_lengths else 0,
        "min_path_length": min(all_path_lengths) if all_path_lengths else 0,
        "max_path_length": max(all_path_lengths) if all_path_lengths else 0,
        "avg_successful_path": sum(successful_path_lengths) / len(successful_path_lengths) if successful_path_lengths else 0,
        "best_path_length": min(successful_path_lengths) if successful_path_lengths else float("inf"),
    }


def find_pheromone_trails(
    pheromones: Dict[Tuple[Tuple[int, int], Tuple[int, int]], float],
    threshold: float = 0.5
) -> List[List[Tuple[int, int]]]:
   
    # Create adjacency list for strong edges
    strong_edges = {edge: pheromone for edge, pheromone in pheromones.items() 
                   if pheromone >= threshold}
    
    # Build graph
    graph: Dict[Tuple[int, int], List[Tuple[int, int]]] = {}
    for (from_pos, to_pos) in strong_edges.keys():
        if from_pos not in graph:
            graph[from_pos] = []
        graph[from_pos].append(to_pos)
    
    # Find trails using DFS-like approach
    trails = []
    visited_edges = set()
    
    for start_node in graph:
        trail = [start_node]
        current = start_node
        
        while current in graph and graph[current]:
            next_node = graph[current][0]
            edge = (current, next_node)
            
            if edge in visited_edges:
                break
            
            visited_edges.add(edge)
            trail.append(next_node)
            current = next_node
        
        if len(trail) > 1:
            trails.append(trail)
    
    return trails


def ant_path_efficiency(path: List[Tuple[int, int]], world: GridWorld) -> float:
    if len(path) < 2:
        return 0.0
    
    optimal_distance = world.distance(path[0], path[-1])
    actual_distance = len(path) - 1
    
    if actual_distance == 0:
        return 0.0
    
    return optimal_distance / actual_distance


def convergence_analysis(
    cost_history: List[float],
    window_size: int = 10
) -> Dict[str, float]:
    
    if len(cost_history) < 2:
        return {"convergence_rate": 0, "improvement": 0}
    
    first_half = cost_history[:len(cost_history)//2]
    second_half = cost_history[len(cost_history)//2:]
    
    avg_first = sum(first_half) / len(first_half) if first_half else float("inf")
    avg_second = sum(second_half) / len(second_half) if second_half else float("inf")
    
    improvement = (avg_first - avg_second) / avg_first if avg_first != float("inf") else 0
    convergence_rate = (cost_history[0] - cost_history[-1]) / cost_history[0] if cost_history[0] > 0 else 0
    
    return {
        "first_half_avg": avg_first,
        "second_half_avg": avg_second,
        "improvement": improvement,
        "convergence_rate": convergence_rate,
        "final_cost": cost_history[-1],
        "initial_cost": cost_history[0]
    }


def print_analysis_report(
    ants: List[Ant],
    pheromones: Dict,
    world: GridWorld,
    cost_history: List[float] = None
) -> None:
   
    print("\n" + "="*50)
    print("DETAILED ANALYSIS REPORT")
    print("="*50)
    
    # Ant performance
    ant_perf = analyze_ant_performance(ants, world)
    print("\n--- Ant Performance ---")
    print(f"Total ants: {ant_perf['total_ants']}")
    print(f"Successful ants: {ant_perf['successful_ants']}")
    print(f"Success rate: {ant_perf['success_rate']:.2%}")
    print(f"Best path found: {ant_perf['best_path_length']}")
    print(f"Average path length: {ant_perf['avg_path_length']:.2f}")
    
    # Pheromone analysis
    pheromone_stats = analyze_pheromone_distribution(pheromones)
    print("\n--- Pheromone Distribution ---")
    print(f"Total pheromone: {pheromone_stats['total']:.4f}")
    print(f"Average per edge: {pheromone_stats['average']:.6f}")
    print(f"Max per edge: {pheromone_stats['max']:.6f}")
    print(f"Min per edge: {pheromone_stats['min']:.6f}")
    
    # Strong edges
    strongest = get_strongest_edges(pheromones, n=5)
    print("\n--- Top 5 Strongest Edges ---")
    for i, (edge, pheromone) in enumerate(strongest, 1):
        print(f"{i}. {edge}: {pheromone:.6f}")
    
    # Convergence analysis
    if cost_history:
        conv = convergence_analysis(cost_history)
        print("\n--- Convergence Analysis ---")
        print(f"Initial cost: {conv['initial_cost']}")
        print(f"Final cost: {conv['final_cost']}")
        print(f"Convergence rate: {conv['convergence_rate']:.2%}")
        print(f"Improvement: {conv['improvement']:.2%}")
    
    print("="*50 + "\n")
