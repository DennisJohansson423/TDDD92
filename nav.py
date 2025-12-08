
from queue import PriorityQueue
from typing import Callable
import numpy as np
import math
from commandcenter import Point2D,Color, UNIT_TYPEID,PLAYER_ENEMY,PLAYER_NEUTRAL

Point2D.distance = lambda self, other: math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)

Point2D.to_np_postion = lambda self : np.array([self.x,self.y])

Point2D.to_tuple = lambda self : (int(self.x),int(self.y))


def manhatta_distance(current_position: tuple[int, int], goal_position:tuple[int, int]) -> int:
    return abs(current_position[0] - goal_position[0]) + abs(current_position[1] - goal_position[1])


def get_neighbors(x:int, y:int, is_walkable:Callable[[int,int], bool],is_rock_pos, not_vaild_pos,units) -> list[tuple[int, int]]:
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1),(1,1),(-1,-1),(-1,1),(1,-1)]  # (dx, dy)
    neighbors = []
    for dx, dy in directions:
        neighbor_x, neighbor_y = x + dx, y + dy
        if is_walkable(int(neighbor_x), int(neighbor_y)) and (neighbor_x, neighbor_y ) not in is_rock_pos and (neighbor_x, neighbor_y ) not in not_vaild_pos:  # Check if the neighbor is walkable
            neighbors.append((neighbor_x, neighbor_y))
    return neighbors
    

def manhattan_distance(pos1, pos2):
    return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])


def a_star(start_position: tuple[int, int], goal_position: tuple[int, int], is_walkable,rock_pos,not_vaild, all_units) -> list[tuple[int, int]]:
    

    if manhattan_distance(start_position,goal_position) < 10:
        return []

    pq = PriorityQueue()
    visited = set()
    came_from = {}
    g_cost = {start_position: 0}
    pq.put((manhattan_distance(start_position, goal_position), start_position))
    
    while not pq.empty():
        _, position = pq.get() 
        if position == goal_position:
            path = []
            while position in came_from:
                path.append(position)
                position = came_from[position]
            path.append(start_position)
            return path[::-1]  # Reverse the path
        
        if position in visited:
            continue
        
        visited.add(position)
        neighbors = get_neighbors(position[0], position[1],is_walkable,rock_pos,not_vaild, all_units)
        
        for neighbor in neighbors:
            if neighbor in visited:
                continue
            
            tentative_g = g_cost[position] + 1  
            f = tentative_g + manhattan_distance(neighbor, goal_position)
            
            if neighbor not in g_cost or tentative_g < g_cost[neighbor]:
                g_cost[neighbor] = tentative_g
                pq.put((f, neighbor))
                came_from[neighbor] = position

    return [] 


def distance(start, end) -> int:
    return np.linalg.norm(start - end)


def attractive_force(agent_pos,goal_pos,k_att) -> float:
    direction = goal_pos - agent_pos
    return k_att * direction


def repulsive_force(agent_pos, obstacle, krep, do):
    dist = distance(agent_pos, obstacle)
    if dist >= do:
        return np.array([0.0,0.0]) 
    direction = agent_pos - obstacle
    scale = krep * (1.0/ dist - 1.0/ do) * (1.0 / dist**2)
    return scale * direction


def total_force(agent_pos,goal, obstacles, krep, do):
    total_repulsive_force = np.array([0.0,0.0])
    for obstacle in  obstacles:
        total_repulsive_force += repulsive_force(agent_pos ,obstacle,krep,do)
    return attractive_force(agent_pos,goal,0.00001) + total_repulsive_force


def direction_radius(force):
    return np.arctan2(force[1],force[0])


def move_direction(angle):
    return np.array([np.cos(angle),np.sin(angle)])




class Navigation:

    def __init__(self, agent):
        self.agent = agent
        self.is_first = True
        self.rocks = set()
        self.is_potienfieid = False
        self.latest_postion = []
        self.latest_click = None
        self.units_in_action = {}
        self.test_dicts = {}
        self.tick = 0


    def is_attack(self):
        print("We are stepping")
        

        
    def is_allready(self,id,goal):
        if id in self.units_in_action:
            return self.units_in_action[id][1] == goal
        
    def move(self, goal,id):
       if self.is_allready(id,goal):
           return
       if self.get_unit_by_id(id) == None:
            self.remove_units(id)
            return
       units = self.agent.get_all_units()
       not_vaild = self.check_if_not_blocked_postion(units)
       self.not_vaild = not_vaild
       path = a_star(self.get_unit_by_id(id).position.to_tuple(),goal.to_tuple(),self.agent.map_tools.is_walkable,self.get_rockspostion(),not_vaild,self.agent.get_all_units() )

       if self.get_unit_by_id(id) is None:
           return
       if self.is_allready(id,goal):
           return
       if distance(goal.to_np_postion(),self.get_unit_by_id(id).position.to_np_postion()) < 2:
           self.units_in_action[id] = ([],goal)
           self.test_dicts[id] = set()
           return
       self.get_unit_by_id(id).position.to_tuple()
       units = self.agent.get_all_units()
       not_vaild = self.check_if_not_blocked_postion(units)
       if goal.to_tuple() in not_vaild:
        self.not_vaild = not_vaild.remove(goal.to_tuple())
       
       path =  a_star(self.get_unit_by_id(id).position.to_tuple(),goal.to_tuple(),self.agent.map_tools.is_walkable,self.get_rockspostion(),not_vaild,self.agent.get_all_units() )
       if len(path) > 0 and len(path) % 2 != 0:  # Check if the length of the path is odd
         path.append(path[-1]) 
       self.units_in_action[id] = (path,goal)
       self.test_dicts[id] = set()
    


    def get_path(self, start, goal, id) -> None:
       self.start = start 
       self.goal = goal
       self.id = id
       units = self.agent.get_all_units()
       not_vaild = self.check_if_not_blocked_postion(units)
       self.not_vaild = not_vaild
       path = a_star(start,goal,self.agent.map_tools.is_walkable,self.get_rockspostion(),not_vaild,self.agent.get_all_units() )
       if len(path) > 0 and len(path) % 2 != 0:  # Check if the length of the path is odd
         path.append(path[-1]) 
       self.units_in_action[id] = (path,goal)

   
    def print_path(self):
        for key in self.units_in_action:
            path = self.units_in_action[key][0]
            for i in range(len(path) - 1): 
                self.agent.map_tools.draw_line(
                    Point2D(path[i][0],path[i][1]),
                    Point2D(path[i+1][0],path[i+1][1]),
                    Color.GREEN)


    def is_local_minum(self):
        if len(self.latest_postion) < 15:
            return False
        unique_values = set(self.latest_postion[-15:])  # Use the last 5 positions
        if len(unique_values) == 1:
            return True
        return False
        

    def on_step(self):
        if self.tick == 10:
            for key in list(self.units_in_action):
                self.navigate(key)
            self.tick = 0
        self.tick += 1

    def remove_units(self, id):
        if id in self.units_in_action:
            del self.units_in_action[id]

    def navigate(self,id) -> None:
        if self.get_unit_by_id(id) == None:
            self.remove_units(id)
            return
        goal = self.units_in_action[id][1]
        path = self.units_in_action[id][0]
        self.agent.map_tools.draw_circle(goal,2,Color.RED)
        current_position = self.get_unit_by_id(id).position
       
        if  len(path) == 0 and not self.is_potienfieid :
            self.agent.map_tools.draw_circle(self.get_unit_by_id(id).position,2,Color.GRAY)
            obstacles = [ unit.position.to_np_postion() for unit in self.agent.get_all_units() if unit.player == PLAYER_ENEMY  and distance(unit.position.to_np_postion() ,goal.to_np_postion()) > 6]
            force = total_force(self.get_unit_by_id(id).position.to_np_postion(),goal.to_np_postion(),obstacles,2,2 )
            angle = direction_radius(force)
            movement_vector = move_direction(angle)
            step_size = 1
            new_agent_pos = self.get_unit_by_id(id).position.to_np_postion() + step_size * movement_vector
            self.latest_click = Point2D(new_agent_pos[0],new_agent_pos[1])
            self.get_unit_by_id(id).move(Point2D(new_agent_pos[0],new_agent_pos[1]))
            self.latest_postion.append(self.get_unit_by_id(id).position.to_tuple())
            if self.is_near((current_position.x,current_position.y),goal.to_tuple()):
                del self.units_in_action[id]
            not_vaild = self.check_if_not_blocked_postion(self.agent.get_all_units())

            if (self.get_unit_by_id(id).position.to_tuple(),goal.to_tuple()) not in self.test_dicts[id]:
                path = a_star(self.get_unit_by_id(id).position.to_tuple(),goal.to_tuple(),self.agent.map_tools.is_walkable,[],not_vaild,self.agent.get_all_units() )
                self.test_dicts[id].add((self.get_unit_by_id(id).position.to_tuple(),goal.to_tuple()))
                if len(path) > 0 and len(path) % 2 != 0:  # Check if the length of the path is odd
                    path.append(path[-1])
                self.units_in_action[id] = (path,goal)
            return
        if self.is_potienfieid:
            self.agent.map_tools.draw_circle(self.get_unit_by_id(id).position,2,Color.GREEN)
            if self.is_local_minum():
                not_vaild = self.check_if_not_blocked_postion(self.agent.get_all_units())
                path = a_star(self.get_unit_by_id(id).position.to_tuple(),goal.to_tuple(),self.agent.map_tools.is_walkable,[],not_vaild,self.agent.get_all_units() )
                if len(path) > 0 and len(path) % 2 != 0:  # Check if the length of the path is odd
                    path.append(path[-1])
                self.units_in_action[id] = (path,goal)
                
                self.is_potienfieid = False
                self.latest_postion = []
                return

            current_position = self.get_unit_by_id(id).position
            if  len(path) != 0 and self.is_near((current_position.x,current_position.y),(path[0][0],path[0][1])):
                    path.pop(0)
                    next_postion = path.pop(0)
                    if len(path) == 0:
                        del self.units_in_action[id]
                        return
                    
            try:
                next_postion = path[0]
            except Exception:
                self.remove_units(id)
                return

            
            obstacles = [ unit.position.to_np_postion() for unit in self.agent.get_all_units() if unit.player == PLAYER_ENEMY ]
            force = total_force(self.get_unit_by_id(id).position.to_np_postion(),np.array([next_postion[0],next_postion[1]]) ,obstacles,2,2 )
            angle = direction_radius(force)
            movement_vector = move_direction(angle)
            step_size = 1
            new_agent_pos = self.get_unit_by_id(id).position.to_np_postion() + step_size * movement_vector
            self.latest_click = Point2D(new_agent_pos[0],new_agent_pos[1])
            self.get_unit_by_id(id).move(Point2D(new_agent_pos[0],new_agent_pos[1]))
            self.latest_postion.append(self.get_unit_by_id(id).position.to_tuple())
            current_position = (next_postion[0],next_postion[1])
            cords = set()
            enmys =  [ unit for unit in self.agent.get_all_units() if unit.player == PLAYER_ENEMY] 
            for unit in enmys:
                self.points_in_circle_fine(unit.position.to_tuple(),11,cords)
            self.is_potienfieid = current_position in cords

        else:
            if self.is_first:
                path.pop(0)
                next_postion = path.pop(0)
                self.latest_click = Point2D(next_postion[0],next_postion[1])
                
                self.get_unit_by_id(id).move(Point2D(next_postion[0],next_postion[1]))
                self.is_first = False
            else:
                current_position = self.get_unit_by_id(id).position
                if self.is_near((current_position.x,current_position.y),(path[0][0],path[0][1])):
                    path.pop(0)
                    next_postion = path.pop(0)
                    self.latest_click = Point2D(next_postion[0],next_postion[1])
                    self.get_unit_by_id(id).move(Point2D(next_postion[0],next_postion[1]))
                else:
                    next_postion = path[0]
                    self.latest_click = Point2D(next_postion[0],next_postion[1])
                    self.get_unit_by_id(id).move(Point2D(next_postion[0],next_postion[1]))

            current_position = (next_postion[0],next_postion[1])
            enmys =  [ unit for unit in self.agent.get_all_units() if unit.player == PLAYER_ENEMY]
            cords = set()
            for unit in enmys:
                self.points_in_circle_fine(unit.position.to_tuple(),11,cords)
            self.is_potienfieid = current_position in cords
            self.latest_postion.append(self.get_unit_by_id(id).position.to_tuple())
            
           
    def get_unit_by_id(self, id):
        my_units = self.agent.get_my_units()
        for unit in my_units:
            if unit.id == id:
                return unit
            
    def is_at_pos(self,id):
        return id in self.units_in_action
        

    def check_if_not_blocked_postion(self, units):
        cords = set()
        for unit in units:
            self.points_in_circle_fine(unit.position.to_tuple(),unit.radius,cords)
        return cords
    

    def points_in_circle_fine(self, center: tuple, radius: float,points , step: float = 1):
        cx, cy = center
        # Define the bounds of the square
        x = cx - radius
        while x <= cx + radius:
            y = cy - radius
            while y <= cy + radius:
                # Add the point to the set
                points.add((int(x), int(y)))
                y += step
            x += step
        return points
     

    def get_rockspostion(self) -> list[tuple]:
        rocks_postion = []
        units = self.agent.get_all_units()
        for unit in units:
            if unit.unit_type.unit_typeid == UNIT_TYPEID.DESTRUCTIBLEROCKEX16X6:
                rocks_postion.append(unit.position.to_tuple())
                self.agent.map_tools.draw_box(Point2D(unit.position.x+2,unit.position.y+2),
                                              Point2D(unit.position.x-2,unit.position.y-2),
                                              Color.RED)
        rock_area = set()
        for rocks in rocks_postion:
            for rock in self.get_rock_cords(rocks):
                rock_area.add(rock)

        return rock_area

    
    def get_rock_cords(self, position):
        x, y = position
        rocks_postions = []
        for dx in range(-2, 2):
            for dy in range(-2, 2):
                rocks_postions.append((x + dx, y + dy))
    
        return rocks_postions
    

    def is_near(self, current_position,goal_positon, threshold=3.0):
        distance = math.sqrt(
            (goal_positon[0] - current_position[0]) ** 2 +
            (goal_positon[1] - current_position[1]) ** 2
        )
       
        return distance <= threshold 





    



