import pygame
import sys
from typing import Optional, Tuple
from config import SimulationConfig, DEFAULT_CONFIG, SMALL_WORLD, LARGE_WORLD, COMPLEX_MAZE


# Colors
COLOR_BG = (20, 20, 30)
COLOR_PANEL = (30, 30, 45)
COLOR_TEXT = (255, 255, 255)
COLOR_LABEL = (180, 180, 200)
COLOR_INPUT_BG = (45, 45, 60)
COLOR_INPUT_BORDER = (100, 100, 150)
COLOR_BUTTON = (70, 100, 180)
COLOR_BUTTON_HOVER = (90, 120, 200)
COLOR_BUTTON_ACTIVE = (100, 200, 100)
COLOR_PRESET_SELECTED = (100, 200, 100)
COLOR_ERROR = (255, 100, 100)


class TextInput:
    """Text input field for configuration."""
    def __init__(self, x: int, y: int, width: int, height: int, label: str, initial_value: str = ""):
        self.rect = pygame.Rect(x, y, width, height)
        self.label = label
        self.text = initial_value
        self.active = False
        self.error = False
        self.label_rect = pygame.Rect(x, y - 30, width, 25)

    def draw(self, surface: pygame.Surface, font: pygame.font.Font, label_font: pygame.font.Font):
        # Draw label
        label_surf = label_font.render(self.label, True, COLOR_LABEL)
        surface.blit(label_surf, self.label_rect)

        # Draw input box
        border_color = COLOR_ERROR if self.error else (COLOR_INPUT_BORDER if self.active else COLOR_INPUT_BG)
        pygame.draw.rect(surface, COLOR_INPUT_BG, self.rect)
        pygame.draw.rect(surface, border_color, self.rect, 2)

        # Draw text
        text_surf = font.render(self.text, True, COLOR_TEXT)
        text_rect = text_surf.get_rect(midleft=(self.rect.x + 10, self.rect.centery))
        surface.blit(text_surf, text_rect)

    def handle_event(self, event: pygame.event.EventType) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
            self.error = False
        elif event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key == pygame.K_RETURN:
                self.active = False
            elif len(self.text) < 20:  # Limit input length
                if event.unicode.isdigit() or event.unicode == '.':
                    self.text += event.unicode

    def get_value(self) -> Optional[float]:
        """Get numeric value, return None if invalid."""
        if not self.text:
            return None
        try:
            if '.' in self.text:
                return float(self.text)
            return float(self.text)
        except ValueError:
            self.error = True
            return None


class Button:
    """Clickable button."""
    def __init__(self, x: int, y: int, width: int, height: int, label: str):
        self.rect = pygame.Rect(x, y, width, height)
        self.label = label
        self.hovered = False

    def draw(self, surface: pygame.Surface, font: pygame.font.Font):
        color = COLOR_BUTTON_HOVER if self.hovered else COLOR_BUTTON
        pygame.draw.rect(surface, color, self.rect)
        pygame.draw.rect(surface, COLOR_TEXT, self.rect, 2)

        text_surf = font.render(self.label, True, COLOR_TEXT)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

    def handle_event(self, event: pygame.event.EventType) -> bool:
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.hovered:
                return True
        return False


class PresetButton:
    """Preset configuration button."""
    def __init__(self, x: int, y: int, width: int, height: int, name: str, config: SimulationConfig):
        self.rect = pygame.Rect(x, y, width, height)
        self.name = name
        self.config = config
        self.selected = False
        self.hovered = False

    def draw(self, surface: pygame.Surface, font: pygame.font.Font):
        color = COLOR_PRESET_SELECTED if self.selected else (COLOR_BUTTON_HOVER if self.hovered else COLOR_BUTTON)
        pygame.draw.rect(surface, color, self.rect)
        pygame.draw.rect(surface, COLOR_TEXT, self.rect, 2)

        text_surf = font.render(self.name, True, COLOR_TEXT)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

    def handle_event(self, event: pygame.event.EventType) -> bool:
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.hovered:
                return True
        return False


class StartMenu:
    """Configuration menu for ant colony simulation."""

    def __init__(self, width: int = 1200, height: int = 800):
        pygame.init()
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Ant Colony Simulator - Configuration")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("monospace", 14)
        self.font_large = pygame.font.SysFont("monospace", 18, bold=True)
        self.font_title = pygame.font.SysFont("monospace", 24, bold=True)

        # Current configuration
        self.config = DEFAULT_CONFIG

        # UI Elements
        self.setup_ui_elements()

    def setup_ui_elements(self):
        """Create all UI input fields and buttons."""
        start_x = 50
        start_y = 150
        col_width = 300
        row_height = 80

        # Column 1: World configuration
        self.input_width = TextInput(start_x, start_y, 250, 35, "Grid Width:", str(self.config.world_width))
        self.input_height = TextInput(start_x, start_y + row_height, 250, 35, "Grid Height:", str(self.config.world_height))
        self.input_ants = TextInput(start_x, start_y + row_height * 2, 250, 35, "Number of Ants:", str(self.config.n_ants))
        self.input_max_steps = TextInput(start_x, start_y + row_height * 3, 250, 35, "Max Steps per Ant:", str(self.config.max_steps_per_ant))

        # Column 2: ACO parameters
        col2_x = start_x + col_width
        self.input_alpha = TextInput(col2_x, start_y, 250, 35, "Alpha (Pheromone):", str(self.config.alpha))
        self.input_beta = TextInput(col2_x, start_y + row_height, 250, 35, "Beta (Heuristic):", str(self.config.beta))
        self.input_rho = TextInput(col2_x, start_y + row_height * 2, 250, 35, "Rho (Evaporation):", str(self.config.rho))
        self.input_q = TextInput(col2_x, start_y + row_height * 3, 250, 35, "Q (Pheromone Deposit):", str(self.config.Q))

        # Column 3: Advanced parameters
        col3_x = start_x + col_width * 2
        self.input_tau0 = TextInput(col3_x, start_y, 250, 35, "Tau0 (Initial Pheromone):", str(self.config.tau0))
        self.input_timesteps = TextInput(col3_x, start_y + row_height, 250, 35, "Max Timesteps:", str(self.config.max_timesteps))

        # Preset buttons
        preset_y = start_y + row_height * 5 + 30
        self.presets = [
            PresetButton(start_x, preset_y, 140, 40, "Small World", SMALL_WORLD),
            PresetButton(start_x + 150, preset_y, 140, 40, "Default", DEFAULT_CONFIG),
            PresetButton(start_x + 300, preset_y, 140, 40, "Large World", LARGE_WORLD),
            PresetButton(start_x + 450, preset_y, 140, 40, "Complex Maze", COMPLEX_MAZE),
        ]
        self.presets[1].selected = True  # Default selected

        # Buttons
        button_y = preset_y + 80
        self.button_start = Button(start_x, button_y, 200, 50, "START SIMULATION")
        self.button_reset = Button(start_x + 220, button_y, 200, 50, "RESET TO DEFAULT")

        # Status message
        self.status_message = ""
        self.status_color = COLOR_TEXT

    def load_preset(self, config: SimulationConfig):
        """Load a preset configuration into the input fields."""
        self.config = config

        self.input_width.text = str(config.world_width)
        self.input_height.text = str(config.world_height)
        self.input_ants.text = str(config.n_ants)
        self.input_max_steps.text = str(config.max_steps_per_ant)
        self.input_alpha.text = str(config.alpha)
        self.input_beta.text = str(config.beta)
        self.input_rho.text = str(config.rho)
        self.input_q.text = str(config.Q)
        self.input_tau0.text = str(config.tau0)
        self.input_timesteps.text = str(config.max_timesteps)

        self.status_message = "Loaded preset configuration"
        self.status_color = COLOR_BUTTON_ACTIVE

    def build_config_from_inputs(self) -> Optional[SimulationConfig]:
        """Build configuration from input fields with validation."""
        try:
            width = int(self.input_width.get_value())
            height = int(self.input_height.get_value())
            n_ants = int(self.input_ants.get_value())
            max_steps = int(self.input_max_steps.get_value())
            alpha = float(self.input_alpha.get_value())
            beta = float(self.input_beta.get_value())
            rho = float(self.input_rho.get_value())
            q = float(self.input_q.get_value())
            tau0 = float(self.input_tau0.get_value())
            timesteps = int(self.input_timesteps.get_value())

            # Validate ranges
            if width < 10 or width > 200:
                raise ValueError("Grid width must be between 10 and 200")
            if height < 10 or height > 200:
                raise ValueError("Grid height must be between 10 and 200")
            if n_ants < 1 or n_ants > 500:
                raise ValueError("Number of ants must be between 1 and 500")
            if not (0 <= rho < 1):
                raise ValueError("Rho must be between 0 and 1")
            if q <= 0:
                raise ValueError("Q must be positive")
            if tau0 <= 0:
                raise ValueError("Tau0 must be positive")

            config = SimulationConfig(
                world_width=width,
                world_height=height,
                start_pos=(0, 0),
                goal_pos=(height - 1, width - 1),
                n_ants=n_ants,
                max_steps_per_ant=max_steps,
                alpha=alpha,
                beta=beta,
                rho=rho,
                Q=q,
                tau0=tau0,
                max_timesteps=timesteps,
                obstacles=[]
            )

            return config

        except ValueError as e:
            self.status_message = f"Error: {str(e)}"
            self.status_color = COLOR_ERROR
            return None

    def handle_events(self) -> Optional[SimulationConfig]:
        """Handle input events. Returns config if simulation should start."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            # Text inputs
            for input_field in [
                self.input_width, self.input_height, self.input_ants, self.input_max_steps,
                self.input_alpha, self.input_beta, self.input_rho, self.input_q,
                self.input_tau0, self.input_timesteps
            ]:
                input_field.handle_event(event)

            # Preset buttons
            for i, preset in enumerate(self.presets):
                if preset.handle_event(event):
                    # Deselect all
                    for p in self.presets:
                        p.selected = False
                    # Select this one
                    preset.selected = True
                    # Load configuration
                    self.load_preset(preset.config)

            # Start button
            if self.button_start.handle_event(event):
                config = self.build_config_from_inputs()
                if config:
                    return config

            # Reset button
            if self.button_reset.handle_event(event):
                self.load_preset(DEFAULT_CONFIG)
                for i, preset in enumerate(self.presets):
                    preset.selected = (i == 1)

        return None

    def draw(self):
        """Draw the entire menu."""
        self.screen.fill(COLOR_BG)

        # Title
        title_surf = self.font_title.render("Ant Colony Simulator - Configuration", True, COLOR_TEXT)
        self.screen.blit(title_surf, (50, 10))

        # Draw all input fields
        for input_field in [
            self.input_width, self.input_height, self.input_ants, self.input_max_steps,
            self.input_alpha, self.input_beta, self.input_rho, self.input_q,
            self.input_tau0, self.input_timesteps
        ]:
            input_field.draw(self.screen, self.font, self.font_large)

        # Draw section labels
        self.screen.blit(
            self.font_large.render("World Configuration", True, COLOR_LABEL),
            (50, 115)
        )
        self.screen.blit(
            self.font_large.render("ACO Parameters", True, COLOR_LABEL),
            (350, 115)
        )
        self.screen.blit(
            self.font_large.render("Advanced", True, COLOR_LABEL),
            (650, 115)
        )

        # Draw presets label
        preset_label = self.font_large.render("Presets:", True, COLOR_LABEL)
        self.screen.blit(preset_label, (50, 480))

        # Draw preset buttons
        for preset in self.presets:
            preset.draw(self.screen, self.font)

        # Draw action buttons
        self.button_start.draw(self.screen, self.font_large)
        self.button_reset.draw(self.screen, self.font_large)

        # Draw status message
        if self.status_message:
            status_surf = self.font.render(self.status_message, True, self.status_color)
            self.screen.blit(status_surf, (50, self.height - 50))

        # Draw info
        info_text = (
            "Configure the simulation parameters above and click START SIMULATION to begin. "
            "Select a preset or enter custom values."
        )
        info_surf = self.font.render(info_text, True, COLOR_LABEL)
        self.screen.blit(info_surf, (50, self.height - 70))

        pygame.display.flip()

    def run(self) -> Optional[SimulationConfig]:
        """Run the menu until user starts simulation or quits."""
        running = True
        while running:
            result = self.handle_events()

            if result is False:  # User quit
                pygame.quit()
                sys.exit()
            elif result is not None:  # User started simulation
                pygame.quit()
                return result

            self.draw()
            self.clock.tick(60)

        return None


def show_menu() -> Optional[SimulationConfig]:
    """Show the start menu and return the configuration."""
    menu = StartMenu()
    return menu.run()
