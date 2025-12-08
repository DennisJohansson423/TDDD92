import commandcenter as pycc
import numpy as np
from typing import List
import math
class BoidsPotential:
    def __init__(self, agent, use_boids=True):
        self.agent = agent
        self.use_boids = use_boids
        self.own_combat_units = [] 
        self.enemy_combat_units = [] 
        self.closest_enemy = None

    def get_friendly_units(self):
        """get our own units"""
        for unit in self.agent.get_my_units():
            if unit.unit_type.is_combat_unit:
                if unit not in self.own_combat_units:
                    self.own_combat_units.append(unit)
        
    def get_enemy_units(self):
        """Gets the enemy units spotted by the scout.
            If an unit is dead we remove it  
        """
        for en_unit in self.agent.unit_collection.get_group(1):
            if en_unit not in self.enemy_combat_units and self.is_enemy_in_range(en_unit):
                self.enemy_combat_units.append(en_unit)
        for unit in self.enemy_combat_units:
            if not unit.is_alive:
                self.enemy_combat_units.remove(unit)
                
    def is_under_attack(self, detection_radius=25.0):
        for unit in self.own_combat_units:
            if unit.unit_type.is_combat_unit:  
                for enemy in self.enemy_combat_units:  # Assuming self.enemy_units contains all detected enemy units
                    # Calculate the Euclidean distance between unit and enemy
                    distance = math.sqrt(
                        (unit.position.x - enemy.position.x) ** 2 +
                        (unit.position.y - enemy.position.y) ** 2)
                    if distance <= detection_radius:
                        return True

        return False
    
    def is_enemy_in_range(self,en_unit, detection_radius = 20): 
        for unit in self.own_combat_units:
            if unit.unit_type.is_combat_unit:  
                # Assuming self.enemy_units contains all detected enemy units
                # Calculate the Euclide                  
                distance = math.sqrt(
                    (unit.position.x - en_unit.position.x) ** 2 +
                    (unit.position.y - en_unit.position.y) ** 2)
                if distance <= detection_radius:
                    return True

        return False
    def get_closest_enemy(self, unit):
        closest_enemy = None
        min_distance = float('inf')
        for enemy in self.enemy_combat_units:
            distance = np.linalg.norm(np.array([unit.position.x - enemy.position.x,
                                                unit.position.y - enemy.position.y]))
            if distance < min_distance:
                min_distance = distance
                closest_enemy = enemy
        self.closest_enemy = closest_enemy        
        return closest_enemy
    def get_unit_range(self, unit:pycc):
        """gets the range of each of our own unit"""
        unit_type = unit.unit_type
        attack_range = unit_type.attack_range
        return attack_range
    
    def calculate_attractive(self, own_unit:pycc.Unit,target_unit:pycc.Unit):
        """given a unit, calculate the attractive potential towards a target"""
        range = self.get_unit_range(own_unit)
        direction = np.array([own_unit.position.x - target_unit.position.x, own_unit.position.y - target_unit.position.y ])
        distance = np.linalg.norm(direction)
        if distance == 0:
            return np.zeros(2)
        desired_distance = max(0,distance -range)
        force_magnitude = min(1,desired_distance/10)
        return (direction/distance)*force_magnitude
    
    def calculate_repulsive(self, own_unit: pycc.Unit, enemy_unit, buffer: float = 10.0 ):
        total_force = np.zeros(2)

        enemy = self.closest_enemy
            
        enemy_range = self.get_unit_range(enemy)
        direction = np.array([own_unit.position.x - enemy.position.x, own_unit.position.y - enemy.position.y])
        distance = np.linalg.norm(direction)
        buffer_distance = enemy_range + buffer
        if 0 < distance < buffer_distance:
            force = (buffer_distance - distance)/buffer_distance
            total_force += (direction/distance) *force
        return total_force
    
    def calculate_separation(self, own_unit: pycc.Unit, allies: List[pycc.Unit], separation_distance: float = 5.0):
        """Calculates the separation force to avoid crowding within the troops."""
        total_force = np.zeros(2)
        for ally in allies:
            if  ally != own_unit:  # Skip itself
                continue
            direction = np.array([own_unit.position.x - ally.position.x,
                                  own_unit.position.y - ally.position.y])
            distance = np.linalg.norm(direction)
            if distance < separation_distance and distance > 0:
                force = (separation_distance - distance) / separation_distance
                total_force += (direction / distance) * force
        return total_force

    def calculate_alignment(self, own_unit: pycc.Unit, allies: List[pycc.Unit]):
        """Calculates the alignment force to match velocity with allied units."""
        velocities = []
        for ally in allies:
            if  ally != own_unit:
                velocities.append(np.array([ally.position.x, ally.position.y]))
        if velocities:
            average_velocity = np.mean(velocities, axis=0)
            return average_velocity - np.array([own_unit.position.x, own_unit.position.y])
        return np.zeros(2)

    def calculate_cohesion(self, own_unit: pycc.Unit, allies: List[pycc.Unit]):
        """Calculates the cohesion force to move towards the center of the troop group."""
        positions = []
        for ally in allies:
            if  ally != own_unit:
                positions.append(np.array([ally.position.x, ally.position.y]))
        if positions:
            center_of_mass = np.mean(positions, axis=0)
            direction = center_of_mass - np.array([own_unit.position.x, own_unit.position.y])
            distance = np.linalg.norm(direction)
            if distance > 0:
                return direction / distance
        return np.zeros(2)

    def combined_force(self, unit):
        attractive_forces = np.sum([self.calculate_attractive(unit, target) for target in self.enemy_combat_units if target.is_alive], axis=0)
        
        repulsive_force = self.calculate_repulsive(unit, self.closest_enemy)
        total_dist = np.array([unit.position.x - self.closest_enemy.position.x,
                                  unit.position.y - self.closest_enemy.position.y])

        if self.use_boids:
            separation_force = self.calculate_separation(unit, self.own_combat_units)
            alignment_force = self.calculate_alignment(unit, self.own_combat_units)
            cohesion_force = self.calculate_cohesion(unit, self.own_combat_units)

            boids_force = (
                1.5 * separation_force +
                0.5 * alignment_force +
                1.3 * cohesion_force
            )
        else:
            boids_force = np.zeros(2)
        total_force = attractive_forces + repulsive_force + boids_force
        norm = np.linalg.norm(total_force)
        return total_force / norm if norm != 0 else total_force