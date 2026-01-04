from dataclasses import dataclass, field
from typing import List, Tuple


@dataclass
class GridWorld:
    width: int
    height: int
    start: Tuple[int, int]
    goal: Tuple[int, int]
    obstacles: List[Tuple[int, int]] = field(default_factory=list)

    def is_free(self, position: Tuple[int, int]) -> bool:
        r, c = position
        if (0 <= r < self.height) and (0 <= c < self.width) and (position not in self.obstacles):
            return True
        return False
    
    def neighbors(self, position: Tuple[int, int]) -> List[Tuple[int, int]]:
        r, c = position
        potential_moves = [(r-1, c), (r+1, c), (r, c-1), (r, c+1)]
        return [move for move in potential_moves if self.is_free(move)]
    
    def heuristic(self, position: Tuple[int, int]) -> float:
        return abs(position[0] - self.goal[0]) + abs(position[1] - self.goal[1])  

        