import pygame
import sys

class VisualizeFloodFill:
    """
    Class used to visualize the flood_fill algorithm with all of its steps.
    Can be run in parallel with starcraft or as a standalone.
    
    To run in parallel: set FLOOD_FILL_DEBUG to True in the config file and run main.py.
    
    To run as standalone: run the laptop_main.py file which only needs the binary_map.jason file 
    found in the maps directory to work.
    """
    def __init__(self, flood_fill, cell_size=5, alongside_game=False):
        pygame.init()
        pygame.display.set_caption("Flood fill Visualization")
        
        self.flood_fill = flood_fill
        self.cell_size = cell_size
        self.alongside_game = alongside_game
        
        if not self.alongside_game:
            self.standalone_init()
        
        self.map_height = len(self.flood_fill.binary_map)
        self.map_width = len(self.flood_fill.binary_map[0])
        
        self.width = self.map_width*cell_size
        self.height = self.map_height*cell_size + 60
        self.screen = pygame.display.set_mode((self.width, self.height))
        
        self.categorized_flood_fill = None
        self.flood_group_colors = {}
        
    def standalone_init(self):
        """
        Initialization of maps needed if the class is ran as standalone.
        """      
        self.flood_fill.create_binary_map()
        self.flood_fill.create_depth_map()

    def display_map(self) -> None:
        """
        Main function called to start displaying the map.
        """                
        if self.alongside_game:
            self.run_parallel()
        else:
            self.run_standalone()
        
    def update_pygame_loop(self):
        """
        This update loop is needed when running the visualization in parallel with
        starcraft to make pygame run as intended.
        """            
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
        pygame.display.flip()
        
    def run_parallel(self):
        """
        Updates the map with new information when ran in parallel.
        Called from the starcraft on_step function located in basic_agent.py
        """   
        self.screen.fill((30, 30, 30))
        self.draw_depth_map()
        pygame.display.flip()
        
    def run_standalone(self):
        font = pygame.font.Font(None, 36)
        button_color = (100, 200, 100)
        hover_color = (150, 250, 150)
        button_text = font.render("Calculate depth", True, (0, 0, 0))
        button_rect = pygame.Rect(self.width*0.5 - 110, self.height - 80, 220, 50)
        
        running = True
        flooded_complete = False
        depth_map_created = False
        categorize = False
        reset = False
        
        while running:
            self.screen.fill((30, 30, 30))
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if button_rect.collidepoint(pygame.mouse.get_pos()):
                        if not depth_map_created:
                            depth_map_created = True
                            button_rect = pygame.Rect(self.width*0.5 - 80, self.height - 80, 160, 50)
                            button_text = font.render("Flood", True, (0, 0, 0))  
                        elif self.flood_fill.flood_level > 0:
                            self.flood_fill.prepare_flood_fill(single_step=True)
                            if self.flood_fill.flood_level == 0:
                                button_rect = pygame.Rect(self.width*0.5 - 150, self.height - 80, 300, 50)
                                button_text = font.render("Filter and categorize", True, (0, 0, 0))
                                categorize = True
                        elif categorize:
                            flooded_complete = True
                            categorize = False
                            self.flood_fill.prepare_flood_fill(single_step=True)
                            self.flood_fill.find_choke_points()
                            self.flood_fill.get_primary_choke_point()
                            button_rect = pygame.Rect(self.width*0.5 - 80, self.height - 80, 160, 50)
                            button_text = font.render("Simplify", True, (0, 0, 0))
                        elif flooded_complete:
                            flooded_complete = False
                            reset = True
                            self.flood_fill.prepare_flood_fill(single_step=True)
                            button_rect = pygame.Rect(self.width*0.5 - 80, self.height - 80, 160, 50)
                            button_text = font.render("Reset", True, (0, 0, 0))
                        elif reset:
                            reset = False
                            depth_map_created = False
                            button_rect = pygame.Rect(self.width*0.5 - 110, self.height - 80, 220, 50)
                            button_text = font.render("Calculate depth", True, (0, 0, 0))
                            self.flood_fill.reset_depth_map() 
                    else:
                        if not reset:
                            continue
                        
                        mouse_x, mouse_y = pygame.mouse.get_pos()
                        map_x = mouse_x//self.cell_size
                        map_y = mouse_y//self.cell_size
                        self.flood_fill.add_enemy_debug((map_x, map_y))
                        self.flood_fill.find_choke_points()
                        self.flood_fill.get_primary_choke_point()
                        
                            
            color = hover_color if button_rect.collidepoint(pygame.mouse.get_pos()) else button_color
            pygame.draw.rect(self.screen, color, button_rect)
            self.screen.blit(button_text, button_text.get_rect(center=button_rect.center))

            mouse_x, mouse_y = pygame.mouse.get_pos()
            hovered_group = self.get_hovered_details(mouse_x, mouse_y, depth_map_created)
            
            if not depth_map_created:
                self.draw_binary_map()
            else:
                self.draw_depth_map(hovered_group=hovered_group)
            
            if self.popup_text != "":
                self.draw_popup(self.screen, self.popup_text, (mouse_x, mouse_y))
            
            pygame.display.flip()

        pygame.quit()
        sys.exit()
        
    def get_hovered_details(self, mouse_x, mouse_y, depth_map_created):
        """
        Retrieves information about tile under mouse position.
        This data is stored in the self.popup_text variable.
        """
        map_x = mouse_x//self.cell_size
        map_y = mouse_y//self.cell_size
        hovered_group = None
        gate_description = None
        self.popup_text = ""
        
        if (map_x, map_y) in [(tile.x, tile.y) for tile in self.flood_fill.depth_map.values()]:
            tile = next(t for t in self.flood_fill.depth_map.values() if t.x == map_x and t.y == map_y)
            
            if tile.flood_group:
                hovered_group = tile.flood_group
                
            self.popup_text = [
                f"Coords: ({map_x}, {map_y})",
            ]
            
            if depth_map_created:
                self.popup_text.append(f"Depth: {tile.depth}")
                
            if tile.flood_group:
                self.popup_text.append(f"Flood group: {tile.flood_group}")
            
            if tile.gate_group:
                for gate_tile in self.flood_fill.gate_tile_groups[tile.gate_group]:
                    if self.flood_fill.categorized_choke_points:
                        coordinate = (gate_tile.x, gate_tile.y)
                        for category, points in self.flood_fill.categorized_choke_points.items():
                            if any(point[0] == coordinate for point in points):
                                gate_description = category
                                break
                            
                self.popup_text.extend([
                    f"Gate group: {tile.gate_group}",
                    f"Gate group length: {tile.gate_group if not tile.gate_group else len(self.flood_fill.gate_tile_groups[tile.gate_group])}",
                    f"Gate description: {gate_description}"
                ])

            self.popup_text = "\n".join(self.popup_text) 
        
        return hovered_group
        
    def display_binary_map_details(self, screen, font, width):
        """
        Display details in text on screen about the binary map.
        """
        binary_title_text = font.render('Binary Map', True, (255, 255, 255))
        binary_title_rect = binary_title_text.get_rect(center=(0.25*width, 30))
        screen.blit(binary_title_text, binary_title_rect)

    def draw_binary_map(self) -> None:
        """
        Visualize the binary map.
        """
        walkable_color = (255, 255, 255)
        non_walkable_color = (0, 0, 0)

        for y, row in enumerate(self.flood_fill.binary_map):
            for x, walkable in enumerate(row):
                color = walkable_color if walkable else non_walkable_color
                if walkable:
                    pygame.draw.rect(self.screen, color, (x*self.cell_size, y*self.cell_size, self.cell_size, self.cell_size))

    def draw_depth_map(self, hovered_group=None) -> None:
        """
        Visualize the depth map based on the tiles characteristics.
        """
        RED = (255, 0, 0)
        BROWN = (150, 75, 0)
        ORANGE = (255, 165, 0)
        GREEN = (0, 128, 0)
        
        enemy_positions = self.flood_fill.enemy_positions
        friendly_positions = self.flood_fill.friendly_positions
        enemy_base_pos = self.flood_fill.enemy_base_pos
        
        for tile in self.flood_fill.depth_map.values():
            color = None
            if tile.walkable:
                if (tile.x, tile.y) == enemy_base_pos:
                    color = BROWN
                elif tile.gate and self.flood_fill.primary_choke_point and tile.gate_group == self.flood_fill.primary_gate_group:
                    color = ORANGE
                elif tile.gate or (tile.x, tile.y) in enemy_positions:
                    color = RED    
                elif (tile.x, tile.y) in friendly_positions:
                    color = GREEN
                elif tile.flooded and not self.flood_fill.complete:
                    if hovered_group == tile.flood_group:
                        color = self.flood_group_to_color(tile.flood_group, True)
                    else:
                        color = self.flood_group_to_color(tile.flood_group, False)
                else:
                    color = self.depth_to_color(tile.depth)

                rect = pygame.Rect((tile.x*self.cell_size, tile.y*self.cell_size, self.cell_size, self.cell_size))  
                pygame.draw.rect(self.screen, color, rect)
                outline_color = tuple(max(0, c - 50) for c in color)
                pygame.draw.rect(self.screen, outline_color, rect, width=1)
                
    def draw_popup(self, surface, text, position):
        """
        Draws a popup with tile details at the given position.
        """
        font = pygame.font.Font(None, 22)
        
        lines = text.split("\n")
        padding = 5

        line_height = font.get_linesize()
        popup_width = max(font.size(line)[0] for line in lines) + 2 * padding
        popup_height = len(lines) * line_height + 2 * padding

        rect = pygame.Rect(position[0], position[1] - popup_height, popup_width, popup_height)

        if rect.right > surface.get_width():
            rect.x -= rect.right - surface.get_width()
        if rect.bottom > surface.get_height():
            rect.y -= rect.bottom - surface.get_height()
        if rect.left < 0:
            rect.x = 0
        if rect.top < 0:
            rect.y = 0

        pygame.draw.rect(surface, (200, 200, 200), rect)
        pygame.draw.rect(surface, (0, 0, 0), rect, 2)

        for i, line in enumerate(lines):
            text_surface = font.render(line, True, (0, 0, 0))
            surface.blit(text_surface, (rect.x + padding, rect.y + padding + i * line_height))
        
    def depth_to_color(self, depth: int) -> tuple:
        """
        Convert the depth value into a grayscale RGB color.
        The deeper the tile, the darker the gray.
        """
        max_depth = 10
        normalized_depth = min(depth, max_depth) / max_depth
        gray_value = int(255 * (1 - normalized_depth))
        return (gray_value, gray_value, gray_value)
        
    def flood_group_to_color(self, flood_group: int, hovered: bool) -> tuple:
        """
        Convert the flood_group value into an RGB color.
        Used to visually separate each flood group from eachother.
        Makes the color brighter if "hovered" is True.
        """
        if flood_group:
            if flood_group not in self.flood_group_colors:
                max_group = 20
                normalized_group = min(flood_group, max_group) / max_group
                
                r = int(255 * (1 - normalized_group))
                g = int(255 * normalized_group)
                b = int(255 * ((normalized_group + 0.5) % 1))
                self.flood_group_colors[flood_group] = (r, g, b)
                
            base_color = self.flood_group_colors[flood_group]
            if hovered:
                brightness_offset = 80
                return tuple(min(255, component + brightness_offset) for component in base_color)
            else:
                return base_color
        else:
            return (10, 10, 255)