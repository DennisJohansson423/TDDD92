from typing import Union
import commandcenter as pycc
from modules.build_order import BuildOrder
from modules.py_unit import PyUnit
from modules.task_manager import TaskManager
from modules.unit_collection import UnitCollection
from modules.py_building_placer import PyBuildingPlacer
from modules import debugging as debug
from config import DEBUG_CHEATS, DEBUG_CONSOLE, DEBUG_LOGS, DEBUG_TEXT, DEBUG_UNIT, DEBUG_VISUAL, FRAME_SKIP, \
    BUILD_ORDER_PATH, USE_RESOURCE_MANAGER, USE_BAYESIAN_NETWORK, USE_BOIDS_POTENTIAL, USE_FLOOD_FILL, USE_DEBUG_FLOOD_FILL, USE_NAVIGATION, \
    USE_DFBB, DFBB_INSTEAD_OF_HARDCODE, DFBB_BUILD_ORDER_PATH
from modules.extra import unit_types_by_condition

if DEBUG_VISUAL:
    from visualdebugger.heat_map_debugger import HeatMapDebugger

if DEBUG_LOGS:
    from modules.tictoc import TicToc
    from modules.logger import Logger

if USE_RESOURCE_MANAGER:
    from modules.resource_manager import *

if USE_BAYESIAN_NETWORK:
    from modules.belief_network import BayesianNetworkModel, EnemyStateEstimator

if USE_BOIDS_POTENTIAL:
    from modules.potential_boids import BoidsPotential
    
if USE_FLOOD_FILL:
    from modules.flood_fill import FloodFill
    if USE_DEBUG_FLOOD_FILL:
        from visualdebugger.visualize_flood_fill import VisualizeFloodFill

if USE_NAVIGATION:
    import nav

if USE_DFBB:
    from modules.DFBB import *
    from modules.tictoc import *
    import os

class BasicAgent(pycc.IDABot):
    """Base agent for PyCommandCenter and SC2"""
    def __init__(self):
        pycc.IDABot.__init__(self)
        self.unit_collection = UnitCollection(self)
        if not USE_DFBB:
            self.build_order = BuildOrder(BUILD_ORDER_PATH)
            
        self.task_manager = TaskManager(self)
        self.py_building_placer = PyBuildingPlacer(self)
        self.internal_gas = 0
        self.internal_minerals = 0
        self.internal_supply = 0

        # Hard coded costs for upgrades since they are not available in the API
        self.UPGRADES = {
            pycc.UNIT_TYPEID.TERRAN_ORBITALCOMMAND: (150, 0),
            pycc.UNIT_TYPEID.TERRAN_PLANETARYFORTRESS: (150, 150),
            pycc.UNIT_TYPEID.ZERG_LAIR: (150, 100),
            pycc.UNIT_TYPEID.ZERG_HIVE: (200, 150)
        }
        self.WORKER_TYPES = set()
        self.COMBAT_TYPES = set()

        if DEBUG_VISUAL:
            self.debugger = HeatMapDebugger()

        if DEBUG_LOGS:
            self.timer = TicToc(prints=DEBUG_CONSOLE)
            self.logger = Logger()

        ### Simon ###
        if USE_BAYESIAN_NETWORK:
            #Bayesian Model
            self.bayesian_model = BayesianNetworkModel(self)
            self.enemy_state_estimator = EnemyStateEstimator()
            self.strategy_attack = None
            self.strategy_upgrade = None
            self.strategy_resource = None

        ### David ###
        if USE_BOIDS_POTENTIAL:
            self.potential = BoidsPotential(self, use_boids = True)

        if USE_NAVIGATION:
            self.nav = nav.Navigation(self)

        ### Antti ###
        if USE_DFBB:
            self.dfbb_timer = TicToc(prints=False)
            self.dfbb_timer.tic("dfbb")
            self.dfbb = DFBB(self, self.unit_collection)
            self.current_strategy = None
            self.mineral_gas_prio = None
            self.stratometer = ""
            file_path = "builds/DFBB_build_order"
            with open(file_path, 'w') as file:
                pass
            self.build_order = BuildOrder(DFBB_BUILD_ORDER_PATH)

    def on_game_start(self) -> None:
        """Runs on game start. Loads necessary data and generates settings"""
        pycc.IDABot.on_game_start(self)
        self.tech_tree.suppress_warnings(True)
        self.WORKER_TYPES = unit_types_by_condition(self, lambda u: u.is_worker)
        self.COMBAT_TYPES = unit_types_by_condition(self, lambda u: u.is_combat_unit)
        
        if DEBUG_VISUAL:
            self.set_up_debugging()
            self.debugger.on_start()
            self.debugger.on_step(lambda: debug.debug_map(self))
        if DEBUG_CHEATS:
            debug.up_up_down_down_left_right_left_right_b_a_start(self)
            
        ### Dennis ###
        if USE_RESOURCE_MANAGER:
            init_resource_queues(self, self.base_location_manager)
            if not USE_DFBB:
                self.mineral_gas_prio = "prio_minerals"
            
        ### JONTE ###
        if USE_FLOOD_FILL:
            self.flood_fill = FloodFill(agent=self)
            self.flood_fill.create_binary_map()
            self.flood_fill.prepare_flood_fill()
            self.choke_points = {}
            self.primary_choke_point = None
            
            if USE_DEBUG_FLOOD_FILL:
                self.vizualise_flood_fill = VisualizeFloodFill(self.flood_fill, cell_size=5, alongside_game=True)
        
    def on_game_end(self) -> None:
        """Runs on game end. Saves a replay file."""
        pycc.IDABot.on_game_end(self)
        self.save_replay("latest.SC2Replay")

    def on_step(self) -> None:
        """Runs on every step and runs IDABot.on_step. Updates variables, reassigns units, updates debug info."""
        pycc.IDABot.on_step(self)
        
        if self.current_frame % FRAME_SKIP == 1:
            if DEBUG_LOGS:
                self.logger.new_row()
                self.timer.tic()

            self.internal_gas = self.gas
            self.internal_minerals = self.minerals
            self.internal_supply = self.current_supply

            self.unit_collection.on_step()

        if self.current_frame % FRAME_SKIP == 1:
            new_units = [u for u in self.unit_collection.new_units_this_step if u.player == pycc.PLAYER_SELF]
            self.task_manager.on_step(new_units)

            self.unit_collection.remove_dead_units()

        if self.current_frame % FRAME_SKIP == 1 and DEBUG_LOGS:
            self.timer.toc()
            self.logger.add("frame", self.current_frame)
            self.logger.add("units", len(self.unit_collection.get_group(pycc.PLAYER_SELF)))
            for key, val in self.timer:
                self.logger.add(key, val)
            self.timer.reset()

        if DEBUG_UNIT:
            debug.debug_units(self)
        if DEBUG_TEXT:
            debug.debug_text(self)
        
        ### Simon ###
        if USE_BAYESIAN_NETWORK:
            # Bayesian Model Inference
            if self.current_frame % 300 == 0:
                # Collect evidence from the game state
                evidence = self.bayesian_model.collect_evidence()
                self.strategy = self.bayesian_model.estimate_best_strategy(evidence)

                self.strategy_attack = self.strategy[0]
                self.strategy_upgrade = self.strategy[1]
                self.strategy_resource = self.strategy[2]

                print("COMBAT: ", self.strategy_attack)
                print("RESOURCE: ", self.strategy_resource)
                print("UPGRADE: ", self.strategy_upgrade)
                
        ### ANTTI ###
        if USE_DFBB:
            if USE_BAYESIAN_NETWORK:
                goal_strategy = self.dfbb.classify_bayesian_info(self.strategy_attack, self.strategy_upgrade, self.strategy_resource) #"upgrading"  #adjust dynamically based on simon
            else:
                goal_strategy = "attacking"
            self.stratometer = goal_strategy
            current_strategy = self.current_strategy
            dont_update = False

            if current_strategy == goal_strategy:
                dont_update = True

            elapsed_time = time.time() - self.dfbb_timer._time_start.get("dfbb", time.time())
            if elapsed_time >= 30: #or 45 if lag?
                
                if "dfbb" in self.dfbb_timer._await_toc:
                    self.dfbb_timer.toc("dfbb") 

                dfbb_result, self.current_strategy, self.mineral_gas_prio = self.dfbb.DFBB_main(goal_strategy, self.current_strategy, self.mineral_gas_prio, DFBB_INSTEAD_OF_HARDCODE)

                if dfbb_result and DFBB_INSTEAD_OF_HARDCODE:
                    self.build_order = BuildOrder(DFBB_BUILD_ORDER_PATH)
                elif dfbb_result and dont_update == False:
                    self.build_order = BuildOrder(DFBB_BUILD_ORDER_PATH)
                    dont_update = True
                self.dfbb_timer.tic("dfbb")
            
        ### Dennis ###
        if USE_RESOURCE_MANAGER and self.current_frame % 100 == 0:
            if len(self.unit_collection.get_group(pycc.UNIT_TYPEID.TERRAN_SCV)) >= 15:
                gas_enabled = True
            else:
                gas_enabled = False

            # Assign tasks to idle workers
            for worker in self.unit_collection.get_group(pycc.UNIT_TYPEID.TERRAN_SCV):
                if worker.is_idle:
                    if gas_enabled:
                        assign_worker_to_best_task(self, worker, self.base_location_manager, self.mineral_gas_prio)
                    else:
                        assign_worker_to_best_task(self, worker, self.base_location_manager, "prio_minerals")

        ### DAVID ### 
        if USE_BOIDS_POTENTIAL and USE_BAYESIAN_NETWORK:
            if self.strategy_attack == "Aggressive Action":
                self.task_manager.ATTACK_PRIO = 15
            elif self.strategy_attack == "Moderate Action":
                self.task_manager.ATTACK_PRIO = 6
            else: 
                self.task_manager.ATTACK_PRIO = 2 

        ### JONTE ###
        if USE_FLOOD_FILL:
            if self.current_frame % 400 == 0:   
                if USE_BAYESIAN_NETWORK:
                    self.flood_fill.update_current_strategy(self.strategy_attack)
                self.choke_points = self.flood_fill.find_choke_points()
                self.primary_choke_point = self.flood_fill.get_primary_choke_point()
                
            if USE_DEBUG_FLOOD_FILL:
                self.vizualise_flood_fill.update_pygame_loop() # Needed for pygame not to crash
                if self.current_frame % 400 == 0:
                    self.vizualise_flood_fill.display_map()

        ### Belmin ###
        if USE_NAVIGATION:
            self.nav.on_step()
                        
    def set_up_debugging(self) -> None:
        """Set up visual debugger"""
        self.debugger.tile_margin = 1
        # sets the colormap for the debugger {(interval): (r, g, b)}
        color_map = {
            (0, 0): (0, 0, 0,),
            (1, 1): (255, 255, 255)
        }
        self.debugger.set_color_map(color_map)
    
    ### Antti ###
    if USE_DFBB:
        def get_stratometer(self):
            return self.stratometer

    def can_afford(self, unit_type: Union[pycc.UnitType, pycc.UPGRADE_ID]) -> bool:
        """
        Returns whether the agent have the sufficient minerals, vespene gas, and available supply to build
        unit/upgrade
        """
        minerals, gas, supply = self._cost(unit_type)
        supply_left = self.max_supply - self.internal_supply
        return self.internal_minerals >= minerals and self.internal_gas >= gas and supply_left >= supply

    def pay(self, unit_type: Union[pycc.UnitType, pycc.UPGRADE_ID]) -> None:
        """Reduces our internal resources as if the agent payed for the unit/upgrade"""
        minerals, gas, supply = self._cost(unit_type)
        self.internal_gas -= minerals
        self.internal_minerals -= gas
        self.internal_supply += supply

    def _cost(self, unit_type: Union[pycc.UnitType, pycc.UPGRADE_ID]) -> tuple[int, int, int]:
        """Calculates the mineral, gas, and supply cost of a unit/upgrade"""
        data = self.tech_tree.get_data(unit_type)
        minerals, gas, supply = data.mineral_cost, data.gas_cost, data.supply_cost
        if isinstance(unit_type, pycc.UnitType) and unit_type.unit_typeid in self.UPGRADES:
            minerals, gas = self.UPGRADES[unit_type.unit_typeid]
        return minerals, gas, supply
    
    
