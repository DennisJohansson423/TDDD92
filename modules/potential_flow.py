import commandcenter as pycc
from commandcenter import Unit

import math
import numpy as np
from enum import Enum
import matplotlib.pyplot as plt


class FlowType(Enum):
    REGION_FLOW = "regionflow"
    BORDER_FLOW = "borderflow"
    OBSTACLE_FLOW = "obstacleflow"
    ATTACK_FLOW = "attackflow"


class PotentialFlow:
    EPSILON = 1e-5
    def __init__(self, U: float, region_center: complex, scout: Unit, p1: float = 0.5, p2: float = 0.125, p3: float = -0.2, p4: float = 0.150, p5: float = 0.75, d_r_thres: float = 5, d_b_thres: float = 5) -> None:
        """
        Initializes the potential flow generator with key parameters.
        Parameters:
          - U: Base flow strength.
          - region_center: Complex coordinate of the region's center.
          - scout: The scout unit.
          - p1, p2, p3, p4, p5: Coefficients for different flow components.
          - d_r_thres: Distance threshold for region flow behavior.
          - d_b_thres: Distance threshold for border flow behavior.
        """
        self.U = U
        self.region_center = region_center
        self.scout = scout
        self.p1 = p1
        self.p2 = p2
        self.p3 = p3
        self.p4 = p4
        self.p5 = p5
        self.d_r_thres = d_r_thres
        self.d_b_thres = d_b_thres

    def region_flow(self, z: complex) -> complex:
        """
        Computes the region flow potential, combining vortex and source/sink
        based on the scout's distance from the region center.
        """
        distance = np.abs(z - self.region_center)
        vortex_pot = self.vortex_flow(self.region_center, z)
        source_pot = self.source_sink_flow(self.region_center, z)

        # Different behaviors based on distance threshold
        if distance > self.d_r_thres:
            return self.p1 * vortex_pot - self.p2 * source_pot
        else:
            return self.p1 * vortex_pot + self.p2 * source_pot

    def border_flow(self, z_start: complex, z: complex) -> complex:
        """
        Computes the border flow potential.
        If the point z is close to the border point z_start, applies
        vortex and source potentials.
        """
        z_prime = z - z_start
        if np.abs(z_prime) < self.d_b_thres:
            return self.p3 * self.vortex_flow(z_start, z) + self.p4 * self.source_sink_flow(z_start, z)
        else:
            return 0

    def obstacle_flow(self, z_o: complex, a: float, z: complex) -> complex:
        """
        Computes the potential caused by an obstacle using the mirror
        image method to avoid the obstacle.
        """
        z_s = self.region_center
        z_rel = z - z_o
        z_inverted = z_o + (a**2) / np.conj(z_rel)
        f_image_arg = z_inverted - (z_s - z_o)
        f_image = np.conj(self.region_flow(f_image_arg))
        return f_image

    def attack_flow(self, z_start: complex, z: complex, attack_range: float, safety_margin: float = 2.0) -> complex:
        """
        Computes the potential flow caused by an attacking enemy unit.
        Creates a repulsive force to keep the scout outside the enemy's attack range.

        Args:
            z_start: Position of the enemy unit (complex number).
            z: Position of the scout unit (complex number).
            attack_range: Attack range of the enemy unit.
            safety_margin: Desired distance to keep outside the attack range.
        """
        distance = np.abs(z - z_start)

        # Avoid division by zero or log(0)
        if distance < PotentialFlow.EPSILON:
            distance = PotentialFlow.EPSILON

        # --- Simplified Effective Range ---
        effective_range = attack_range + safety_margin

        # --- Stronger Repulsion for Close Distances ---
        if distance < effective_range+10:
            repulsion = self.p5 * self.source_sink_flow(z_start, z)
            return repulsion
        else:
            return 0
    def vortex_flow(self, z_start: complex, z: complex) -> complex:
        """
        Computes the vortex potential: V(z) = i * U * log(z - z_start).
        This creates a rotational influence around z_start.
        """
        return 1j * self.U * np.log(z - z_start)

    def source_sink_flow(self, z_start: complex, z: complex) -> complex:
        """
        Computes the source/sink potential: S(z) = U * log(z - z_start).
        This creates a flow toward or away from z_start.
        """
        return self.U * np.log(z - z_start)



class PotentialFlowGenerator:
    def __init__(self, agent: pycc.IDABot, target: pycc.Point2D, unit: Unit):
        """
        Generates a potential flow field around a region, including optional influences
        like borders, obstacles, and attack flows.
        """
        self.agent = agent
        self.target_position = target
        self.unit = unit

        # Compute base flow strength and border points
        self.U = self.calculate_region_perimeter()
        self.border_points = self.get_border_points()

        self.potential_flow = PotentialFlow(U=self.U, region_center=self.to_complex(self.target_position), scout=self.unit)

        # Add distance calculation helper
        pycc.Point2D.distance_to = lambda self, other: math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)


    def update_target(self, new_target: pycc.Point2D) -> None:
        self.U = self.calculate_region_perimeter()
        self.potential_flow.region_center = self.to_complex(new_target)
        self.target_position = new_target

    def get_velocity(self, position: pycc.Point2D, eps: float = 1e-5) -> complex:
        """
        Approximate the flow velocity at a given position by numerically differentiating
        the complex potential from get_total_flow.

        dw/dz ≈ (w(z+eps) - w(z-eps)) / (2*eps)
        Given q = dw/dz, velocity components are:
        u = real(q), v = -imag(q)
        """
        z = self.to_complex(position)
        w_forward = self.get_total_flow(z + eps)
        w_backward = self.get_total_flow(z - eps)

        q = (w_forward - w_backward) / (2 * eps)
        u = q.real
        v = -q.imag
        return u + 1j * v

    def visualize_flow1(self, look_radius: float = 10.0, resolution: int = 30) -> None:
        """
        Visualize the velocity field around the scout’s current position.
        look_radius defines how far in each direction from the scout’s position to visualize.
        resolution defines the number of points in each dimension.
        """
        scout_pos = self.unit.position
        x_min = scout_pos.x - look_radius
        x_max = scout_pos.x + look_radius
        y_min = scout_pos.y - look_radius
        y_max = scout_pos.y + look_radius

        x_vals = np.linspace(x_min, x_max, resolution)
        y_vals = np.linspace(y_min, y_max, resolution)
        X, Y = np.meshgrid(x_vals, y_vals)

        U_field = np.zeros((resolution, resolution), dtype=float)
        V_field = np.zeros((resolution, resolution), dtype=float)

        # Sample the velocity field at each point
        for i in range(resolution):
            for j in range(resolution):
                pos = pycc.Point2D(X[i, j], Y[i, j])
                vel = self.get_velocity(pos)
                U_field[i, j] = vel.real
                V_field[i, j] = vel.imag

        plt.figure(figsize=(8, 6))
        plt.quiver(X, Y, U_field, V_field, color='blue', pivot='mid', scale=20)

        # Plot enemy units as red circles if they're within the visualization area
        enemy_units = self.get_enemy_combat_units()
        for enemy in enemy_units:
            if (x_min <= enemy.position.x <= x_max) and (y_min <= enemy.position.y <= y_max):
                plt.scatter(enemy.position.x, enemy.position.y, c='red', marker='o', s=60, edgecolors='black', zorder=5)

        plt.title("Localized Velocity Field Around Scout")
        plt.xlabel('X')
        plt.ylabel('Y')
        plt.grid(True)
        plt.show()


    def visualize_flow(self, height: int, width: int, resolution: int = 50) -> None:
        """
        Visualize the velocity field over a specified region.
        height and width define the area, resolution defines sampling density.
        """
        x_vals = np.linspace(0, width, resolution)
        y_vals = np.linspace(0, height, resolution)
        X, Y = np.meshgrid(x_vals, y_vals)

        U_field = np.zeros((resolution, resolution), dtype=float)
        V_field = np.zeros((resolution, resolution), dtype=float)

        for i in range(resolution):
            for j in range(resolution):
                pos = pycc.Point2D(X[i, j], Y[i, j])
                vel = self.get_velocity(pos)
                U_field[i, j] = vel.real
                V_field[i, j] = vel.imag

        plt.figure(figsize=(8, 6))
        plt.quiver(X, Y, U_field, V_field, color='blue', pivot='mid')
        plt.title("Velocity Field from Potential Flow")
        plt.xlabel('X')
        plt.ylabel('Y')
        plt.grid(True)
        plt.tight_layout()
        plt.show()

    def get_all_obstacles(self) -> list[Unit]:
        """
        Gathers all relevant obstacles within the scout's sight range, including enemy buildings,
        neutral destructibles, and resources such as minerals and geysers that can block movement.
        Filters units within the scout's sight range only once.
        """

        sight_range = self.unit.unit_type.sight_range
        scout_position = self.unit.position

        # Filter all units once based on sight range
        nearby_units = [
            u for u in self.agent.get_all_units()
            if u.position.distance_to(scout_position) <= sight_range * 2
        ]

        # Collect relevant obstacles from filtered units
        obstacles = [
            u for u in nearby_units
            if (
                (u.player == pycc.PLAYER_ENEMY and u.unit_type.is_building) or
                (u.player == pycc.PLAYER_NEUTRAL and (u.unit_type.is_building or u.unit_type.is_mineral or u.unit_type.is_geyser)) or
                (u.unit_type.is_resource_depot or u.unit_type.is_refinery)
            )
        ]

        return obstacles

    def get_enemy_combat_units(self) -> list[Unit]:
        """Return a list of enemy combat units."""
        return [
            u for u in self.agent.get_all_units()
            if u.player == pycc.PLAYER_ENEMY and u.unit_type.is_combat_unit
        ]

    def calculate_region_perimeter(self) -> float:
        """
        Estimate a base flow strength (U) based on the perimeter formed by enemy buildings.
        If no enemy buildings are found, return a default value.
        """
        enemy_buildings = [
            u for u in self.agent.get_all_units()
            if u.player == pycc.PLAYER_ENEMY and u.unit_type.is_building
        ]

        if not enemy_buildings:
            return 20  # Arbitrary fallback value

        main_base = self.agent.base_location_manager.get_player_starting_base_location(pycc.PLAYER_ENEMY).position
        max_distance = max(b.position.distance_to(main_base) for b in enemy_buildings)
        return max_distance

    def get_border_points(self) -> list[pycc.Point2D]:
        """
        Extract and return points along the border of the map (edges of walkable space).
        """
        map_grid = [
            [int(self.agent.map_tools.is_walkable(y, x)) for x in range(self.agent.map_tools.width)]
            for y in range(self.agent.map_tools.height)
        ]
        extractor = EdgePointExtractor(grid=map_grid, distance=3.0)
        return extractor.get_edge_points()

    def get_total_flow(self, z: complex) -> complex:
        """
        Compute the total potential at position z (complex).
        Currently, this focuses primarily on region_flow.
        Additional flows (border, obstacle, attack) can be added as needed.
        """
        total_flow = self.potential_flow.region_flow(z)
        # Uncomment and adapt as needed when border, obstacle, and attack flows are ready:
        for bp in self.border_points:
            z_start = self.to_complex(bp)
            total_flow += self.potential_flow.border_flow(z_start=z_start, z=z)

        for obs in self.get_all_obstacles():
            z_obs = self.to_complex(obs.position)
            total_flow += self.potential_flow.obstacle_flow(z_o=z_obs, a=obs.radius, z=z)

        # Add attack flow from enemy combat units
        for enemy in self.get_enemy_combat_units():
            z_enemy = self.to_complex(enemy.position)
            attack_range = enemy.unit_type.attack_range
            total_flow += self.potential_flow.attack_flow(z_start=z_enemy, attack_range=attack_range, z=z)

        return total_flow

    def to_complex(self, coordinate: pycc.Point2D) -> complex:
        """Convert a Point2D coordinate to a complex number for flow calculations."""
        return coordinate.x + 1j * coordinate.y


class EdgePointExtractor:
    def __init__(self, grid, distance):
        """
        Initializes the EdgePointExtractor with the grid and the desired minimum distance between points.

        Parameters:
        - grid (2D list): The map where 1 represents walls and 0 represents walkable space.
        - distance (float): The minimum desired spacing between points along the wall edges.
        """
        self.grid = grid
        self.distance = distance
        self.rows = len(grid)
        self.cols = len(grid[0]) if self.rows > 0 else 0

    def get_edge_points(self):
        """
        Extracts edge points from the grid and reduces them so that no two points are closer than the specified distance.

        Returns:
        - selected_points (list of tuples): A list of (i, j) coordinates of the selected edge points.
        """
        # Step 1: Get all edge coordinates
        edge_points = self.detect_edges()

        # Step 2: Remove points that are too close to each other
        selected_points = self.reduce_points(edge_points)

        return selected_points

    def detect_edges(self):
        """
        Detects edge cells in the grid and returns a list of their coordinates.

        Returns:
        - edge_points (list of tuples): A list of (i, j) coordinates where each cell is an edge cell.
        """
        edge_points = []
        for i in range(self.rows):
            for j in range(self.cols):
                if self.grid[i][j] == 1:
                    # Check cardinal neighbors (up, down, left, right)
                    neighbors = self.get_cardinal_neighbors(i, j)
                    for ni, nj in neighbors:
                        if self.grid[ni][nj] == 0:
                            edge_points.append((i, j))
                            break  # Stop checking neighbors if edge is found
        return edge_points

    def get_cardinal_neighbors(self, i, j):
        """
        Returns the valid cardinal neighbor indices of cell (i, j).

        Parameters:
        - i, j (int): Indices of the cell.

        Returns:
        - neighbors (list of tuples): List of (ni, nj) neighbor indices.
        """
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]  # Up, down, left, right
        neighbors = []
        for di, dj in directions:
            ni, nj = i + di, j + dj
            if 0 <= ni < self.rows and 0 <= nj < self.cols:
                neighbors.append((ni, nj))
        return neighbors

    def reduce_points(self, edge_points):
        """
        Removes points from the edge_points list so that no two points are closer than the specified distance.

        Parameters:
        - edge_points (list of tuples): The original list of edge point coordinates.

        Returns:
        - selected_points (list of tuples): The reduced list of edge point coordinates.
        """
        # Convert list of edge points to a set for faster removal
        edge_points_set = set(edge_points)
        selected_points = []

        # Precompute the offsets within the specified distance
        offset_range = int(math.ceil(self.distance))
        offsets = []
        for dx in range(-offset_range, offset_range + 1):
            for dy in range(-offset_range, offset_range + 1):
                if dx == 0 and dy == 0:
                    continue  # Skip the center point
                distance = math.hypot(dx, dy)
                if distance <= self.distance:
                    offsets.append((dx, dy))

        while edge_points_set:
            # Pick an arbitrary point from the set
            i, j = edge_points_set.pop()
            selected_points.append((i, j))

            # Remove all points within the specified distance
            points_to_remove = []
            for dx, dy in offsets:
                ni, nj = i + dx, j + dy
                if 0 <= ni < self.rows and 0 <= nj < self.cols and (ni, nj) in edge_points_set:
                    points_to_remove.append((ni, nj))

            # Remove the points from the set
            for point in points_to_remove:
                edge_points_set.remove(point)


        selected_points2d = []    
        # Tuples to Point2d
        for point in selected_points:
            selected_points2d.append(pycc.Point2D(point[0], point[1]))
        
        return selected_points2d


