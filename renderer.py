import pygame
import sys
from typing import Tuple, Optional

from config import SimulationConfig, COMPLEX_MAZE
from simulation import AntColonySimulation
from menu import show_menu


CELL_SIZE = 15
WINDOW_WIDTH = 0  
WINDOW_HEIGHT = 0
FPS = 60


COLOR_BG = (20, 20, 30)           
COLOR_GRID = (40, 40, 50)         
COLOR_OBSTACLE = (80, 80, 90)     
COLOR_START = (0, 255, 100)       
COLOR_GOAL = (255, 50, 50)        
COLOR_OBJECTIVE = (100, 200, 255) # Light blue for objective
COLOR_ANT = (200, 200, 200)       
COLOR_PHEROMONE = (255, 165, 0)   
COLOR_PHEROMONE_EXPLORE = (255, 200, 120)
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
        self.show_pheromones = False  # Press P to toggle
        self.setup_mode = True  # Allow objective/obstacle setup before simulation
        self.sim_complete = False
        self.objective_pos = None
        self.iterations_to_goal = 0
        self.show_debug_info = False
        self.convergence_notified = False  # Track if we've announced convergence

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
                if self.setup_mode:
                    if event.key == pygame.K_RETURN:
                        # Start simulation
                        if self.objective_pos is not None:
                            self.start_simulation()
                        else:
                            print("Please set an objective (right-click on grid)")
                    elif event.key == pygame.K_r:
                        # Reset setup
                        self.objective_pos = None
                        self.world.obstacles = []
                else:
                    # Simulation mode controls
                    if event.key == pygame.K_SPACE:
                        self.paused = not self.paused
                    elif event.key == pygame.K_r:
                        self.reset_simulation()
                    elif event.key == pygame.K_p:
                        self.show_pheromones = not self.show_pheromones
                        print(f"Pheromone visualization: {'ON' if self.show_pheromones else 'OFF'}")

            # Mouse interaction
            if pygame.mouse.get_pressed()[0]:  # Left Click - Place obstacles
                mouse_x, mouse_y = pygame.mouse.get_pos()
                if mouse_y < self.height_px:
                    c = mouse_x // CELL_SIZE
                    r = mouse_y // CELL_SIZE
                    pos = (r, c)
                    
                    if self.setup_mode:
                        # In setup mode: left click places obstacles
                        if pos != self.world.start and pos != self.objective_pos:
                            if pos not in self.world.obstacles:
                                self.world.obstacles.append(pos)
                    else:
                        # During sim: can still add obstacles dynamically!
                        if pos != self.world.start and pos != self.objective_pos:
                            if pos not in self.world.obstacles:
                                self.world.obstacles.append(pos)
                                print(f"Added obstacle at {pos} - watch colony adapt!")
            
            if pygame.mouse.get_pressed()[2]:  # Right Click - Set objective/Remove obstacles
                mouse_x, mouse_y = pygame.mouse.get_pos()
                if mouse_y < self.height_px:
                    c = mouse_x // CELL_SIZE
                    r = mouse_y // CELL_SIZE
                    pos = (r, c)
                    
                    if self.setup_mode:
                        # In setup mode: right click sets objective
                        if pos != self.world.start:
                            self.objective_pos = pos
                            self.world.goal = pos
                    else:
                        # During sim: right click moves food - watch re-routing!
                        if pos != self.world.start and pos not in self.world.obstacles:
                            old_objective = self.objective_pos
                            self.objective_pos = pos
                            self.world.goal = pos
                            # Reset convergence tracking and best path since goal moved
                            self.sim.recent_paths.clear()
                            self.sim.best_path_found = None
                            self.sim.best_path_cost = float("inf")
                            self.sim.iterations_with_same_best = 0
                            self.sim.convergence_detected = False
                            self.sim.visit_counts.clear()
                            self.sim.restricted_cells.clear()
                            self.convergence_notified = False
                            print(f"Moved food from {old_objective} to {pos} - colony will re-route!")

    def start_simulation(self):
        """Start the simulation after setup phase."""
        self.setup_mode = False
        print(f"Starting simulation with objective at {self.objective_pos}")
        self.sim = AntColonySimulation(
            world=self.world,
            n_ants=self.config.n_ants,
            alpha=self.config.alpha,
            beta=self.config.beta,
            rho=self.config.rho,
            Q=self.config.Q,
            tau0=self.config.tau0,
            max_steps_per_ant=self.config.max_steps_per_ant,
            epsilon_explore=self.config.epsilon_explore,
            visit_limit=self.config.visit_limit,
        )

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
            tau0=self.config.tau0,
            max_steps_per_ant=self.config.max_steps_per_ant,
            epsilon_explore=self.config.epsilon_explore,
            visit_limit=self.config.visit_limit,
        )

    def draw(self):
        self.screen.fill(COLOR_BG)

        if self.sim_complete:
            self.draw_results_screen()
        elif self.setup_mode:
            self.draw_setup_screen()
        else:
            self.draw_simulation()

        pygame.display.flip()

    def draw_setup_screen(self):
        """Draw the setup phase screen."""
        # Draw grid and obstacles
        for r in range(self.world.height):
            for c in range(self.world.width):
                rect = (c * CELL_SIZE, r * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                
                if (r, c) in self.world.obstacles:
                    pygame.draw.rect(self.screen, COLOR_OBSTACLE, rect)
                else:
                    pygame.draw.rect(self.screen, COLOR_GRID, rect, 1)

        # Draw start position
        start_rect = (self.world.start[1] * CELL_SIZE, self.world.start[0] * CELL_SIZE, CELL_SIZE, CELL_SIZE)
        pygame.draw.rect(self.screen, COLOR_START, start_rect)
        pygame.draw.rect(self.screen, (255, 255, 255), start_rect, 2)

        # Draw objective if set
        if self.objective_pos:
            obj_rect = (self.objective_pos[1] * CELL_SIZE, self.objective_pos[0] * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            pygame.draw.rect(self.screen, COLOR_OBJECTIVE, obj_rect)
            pygame.draw.rect(self.screen, (255, 255, 255), obj_rect, 2)

        # UI instructions
        ui_rect = (0, self.height_px, self.width_px, 50)
        pygame.draw.rect(self.screen, (30, 30, 40), ui_rect)
        
        instructions = "SETUP - RClick: Set Food Location | LClick: Place Obstacles | ENTER: Start | R: Reset"
        objective_text = f"Food Location: {self.objective_pos if self.objective_pos else 'Not set (right-click to place)'}"
        
        text_surf = self.font.render(instructions, True, (100, 200, 255))
        obj_surf = self.font.render(objective_text, True, (100, 200, 255))
        
        self.screen.blit(text_surf, (10, self.height_px + 10))
        self.screen.blit(obj_surf, (10, self.height_px + 30))

    def draw_simulation(self):
        """Draw the main simulation."""
        # 1. Draw Grid & Obstacles
        for r in range(self.world.height):
            for c in range(self.world.width):
                rect = (c * CELL_SIZE, r * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                
                if (r, c) in self.world.obstacles:
                    pygame.draw.rect(self.screen, COLOR_OBSTACLE, rect)
                else:
                    pygame.draw.rect(self.screen, COLOR_GRID, rect, 1)

        # 2. Draw Pheromones (with transparency)
        if self.show_pheromones:
            pheromone_surface = pygame.Surface((self.width_px, self.height_px), pygame.SRCALPHA)
            
            max_food = max(self.sim.pheromones_food.values()) if self.sim.pheromones_food else 1.0
            max_explore = max(self.sim.pheromones_explore.values()) if self.sim.pheromones_explore else 1.0
            if max_food < 0.001:
                max_food = 0.001
            if max_explore < 0.001:
                max_explore = 0.001

            min_visible_pheromone = 0.0001

            # Draw exploration pheromones (lighter orange)
            for (start_node, end_node), strength in self.sim.pheromones_explore.items():
                if strength <= min_visible_pheromone:
                    continue
                start_px = self.get_pixel_pos(start_node)
                end_px = self.get_pixel_pos(end_node)
                normalized = strength / max_explore
                intensity = min(1.0, normalized ** 0.5)
                alpha = max(30, int(180 * intensity))
                color = (*COLOR_PHEROMONE_EXPLORE, alpha)
                pygame.draw.line(pheromone_surface, color, start_px, end_px, 2)

            # Draw food pheromones (strong orange)
            for (start_node, end_node), strength in self.sim.pheromones_food.items():
                if strength <= min_visible_pheromone:
                    continue
                start_px = self.get_pixel_pos(start_node)
                end_px = self.get_pixel_pos(end_node)
                normalized = strength / max_food
                intensity = min(1.0, normalized ** 0.5)
                alpha = max(60, int(255 * intensity))
                color = (*COLOR_PHEROMONE, alpha)
                pygame.draw.line(pheromone_surface, color, start_px, end_px, 2)
            
            self.screen.blit(pheromone_surface, (0, 0))

        # 3. Draw Best Path
        if self.sim.best_path_found:
            path = self.sim.best_path_found
            if len(path) > 1:
                points = [self.get_pixel_pos(p) for p in path]
                pygame.draw.lines(self.screen, COLOR_BEST_PATH, False, points, 3)
        
        # 4. Draw Colony (Start Position) - Large green marker
        colony_px = self.get_pixel_pos(self.world.start)
        pygame.draw.circle(self.screen, COLOR_START, colony_px, 8)
        pygame.draw.circle(self.screen, (255, 255, 255), colony_px, 8, 2)  # White outline

        # 5. Draw Ants
        for ant in self.sim.ants:
            # Different colors based on state
            if ant.returning_home:
                # Red for ants returning with food
                color = (255, 100, 100)
            elif ant.has_food:
                # Already has food but just arrived
                color = (255, 150, 100)
            else:
                # Normal foraging
                color = COLOR_ANT
            
            pos_px = self.get_pixel_pos(ant.position)
            pygame.draw.circle(self.screen, color, pos_px, 3)

        # 5. Draw Start and Objective
        start_rect = (self.world.start[1] * CELL_SIZE, self.world.start[0] * CELL_SIZE, CELL_SIZE, CELL_SIZE)
        obj_rect = (self.objective_pos[1] * CELL_SIZE, self.objective_pos[0] * CELL_SIZE, CELL_SIZE, CELL_SIZE)
        pygame.draw.rect(self.screen, COLOR_START, start_rect)
        pygame.draw.rect(self.screen, COLOR_OBJECTIVE, obj_rect)
        pygame.draw.rect(self.screen, (255, 255, 255), start_rect, 2)
        pygame.draw.rect(self.screen, (255, 255, 255), obj_rect, 2)

        # 6. UI Stats Bar
        ui_rect = (0, self.height_px, self.width_px, 50)
        pygame.draw.rect(self.screen, (30, 30, 40), ui_rect)
        
        is_stable, stability = self.sim.get_convergence_status()
        status_indicator = "[STABLE]" if is_stable else ""
        stats_text = f"Step: {self.sim.timestep} | Best: {self.sim.best_path_cost:.0f} | Stability: {stability*100:.0f}% {status_indicator}"
        controls_text = "SPACE: Pause | P: Pheromones | LClick: +Obstacle | RClick: Move Food | R: Reset"
        
        text_surf = self.font.render(stats_text, True, (100, 255, 100) if is_stable else (255, 255, 255))
        control_surf = self.font.render(controls_text, True, (150, 150, 150))
        
        self.screen.blit(text_surf, (10, self.height_px + 10))
        self.screen.blit(control_surf, (10, self.height_px + 30))

    def draw_results_screen(self):
        """Draw the results screen when simulation completes."""
        # Semi-transparent overlay
        overlay = pygame.Surface((self.width_px, self.height_px + 50))
        overlay.set_alpha(200)
        overlay.fill((10, 10, 15))
        self.screen.blit(overlay, (0, 0))

        # Results text
        font_title = pygame.font.SysFont("monospace", 24, bold=True)
        font_large = pygame.font.SysFont("monospace", 18)
        font_normal = pygame.font.SysFont("monospace", 14)

        title = font_title.render("OPTIMAL PATH FOUND", True, (100, 200, 100))
        
        results = [
            f"Iterations to convergence: {self.iterations_to_goal}",
            f"Optimal path length: {self.sim.best_path_cost:.0f} steps",
            f"Number of ants: {self.sim.n_ants}",
            f"Grid size: {self.world.width}x{self.world.height}",
            f"",
            f"The colony optimized the path after finding",
            f"food multiple times and reinforcing good routes."
        ]

        # Draw title
        title_y = 80
        self.screen.blit(title, (self.width_px // 2 - title.get_width() // 2, title_y))

        # Draw results
        y_offset = title_y + 60
        for result_text in results:
            if result_text:
                text_surf = font_large.render(result_text, True, (200, 200, 200))
            else:
                text_surf = font_large.render(result_text, True, (200, 200, 200))
            self.screen.blit(text_surf, (self.width_px // 2 - text_surf.get_width() // 2, y_offset))
            y_offset += 35

        # Instructions
        instructions = font_normal.render("Press ENTER to return to menu or R to run again", True, (150, 150, 150))
        self.screen.blit(instructions, (self.width_px // 2 - instructions.get_width() // 2, y_offset + 20))

    def run(self):
        while self.running:
            self.handle_input()
            
            if self.sim_complete:
                # In results screen, waiting for user input
                for event in pygame.event.get():
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_RETURN:
                            self.running = False
                        elif event.key == pygame.K_r:
                            self.reset_to_setup()
            elif not self.paused and not self.setup_mode:
                # Running simulation
                self.sim.step()
                
                # Check for convergence (but don't stop!)
                is_converged, stability = self.sim.get_convergence_status()
                if is_converged and not self.convergence_notified:
                    self.convergence_notified = True
                    print(f"\n{'='*60}")
                    print(f"CONVERGENCE DETECTED at iteration {self.sim.timestep}!")
                    print(f"Route stability: {stability*100:.1f}% of ants using best path")
                    print(f"Best path length: {self.sim.best_path_cost:.0f}")
                    print(f"Simulation continues - try moving food or adding obstacles!")
                    print(f"{'='*60}\n")
                
                # Dynamic pheromone deposition already handled in simulation.step()

            self.draw()
            self.clock.tick(FPS)

    def check_simulation_complete(self) -> bool:
        """Check if simulation should end (optimal path converged)."""
        # Simulation ends when best path has converged (no improvement for N iterations)
        return self.sim.is_converged()

    def reset_to_setup(self):
        """Reset simulation and return to setup mode."""
        self.setup_mode = True
        self.sim_complete = False
        self.iterations_to_goal = 0
        self.objective_pos = None
        self.world.obstacles = []
        print("Reset to setup mode")


if __name__ == "__main__":
    # Show configuration menu
    config = show_menu()
    
    if config is None:
        print("Simulation cancelled")
        sys.exit()
    
    # Adjust config for better visual settings if needed
    viz = AntColonyVisualizer(config)
    viz.run()
