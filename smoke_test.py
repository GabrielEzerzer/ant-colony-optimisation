from typing import List, Tuple
from gridworld import GridWorld


def print_ascii(world: GridWorld) -> None:
    for y in range(world.height):
        row = []
        for x in range(world.width):
            pos = (x, y)
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


def main():
    width, height = 5, 5
    obstacles: List[Tuple[int, int]] = [(3, 0), (1, 1), (3, 1), (1, 2)]
    start = (0, 0)
    goal = (4, 4)

    world = GridWorld(width=width, height=height, obstacles=obstacles, start=start, goal=goal)

    print("ASCII map:")
    print_ascii(world)


    tests = [(0, 0), (3, 0), (-1, 0), (4, 4)]
    for pos in tests:
        print(f"is_free({pos}) -> {world.is_free(pos)}")

    print()


    points = [(0, 0), (2, 1), (4, 4)]
    for p in points:
        print(f"neighbors of {p} -> {world.neighbors(p)}")

    print()


    for p in [(0, 0), (2, 2), (4, 4)]:
        print(f"heuristic({p}) -> {world.heuristic(p)}")


if __name__ == "__main__":
    main()
