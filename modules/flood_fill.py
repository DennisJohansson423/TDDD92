import json
import os
import math
import numpy as np

from dataclasses import dataclass
from collections import deque
from commandcenter import PLAYER_SELF, PLAYER_ENEMY

from typing import Optional

GATE_MAX_THRESHOLD = 15
GATE_MIN_THRESHOLD = 4
TILE_RECHECK_THRESHOLD = 5

ENEMY_CLUSTER_WEIGHT = 0.4
ENEMY_BASE_WEIGHT = 0.6

@dataclass
class Tile:
    """
    Struct used for holding information about each tile.
    """
    x: int
    y: int
    depth: Optional[int] = None
    walkable: Optional[bool] = None
    flooded: Optional[bool] = None
    gate: Optional[bool] = False
    gate_group: Optional[int] = None
    flood_group: Optional[int] = None
    loop_counter: Optional[int] = 0

    def __hash__(self):
        return hash((self.x, self.y))
    
    def __eq__(self, other):
        if not isinstance(other, Tile):
            return False
        return self.x == other.x and self.y == other.y

class FloodFill:
    """
    Class used to find choke points in maps from 
    starcraft by using the flood fill algorithm.
    """
    def __init__(self, agent = None, current_strategy: str = "Moderate Action"):
        self.agent = agent

        self.current_strategy = current_strategy
        
        self.binary_map = [[]]
        self.depth_map = {}

        self.depth_max = 0
        self.flood_level = 0
        self.flooded_tiles = deque()
        self.number_of_flood_groups = 0

        self.gate_tiles = []
        self.gate_tile_groups = {}
        self.number_of_gate_groups = 0
        
        self.enemy_positions = []
        self.friendly_positions = []
        self.enemy_base_pos = None
        self.complete = False
        
        self.primary_choke_point = None
        self.primary_gate_group = None
        
    def get_binary_map(self) -> list[list]:
        return self.binary_map
    
    def get_depth_map(self) -> list[Tile]:
        return self.depth_map
    
    def get_flood_level(self) -> int:
        return self.flood_level
    
    def get_depth_max(self) -> int:
        return self.depth_max
    
    def get_primary_choke_point(self) -> tuple:
        """
        Returns the primary choke point based on the current strategy.
        """
        if self.categorized_choke_points:
            self.primary_choke_point = self.categorized_choke_points.get(self.current_strategy)[0][0]
            self.primary_gate_group = self.categorized_choke_points.get(self.current_strategy)[0][1]
            return self.primary_choke_point
    
    def update_current_strategy(self, current_strategy: str) -> None:
        """
        Updates the current_strategy variable.
        """
        self.current_strategy = current_strategy
    
    def get_tile_neigbours(self, tile: Tile) -> list:
        """
        Returns a list of neighbour coordinates to a specific tile.
        """
        neighbours = [
                (tile.x + 1, tile.y), # East
                (tile.x, tile.y + 1), # North
                (tile.x + 1, tile.y + 1), # NorthEast
                (tile.x - 1, tile.y + 1), # NorthWest
                (tile.x - 1, tile.y), # West
                (tile.x, tile.y - 1), # South
                (tile.x + 1, tile.y - 1), # SouthEast
                (tile.x - 1, tile.y - 1) # SouthWest
            ]
        return neighbours
    
    def prepare_flood_fill(self, single_step: bool = False):
        """
        Main function which is called from the agent to 
        prepare the process of finding choke points.
        Called ones at the start of the game.
        
        This process has four different stages:
        1. Flood the map - loop over tiles and mark them as flooded
        2. Identify - Group certain flooded tiles together and mark tiles as 
        gates if found.
        3. Group gate tiles - Find gate tiles that are adjecent and make them 
        into a group
        4. Filter gate groups - Certain groups are discarded if their length is 
        above a predetermined threshold.
        """ 
        if single_step:
            if self.flood_level == 0:
                self.identify_gate_tile_groups()
                self.filter_gate_groups()
                self.flood_level -= 1
            elif self.flood_level == -1:
                self.complete = True
            else:
                self.flood_map(self.flood_level)
                self.identify_flood_groups_and_gate_tiles()
                self.flood_level -= 1
        else:
            self.reset_depth_map()
            while self.flood_level > 0:
                self.flood_map(self.flood_level)
                self.identify_flood_groups_and_gate_tiles()
                self.flood_level -= 1

            self.identify_gate_tile_groups()                
            self.filter_gate_groups()
            self.complete = True
            
    def get_enemy_start_base_location(self) -> tuple:
        """
        The get_player_starting_base_location() function in base_locaiton_manager 
        returns the wrong starting base location(I think?), it appears to be vertically
        flipped.
        
        Returns the flipped starting base location coordinates.
        """
        enemy_starting_base = self.agent.base_location_manager.get_player_starting_base_location(PLAYER_ENEMY)
                
        enemy_base_pos = (
            round(enemy_starting_base.position.x), round(len(self.binary_map) - 1 - enemy_starting_base.position.y)
            ) if enemy_starting_base else None # Flips the coordinate vertically
        
        return enemy_base_pos
    
    def find_choke_points(self) -> dict:
        """
        Finds and categorizes gate groups. 
        
        Determines aggression score for each group and
        place them in one out of three categories, defensive, medium or aggressive.
        Returns the categorized and sorted dictionary of choke point coordinates.
        """
        if not self.enemy_base_pos and self.agent:
            self.enemy_base_pos = self.get_enemy_start_base_location()
            
        choke_points = self.convert_gate_groups_to_coordinates()

        self.categorized_choke_points = self.categorize_choke_points(choke_points)
        
        return self.categorized_choke_points
    
    def reset_depth_map(self) -> None:
        """
        Resets class variables, enables multiple runs of visualization.
        """
        self.depth_max = 0
        self.flood_level = 0
        self.number_of_flood_groups = 0
        self.flood_groups = {}
        self.gate_tiles = []
        self.gate_tile_groups = {}
        self.number_of_gate_groups = 0
        self.enemy_positions = []
        self.complete = False
        self.create_depth_map()
        
    def create_binary_map(self) -> None:
        """
        Generates binary map from map width, map height and the function 
        is_walkable. Each tile is either 1 or 0(True or False). 
        
        Will get map data from agent if run parallel with 
        starcraft or binary.json if ran as standalone.
        """
        if not self.agent:
            self.read_map_from_json()
        else:
            self.binary_map = [[self.agent.map_tools.is_walkable(x, y) for x in range(self.agent.map_tools.width)]
                                for y in range(self.agent.map_tools.height)]
            
            self.binary_map = self.binary_map[::-1] # Invert the map vertically
            
            self.write_map_to_json()

    def create_depth_map(self) -> None:
        """
        Generates depth map based on the generated binary map. Uses a tile 
        data class which contains information about the tiles properties.
        """
        for y, row in enumerate(self.binary_map):
            for x, walkable in enumerate(row):
                tile = Tile(x, y, 0, walkable)
                tile.depth = self.determine_tile_depth(tile)
                self.depth_map[(tile.x, tile.y)] = tile
                if self.depth_max < tile.depth:
                    self.depth_max = tile.depth

        self.flood_level = self.depth_max
            
    def determine_tile_depth(self, tile: Tile) -> int:
        """
        Calculate depth for the given tile using BFS. The depth is 
        based on the distance to the closest unwalkable tile.
        """
        tile_queue = [tile]
        visited = set()
        visited.add((tile.x, tile.y))
        
        while tile_queue:
            current_tile = tile_queue.pop(0)

            if not current_tile.walkable:
                break
            
            neighbours = self.get_tile_neigbours(current_tile)

            for x, y in neighbours:
                if (x, y) not in visited and self.is_within_bounds(x, y):
                    neighbor_tile = Tile(x, y, current_tile.depth + 1, self.binary_map[y][x])
                    visited.add((x, y))
                    tile_queue.append(neighbor_tile)

        return current_tile.depth
    
    def flood_map(self, flood_depth: int) -> None:
        """
        Floods map up to a given flood depth by marking tiles as flooded.
        """
        for tile in self.depth_map.values():
            if tile.depth >= flood_depth and not tile.flooded and not tile.gate:
                tile.flooded = True
                self.flooded_tiles.append(tile)

        self.flood_level = flood_depth

    def identify_flood_groups_and_gate_tiles(self) -> None:
        """
        Finds seperate floodgroups and gate tiles wihtin the map by setting 
        each tiles "flood_group" property. 
        
        Calls function "change_flood_group" if two flood groups meet, 
        this combines the floodgroups into one.
        
        Sets tile to gate if two adjacent neighbours are found with different 
        floodgroups.
        """
        while self.flooded_tiles:
            tile = self.flooded_tiles.popleft()
            if tile.gate:
                continue

            neighbours = self.get_tile_neigbours(tile)

            found_flood_groups = set()
            for x, y in neighbours:
                if self.is_within_bounds(x, y):
                    neighbour_tile = self.depth_map.get((x, y))
                    if neighbour_tile.flood_group and not neighbour_tile.gate: 
                        found_flood_groups.add(neighbour_tile.flood_group)

            if len(found_flood_groups) == 0: # 0 neighbours
                if tile.loop_counter < TILE_RECHECK_THRESHOLD:
                    self.flooded_tiles.append(tile)
                    tile.loop_counter += 1
                else: # Reached loop limit
                    tile.flood_group = self.number_of_flood_groups
                    self.number_of_flood_groups += 1
            if len(found_flood_groups) == 1: # One neighbour with a flood group
                tile.flood_group = found_flood_groups.pop()
            elif len(found_flood_groups) > 1: # More than one neighbour with a flood group
                tile.gate = True
                tile.flooded = False
                self.gate_tiles.append(tile)

        self.flooded_tiles = deque()

    def identify_gate_tile_groups(self) -> None:
        """
        Finds individual gate tiles and formes groups 
        based on which tiles are adjacent.(Very bloated, not optimal)
        """
        for gate_tile in self.gate_tiles:
            if gate_tile.gate_group:
                continue
            neighbour_gate_tiles = deque()
            neighbour_gate_tiles.append(gate_tile)
            specified_group_number = None

            while neighbour_gate_tiles:
                current_gate_tile = neighbour_gate_tiles.pop()
                if not current_gate_tile.walkable:
                    continue

                if specified_group_number:
                    current_gate_tile.gate_group = specified_group_number
                    specified_group = self.gate_tile_groups.get(specified_group_number)
                    if current_gate_tile not in specified_group:
                        specified_group.append(current_gate_tile)
                else:
                    current_gate_tile.gate_group = self.number_of_gate_groups
                    non_specified_group = self.gate_tile_groups.get(self.number_of_gate_groups)
                    if non_specified_group and current_gate_tile not in non_specified_group:
                        non_specified_group.append(current_gate_tile)
                    else:
                        self.gate_tile_groups[self.number_of_gate_groups] = [current_gate_tile]
                    specified_group_number = self.number_of_gate_groups
                    self.number_of_gate_groups += 1

                for x, y in self.get_tile_neigbours(current_gate_tile):
                    if self.is_within_bounds(x, y):
                        neighbour_tile = self.depth_map.get((x, y))
                        if neighbour_tile.gate and not neighbour_tile.gate_group:
                            neighbour_gate_tiles.append(neighbour_tile)
    
    def filter_gate_groups(self) -> None:
        """
        Filters out gate groups that are longer than a preset threshold.
        """
        groups_to_delete = []
        for group_number in self.gate_tile_groups.keys():
            group_len = len(self.gate_tile_groups.get(group_number))
            if group_len >= GATE_MAX_THRESHOLD or group_len <= GATE_MIN_THRESHOLD:
                groups_to_delete.append(group_number)
        
        for group_number in groups_to_delete:
            self.delete_gate_group(group_number)

    def delete_gate_group(self, gate_group_number: int) -> None:
        """
        Sets the gate property to False on each tile part of the input gate_group_number.
        """
        for gate_tile in self.gate_tile_groups.get(gate_group_number):
            gate_tile.gate = False
            gate_tile.gate_group = None
        del self.gate_tile_groups[gate_group_number]
            

    def is_within_bounds(self, x: int, y: int) -> bool:
        """
        Checks whether x and y are within the bounds of the map.
        """
        return 0 <= x < len(self.binary_map[0]) and 0 <= y < len(self.binary_map)
    
    def convert_gate_groups_to_coordinates(self):
        """
        Returns a list coordinates of gate groups middle points.
        This point is based on maximum depth within a gate group.
        """
        choke_points = {}
        for gate_group in self.gate_tile_groups:
            found_depth = -1
            middle_coord = None
            gate_group_tiles = self.gate_tile_groups[gate_group]
            for tile in gate_group_tiles:
                tile_depth = tile.depth
                if tile_depth > found_depth:
                    found_depth = tile_depth
                    middle_coord = (tile.x, tile.y)
            choke_points[(middle_coord, gate_group)] = 0 # 0 is a placeholder for aggressive score
        
        return choke_points

    def categorize_choke_points(self, choke_points) -> dict:
        """
        Categorizes choke points into three different categories, defensive, medium and aggressive.
        Based on an aggressive score derived from average distance to enemy units and the distance
        to the enemy base.
        """
        if self.agent:
            self.enemy_positions = self.get_enemy_poisitions()
            self.friendly_positions = self.get_friendly_poisitions() # Just for debug
        else:
            self.enemy_base_pos = (128, 146)
        
        if self.enemy_base_pos and choke_points:
            scored_choke_points = {
                choke_point: self.calculate_aggression_score(choke_point[0], self.enemy_positions)
                for choke_point in choke_points
            }
            
            sorted_choke_points = dict(sorted(scored_choke_points.items(), key=lambda x: x[1]))
            scores = list(sorted_choke_points.values())
            low_threshold = np.percentile(scores, 33)
            high_threshold = np.percentile(scores, 66)

            categories = {"No Action": [], "Moderate Action": [], "Aggressive Action": []}
            for choke_point, score in sorted_choke_points.items():
                if score <= low_threshold:
                    categories["No Action"].append((choke_point[0], choke_point[1], score))
                elif score <= high_threshold:
                    categories["Moderate Action"].append((choke_point[0], choke_point[1], score))
                else:
                    categories["Aggressive Action"].append((choke_point[0], choke_point[1], score))

            return categories
        else:
            return None
        
    def get_friendly_poisitions(self) -> list:
        """
        Returns a list of friendly positions.
        """
        friendly_positions = []
        for unit in self.agent.get_my_units():
            friendly_positions.append((round(unit.position.x), round(unit.position.x)))
        return friendly_positions

    def get_enemy_poisitions(self) -> list:
        """
        Returns a list of spotted enemy positions.
        """
        enemy_positions = []
        for unit in self.agent.unit_collection.get_group(1):
            if unit.unit_type.is_combat_unit:
                enemy_positions.append((round(unit.position.x), round(unit.position.x)))
        return enemy_positions
    
    def add_enemy_debug(self, position: tuple) -> None:
        """
        Function used for debugging, adds enemy positions to the self.enemey_positions list
        which will effect the aggressive score of each gate coordinate.
        """
        self.enemy_positions.append(position)
    
    def calculate_aggression_score(self, coord, enemy_positions: list) -> float:
        enemy_positions_score = 0
        enemy_base_score = 0
        if enemy_positions:
            avg_distance_to_enemies = sum(math.dist(coord, enemy) for enemy in enemy_positions) / len(enemy_positions)
            enemy_positions_score = ENEMY_CLUSTER_WEIGHT*(1/avg_distance_to_enemies)
        if self.enemy_base_pos:
            distance_to_enemy_base = math.dist(coord, self.enemy_base_pos)
            enemy_base_score = ENEMY_BASE_WEIGHT*(1/distance_to_enemy_base)
            
        aggression_score = enemy_positions_score + enemy_base_score
        return aggression_score

    def read_map_from_json(self, file_name: str = "binary_map.json", directory: str = "maps") -> None:
        """
        Reads binary map representing walkable and non-walkable tiles from a json file.
        Enables testing isolated from the game enviroment.
        """
        filepath = os.path.join(directory, file_name)
        try:
            with open(filepath, "r") as file:
                self.binary_map = json.load(file)
        
        except FileNotFoundError:
            print(f"Error: The file {file_name} was not found in the directory {directory}.")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            
    def write_map_to_json(self, file_name: str = "binary_map.json", directory: str = "maps") -> None:
        """
        Writes binary map representing walkable and non-walkable tiles to a json file.
        Enables testing isolated from the game enviroment.
        """
        os.makedirs(directory, exist_ok=True)
        filepath = os.path.join(directory, file_name)
        with open(filepath, "w") as file:
            json.dump(self.binary_map, file)
            