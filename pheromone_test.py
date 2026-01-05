from typing import List, Tuple
from gridworld import GridWorld
from pheromones import init_pheromones
from ants import construct_random_path
import random




def print_ascii(world: GridWorld) -> None:
    for r in range(world.height):
        row = []
        for c in range(world.width):
            pos = (r, c)
            if pos == world.start:
                row.append("S")
            elif pos == world.goal:
                row.append("G")
            elif pos in world.obstacles:
                row.append("#")
            else:
                row.append(".")
        print(" ".join(row))
    print()

def create_random_world() -> GridWorld:
    start = (0, 0)
    obstacle_limit = random.randint(5, 10)
    height = random.randint(5, 15)
    width = random.randint(5, 15)
    goal = (random.randint(0, height - 1), random.randint(0, width - 1))
    world = GridWorld(width=width, height=height, start=start, goal=goal)
    for _ in range(obstacle_limit):
        pos = (random.randint(0, height - 1), random.randint(0, width - 1))
        if pos != start and pos != goal and pos not in world.obstacles:
            world.obstacles.append(pos)
    
    return world


def main():

    succeses = 0
    shorterst_path = 10000
    test_cases = 100

    for i in range(test_cases):
        print(f"Test Case {i+1}:")
        world = create_random_world()
        print_ascii(world)

        pher = init_pheromones(world, tau=1.0)
        print(f"Initialized {len(pher)} Pheromones\n")

        assert len(pher) == sum(len(world.neighbors((r, c))) for r in range(world.height) for c in range(world.width) if world.is_free((r, c)))

        path = construct_random_path(world, max_steps=200)
        print(f"Constructed Path ({len(path)} steps): {path}\n")

        if path[-1] == world.goal:
            succeses += 1
            print("Path successfully reached the goal!\n")
        
        if len(path) < shorterst_path or i == 0:
            shorterst_path = len(path)

    print(f"Total Successes: {succeses} out of {test_cases}")
    print(f"Shortest path: {shorterst_path}")

if __name__ == "__main__":
    main()