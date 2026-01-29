import pygame
import sys
from typing import Tuple


from config import SimulationConfig, COMPLEX_MAZE
from simulation import AntColonySimulation


CELL_SIZE = 15
WINDOW_WIDTH = 0  
WINDOW_HEIGHT = 0
FPS = 60


COLOR_BG = (20, 20, 30)           
COLOR_GRID = (40, 40, 50)         
COLOR_OBSTACLE = (80, 80, 90)     
COLOR_START = (0, 255, 100)       
COLOR_GOAL = (255, 50, 50)        
COLOR_ANT = (200, 200, 200)       
COLOR_PHEROMONE = (0, 255, 150)   
COLOR_BEST_PATH = (255, 215, 0)   


class AntColonyVisualizer:
    def __init__(self, config: SimulationConfig):
        pygame.init()
        self.config = config
        
        # Create world first
        from gridworld import GridWorld
        self.world = GridWorld(
            width=config.world_width,
            height=config.world_height,
            start=config.start_pos,
            goal=config.goal_pos,
            obstacles=list(config.obstacles) if config.obstacles else []
        )

        # Initialize Simulation with the world
        self.sim = AntColonySimulation(
            world=self.world,
            n_ants=config.n_ants,
            alpha=config.alpha,
            beta=config.beta,
            rho=config.rho,
            Q=config.Q,
            tau0=config.tau0,
            max_steps_per_ant=config.max_steps_per_ant
        )

        # Window Setup
        self.width_px = self.world.width * CELL_SIZE
        self.height_px = self.world.height * CELL_SIZE
        self.screen = pygame.display.set_mode((self.width_px, self.height_px + 50))  # +50 for UI stats
        pygame.display.set_caption("Ant Colony Optimization Simulator")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("monospace", 14)

        # Interaction State
        self.paused = False
        self.running = True
        self.show_pheromones = True

    def get_pixel_pos(self, grid_pos: Tuple[int, int]) -> Tuple[int, int]:
        """Convert grid (row, col) to pixel (x, y) center."""
        r, c = grid_pos
        return (c * CELL_SIZE + CELL_SIZE // 2, r * CELL_SIZE + CELL_SIZE // 2)

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                pygame.quit()
                sys.exit()
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.paused = not self.paused
                elif event.key == pygame.K_r:
                    self.reset_simulation()
                elif event.key == pygame.K_p:
                    self.show_pheromones = not self.show_pheromones

            # Mouse interaction: Add/Remove obstacles
            if pygame.mouse.get_pressed()[0]:  # Left Click
                mouse_x, mouse_y = pygame.mouse.get_pos()
                if mouse_y < self.height_px:
                    c = mouse_x // CELL_SIZE
                    r = mouse_y // CELL_SIZE
                    pos = (r, c)
                    if pos != self.world.start and pos != self.world.goal:
                        if pos not in self.world.obstacles:
                            self.world.obstacles.append(pos)
            
            if pygame.mouse.get_pressed()[2]:  # Right Click (Remove)
                mouse_x, mouse_y = pygame.mouse.get_pos()
                if mouse_y < self.height_px:
                    c = mouse_x // CELL_SIZE
                    r = mouse_y // CELL_SIZE
                    pos = (r, c)
                    if pos in self.world.obstacles:
                        self.world.obstacles.remove(pos)

    def reset_simulation(self):
        print("Resetting simulation...")
        # Create a fresh simulation instance
        self.sim = AntColonySimulation(
            world=self.world,
            n_ants=self.config.n_ants,
            alpha=self.config.alpha,
            beta=self.config.beta,
            rho=self.config.rho,
            Q=self.config.Q,
            tau0=self.config.tau0
        )

    def draw(self):
        self.screen.fill(COLOR_BG)

        # 1. Draw Grid & Obstacles
        for r in range(self.world.height):
            for c in range(self.world.width):
                rect = (c * CELL_SIZE, r * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                
                # Draw Obstacle
                if (r, c) in self.world.obstacles:
                    pygame.draw.rect(self.screen, COLOR_OBSTACLE, rect)
                else:
                    # Faint grid lines
                    pygame.draw.rect(self.screen, COLOR_GRID, rect, 1)

        # 2. Draw Pheromones (with transparency)
        if self.show_pheromones:
            # We use a separate surface for alpha blending
            pheromone_surface = pygame.Surface((self.width_px, self.height_px), pygame.SRCALPHA)
            
            max_pheromone = max(self.sim.pheromones.values()) if self.sim.pheromones else 1.0
            if max_pheromone == 0:
                max_pheromone = 1.0

            # Optimization: Only draw strong edges to save FPS
            for (start_node, end_node), strength in self.sim.pheromones.items():
                if strength <= self.config.min_tau * 1.5:
                    continue
                
                start_px = self.get_pixel_pos(start_node)
                end_px = self.get_pixel_pos(end_node)
                
                # Normalize strength 0.0 to 1.0 for opacity
                intensity = min(1.0, strength / (max_pheromone * 0.8))  # 0.8 scaling factor to make trails brighter
                alpha = int(255 * intensity)
                
                color = (*COLOR_PHEROMONE, alpha)
                pygame.draw.line(pheromone_surface, color, start_px, end_px, 2)
            
            self.screen.blit(pheromone_surface, (0, 0))

        # 3. Draw Best Path
        if self.sim.best_path_found:
            path = self.sim.best_path_found
            if len(path) > 1:
                points = [self.get_pixel_pos(p) for p in path]
                pygame.draw.lines(self.screen, COLOR_BEST_PATH, False, points, 3)

        # 4. Draw Ants
        for ant in self.sim.ants:
            # Skip ants that finished to reduce clutter
            if ant.has_food:
                continue
            
            pos_px = self.get_pixel_pos(ant.position)
            pygame.draw.circle(self.screen, COLOR_ANT, pos_px, 3)

        # 5. Draw Start and Goal
        start_rect = (self.world.start[1] * CELL_SIZE, self.world.start[0] * CELL_SIZE, CELL_SIZE, CELL_SIZE)
        goal_rect = (self.world.goal[1] * CELL_SIZE, self.world.goal[0] * CELL_SIZE, CELL_SIZE, CELL_SIZE)
        pygame.draw.rect(self.screen, COLOR_START, start_rect)
        pygame.draw.rect(self.screen, COLOR_GOAL, goal_rect)
        
        # Label Start/Goal
        pygame.draw.rect(self.screen, (255, 255, 255), start_rect, 2)
        pygame.draw.rect(self.screen, (255, 255, 255), goal_rect, 2)

        # 6. UI Stats Bar
        ui_rect = (0, self.height_px, self.width_px, 50)
        pygame.draw.rect(self.screen, (30, 30, 40), ui_rect)
        
        stats_text = f"Step: {self.sim.timestep} | Ants: {self.sim.n_ants} | Best Cost: {self.sim.best_path_cost}"
        controls_text = "SPACE: Pause | R: Reset | P: Pheromones | LClick: +Obstacle | RClick: -Obstacle"
        
        text_surf = self.font.render(stats_text, True, (255, 255, 255))
        control_surf = self.font.render(controls_text, True, (150, 150, 150))
        
        self.screen.blit(text_surf, (10, self.height_px + 10))
        self.screen.blit(control_surf, (10, self.height_px + 30))

        pygame.display.flip()

    def run(self):
        while self.running:
            self.handle_input()
            
            if not self.paused:
                self.sim.step()
                
                # Apply pheromone update periodically 
                if self.sim.timestep % 10 == 0:  
                    self.sim.apply_pheromone_update()

            self.draw()
            self.clock.tick(FPS)


if __name__ == "__main__":

    config = COMPLEX_MAZE
    
    config.n_ants = 100
    
    viz = AntColonyVisualizer(config)
    viz.run()
