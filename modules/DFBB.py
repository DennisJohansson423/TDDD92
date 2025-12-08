import commandcenter as pycc
import json
from modules.unit_collection import UnitCollection
from modules.extra import *


class DFBB:
    def __init__(self, agent, unit_collection):
        """Init of the DFBB class."""
        self.agent = agent
        self.unit_collection = unit_collection
        with open("techtree.json", "r") as file:
            self.tech_tree = json.load(file)["terran"]


    def DFBB_main(self, goal_strategy, current_strategy, mineral_gas_prio, dfbb_instead_of_hardcode):
        """The main function for DFBB."""
        needed = self.calculate_needed(goal_strategy)
        #print("Needed is currently: ", needed)
        if current_strategy == goal_strategy:
            if dfbb_instead_of_hardcode:
                if self.is_needed_empty(needed):
                    return None, current_strategy, mineral_gas_prio
            else:
                return None, current_strategy, mineral_gas_prio        
        
        verified_needed = self.verify_needed_types(needed)
        mineral_gas_prio = self.calculate_mineral_gas_cost(verified_needed)
        rename_needed = self.rename_needed(verified_needed)
        
        build_order= self.generate_optimal_build_order(verified_needed, dfbb_instead_of_hardcode, goal_strategy)

        if build_order:
            current_strategy = goal_strategy

        return build_order, current_strategy, mineral_gas_prio
    

    def get_current_strategy(self):
        """Getter for our current strategy."""
        return self.current_strategy


    def map_id(self, task_type):
        """Maps tasks to UNIT_TYPEID or UPGRADE_ID."""
        #With and without terran names atm to skip a bug
        unit_type_map = {
            "SCV": pycc.UNIT_TYPEID.TERRAN_SCV,
            "MARINE": pycc.UNIT_TYPEID.TERRAN_MARINE,
            "MEDIVAC": pycc.UNIT_TYPEID.TERRAN_MEDIVAC,
            "SIEGETANK": pycc.UNIT_TYPEID.TERRAN_SIEGETANK,
            "BARRACKS": pycc.UNIT_TYPEID.TERRAN_BARRACKS,
            "FACTORY": pycc.UNIT_TYPEID.TERRAN_FACTORY,
            "FACTORYTECHLAB": pycc.UNIT_TYPEID.TERRAN_FACTORYTECHLAB,
            "STARPORT": pycc.UNIT_TYPEID.TERRAN_STARPORT,
            "SUPPLYDEPOT": pycc.UNIT_TYPEID.TERRAN_SUPPLYDEPOT,
            "ENGINEERINGBAY": pycc.UNIT_TYPEID.TERRAN_ENGINEERINGBAY,
            "REFINERY": pycc.UNIT_TYPEID.TERRAN_REFINERY,
            "ARMORY": pycc.UNIT_TYPEID.TERRAN_ARMORY,
            "COMMAND CENTER": pycc.UNIT_TYPEID.TERRAN_COMMANDCENTER,
            "COMMANDCENTER": pycc.UNIT_TYPEID.TERRAN_COMMANDCENTER,
            "PLANETARYFORTRESS": pycc.UNIT_TYPEID.TERRAN_PLANETARYFORTRESS,
            "TERRAN_SCV": pycc.UNIT_TYPEID.TERRAN_SCV,
            "TERRAN_MARINE": pycc.UNIT_TYPEID.TERRAN_MARINE,
            "TERRAN_MEDIVAC": pycc.UNIT_TYPEID.TERRAN_MEDIVAC,
            "TERRAN_SIEGETANK": pycc.UNIT_TYPEID.TERRAN_SIEGETANK,
            "TERRAN_BARRACKS": pycc.UNIT_TYPEID.TERRAN_BARRACKS,
            "TERRAN_FACTORY": pycc.UNIT_TYPEID.TERRAN_FACTORY,
            "TERRAN_FACTORYTECHLAB": pycc.UNIT_TYPEID.TERRAN_FACTORYTECHLAB,
            "TERRAN_STARPORT": pycc.UNIT_TYPEID.TERRAN_STARPORT,
            "TERRAN_SUPPLYDEPOT": pycc.UNIT_TYPEID.TERRAN_SUPPLYDEPOT,
            "TERRAN_ENGINEERINGBAY": pycc.UNIT_TYPEID.TERRAN_ENGINEERINGBAY,
            "TERRAN_REFINERY": pycc.UNIT_TYPEID.TERRAN_REFINERY,
            "TERRAN_ARMORY": pycc.UNIT_TYPEID.TERRAN_ARMORY,
            "TERRAN_PLANETARYFORTRESS": pycc.UNIT_TYPEID.TERRAN_PLANETARYFORTRESS,
            "TERRAN_COMMANDCENTER": pycc.UNIT_TYPEID.TERRAN_COMMANDCENTER
        }
        upgrade_map = {
            "TERRANINFANTRYWEAPONSLEVEL1": pycc.UPGRADE_ID.TERRANINFANTRYWEAPONSLEVEL1,
            "TERRANINFANTRYWEAPONSLEVEL2": pycc.UPGRADE_ID.TERRANINFANTRYWEAPONSLEVEL2,
            "TERRANINFANTRYARMORSLEVEL1": pycc.UPGRADE_ID.TERRANINFANTRYARMORSLEVEL1,
            "TERRANINFANTRYARMORSLEVEL2": pycc.UPGRADE_ID.TERRANINFANTRYARMORSLEVEL2,
        }
        if task_type in unit_type_map:
            unit_type_id = unit_type_map[task_type]
            return pycc.UnitType(unit_type_id, self.agent)
        elif task_type in upgrade_map:
            return upgrade_map[task_type]
        else:
            raise ValueError(f"Unknown task type: {task_type}")


    def get_prerequisites(self, task_type):
        """Gets the prerequisites for a task."""
        data = self.agent.tech_tree.get_data(task_type)
        prerequisites = set()
        prerequisites.update(data.required_upgrades)
        prerequisites.update(data.required_addons)
        prerequisites.update(data.required_units)
        return prerequisites


    def verify_needed_types(self, needed):
        """Double checks prerequisites for all types of tasks in needed."""
        needed_types = []
        prereqs_cache = {}
        for key, value in needed.items():
            if isinstance(value, dict): #units or buildings
                for unit, count in value.items():
                    needed_types.extend([self.map_id(unit).name] * count)
            elif isinstance(value, list): #upgrades
                for upgrade in value:
                    needed_types.append(upgrade)
        copy_types = needed_types[:] #copy to add prereqs
        #get prereqs without dupes
        for task_type in needed_types:
            data = self.map_id(task_type)
            if not has_prerequisites(self.agent, data):
                #check cache first
                if task_type in prereqs_cache:
                    prerequisites = prereqs_cache[task_type]
                else:
                    #cache prereqs
                    prerequisites = self.get_prerequisites(data)
                    prereqs_cache[task_type] = prerequisites
                #add prereqs to copy list
                for prerequisite in prerequisites:
                    if prerequisite.name not in copy_types:
                        copy_types.append(prerequisite.name)
        #combine similar units
        needed_combined = {}
        for step in copy_types:
            if step != 'TERRAN_SUPPLYDEPOTLOWERED' and step != 'TERRAN_BARRACKSFLYING' and step != 'TERRAN_FACTORYFLYING' and step != 'TERRAN_COMMANDCENTERFLYING' and step != 'TERRAN_ORBITALCOMMAND' and step != 'TERRAN_ORBITALCOMMANDFLYING':
                if step not in needed_combined:
                    needed_combined[step] = 1
                else:
                    needed_combined[step] += 1
        return needed_combined
    
    
    def calculate_mineral_gas_cost(self, needed):
        """Calculates total mineral and gas costs for needed."""
        starcraft_costs = {
        "units": {
            "SCV": {"minerals": 50, "gas": 0},
            "MARINE": {"minerals": 50, "gas": 0},
            "MEDIVAC": {"minerals": 100, "gas": 100},
            "SIEGETANK": {"minerals": 150, "gas": 125},
            "SCV": {"minerals": 50, "gas": 0},
            "MARINE": {"minerals": 50, "gas": 0},
            "MEDIVAC": {"minerals": 100, "gas": 100},
            "SIEGETANK": {"minerals": 150, "gas": 125}
        },
        "buildings": {
            "BARRACKS": {"minerals": 150, "gas": 0},
            "FACTORY": {"minerals": 150, "gas": 100},
            "FACTORY TECHLAB": {"minerals": 50, "gas": 25},
            "STARPORT": {"minerals": 150, "gas": 100},
            "SUPPLY DEPOT": {"minerals": 100, "gas": 0},
            "ENGINEERING BAY": {"minerals": 125, "gas": 0},
            "REFINERY": {"minerals": 75, "gas": 0},
            "ARMORY": {"minerals": 150, "gas": 100},
            "COMMAND CENTER": {"minerals": 400, "gas": 0},
            "BUNKER": {"minerals": 100, "gas": 0},
            "PLANETARY FORTRESS": {"minerals": 150, "gas": 150},
            "SENSORTOWER": {"minerals": 100, "gas": 50}
        },
        "upgrades": {
            "TERRANINFANTRYWEAPONSLEVEL1": {"minerals": 100, "gas": 100},
            "TERRANINFANTRYARMORSLEVEL1": {"minerals": 100, "gas": 100},
            "TERRANINFANTRYWEAPONSLEVEL2": {"minerals": 175, "gas": 175},
            "TERRANINFANTRYARMORSLEVEL2": {"minerals": 175, "gas": 175}
            }
        }
        total_minerals = 0
        total_gas = 0
        for task, count in needed.items():
            task_type = task.split(" x")[0]
            task_name = task_type.strip()

            if task_name in starcraft_costs["units"]:
                cost = starcraft_costs["units"][task_name]
            elif task_name in starcraft_costs["buildings"]:
                cost = starcraft_costs["buildings"][task_name]
            elif task_name in starcraft_costs["upgrades"]:
                cost = starcraft_costs["upgrades"][task_name]
            else:
                continue
            total_minerals += cost["minerals"] * count
            total_gas += cost["gas"] * count

        if total_minerals >= total_gas:
            return "prio_minerals"
        else:
            return "prio_gas"

    
    def rename_needed(self, needed):
        """Renames units in needed so that they follow the same naming convention"""
        result = []
        if isinstance(needed, dict):
            for task in needed:
                if needed[task] > 1:
                    if "TERRAN_" in task:
                        new_task = task.replace("TERRAN_", "")
                        item = (str(new_task) + " x" + str(needed[task]))
                        result.append(item)
                    elif "TERRAN" in task:
                        new_task = task.replace("TERRAN", "")
                        item = (str(new_task) + " x" + str(needed[task]))
                        result.append(item)
                    else:
                        result.append(str(task) + " x" + str(needed[task]))
                else:
                    if "TERRAN_" in task:
                        new_task = task.replace("TERRAN_", "")
                        result.append(str(new_task))
                    elif "TERRAN" in task:
                        new_task = task.replace("TERRAN", "")
                        result.append(str(new_task))
                    else:
                        result.append(str(task))
        elif isinstance(needed, list):
            for task in needed:
                if "INFANTRY" in task: #for some upgrades
                    result.append(str(task))
                elif "TERRAN_" in task:
                    new_task = task.replace("TERRAN_", "")
                    result.append(str(new_task))
                elif "TERRAN" in task:
                    new_task = task.replace("TERRAN", "")
                    result.append(str(new_task))
                else:
                    result.append(str(task))
        return result
    

    def get_mineral_cost(self, task):
        """Gets the mineral cost for a task."""
        mineral_costs = {
            "TERRAN_SCV": 50,
            "TERRAN_MARINE": 50,
            "TERRAN_MEDIVAC": 100,
            "TERRAN_SIEGETANK": 150,
            "TERRAN_BARRACKS": 150,
            "TERRAN_FACTORY": 150,
            "TERRAN_FACTORYTECHLAB": 50,
            "TERRAN_STARPORT": 150,
            "TERRAN_SUPPLYDEPOT": 100,
            "TERRAN_ENGINEERINGBAY": 125,
            "TERRAN_REFINERY": 75,
            "TERRAN_ARMORY": 150,
            "TERRAN_COMMANDCENTER": 400,
            "TERRAN_BUNKER": 100,
            "TERRAN_PLANETARYFORTRESS": 150,
            "TERRAN_SENSORTOWER": 100,
            "TERRANINFANTRYWEAPONSLEVEL1": 100,
            "TERRANINFANTRYARMORSLEVEL1": 100,
            "TERRANINFANTRYWEAPONSLEVEL2": 175,
            "TERRANINFANTRYARMORSLEVEL2": 175
            }
        mineral_cost = mineral_costs[task]
        return mineral_cost    

    def get_gas_cost(self, task):
        """Gets the gas cost for a task."""
        gas_costs = {
            "TERRAN_SCV": 0,
            "TERRAN_MARINE": 0,
            "TERRAN_MEDIVAC": 100,
            "TERRAN_SIEGETANK": 125,
            "TERRAN_BARRACKS": 0,
            "TERRAN_FACTORY": 100,
            "TERRAN_FACTORYTECHLAB": 25,
            "TERRAN_STARPORT": 100,
            "TERRAN_SUPPLYDEPOT": 0,
            "TERRAN_ENGINEERINGBAY": 0,
            "TERRAN_REFINERY": 0,
            "TERRAN_ARMORY": 100,
            "TERRAN_COMMANDCENTER": 0,
            "TERRAN_BUNKER": 0,
            "TERRAN_PLANETARYFORTRESS": 150,
            "TERRAN_SENSORTOWER": 50,
            "TERRANINFANTRYWEAPONSLEVEL1": 100,
            "TERRANINFANTRYARMORSLEVEL1": 100,
            "TERRANINFANTRYWEAPONSLEVEL2": 175,
            "TERRANINFANTRYARMORSLEVEL2": 175
            }
        gas_cost = gas_costs[task]
        return gas_cost

    def get_time(self, task):
        """Gets the build time for a task."""
        build_times = {
            "TERRAN_SCV": 12,
            "TERRAN_MARINE": 25,
            "TERRAN_MEDIVAC": 50,
            "TERRAN_SIEGETANK": 45,
            "TERRAN_BARRACKS": 65,
            "TERRAN_FACTORY": 70,
            "TERRAN_FACTORYTECHLAB": 40,
            "TERRAN_STARPORT": 50,
            "TERRAN_SUPPLYDEPOT": 35,
            "TERRAN_ENGINEERINGBAY": 40,
            "TERRAN_REFINERY": 35,
            "TERRAN_ARMORY": 60,
            "TERRANINFANTRYWEAPONSLEVEL1": 120,
            "TERRANINFANTRYARMORSLEVEL1": 120,
            "TERRANINFANTRYWEAPONSLEVEL2": 136,
            "TERRANINFANTRYARMORSLEVEL2": 136,
            "TERRAN_PLANETARYFORTRESS": 36,
            "TERRAN_COMMANDCENTER": 125
        }
        task_time = build_times[task]
        return task_time
    

    def dfbb_search(self, needed_tasks, current_order, current_time, minerals_left, gas_left, best_order, best_time):
        """Explanation of this DFBB algorithm: This DFBB search finds the fastest combination of up to 8 tasks
        from needed_tasks, considering prerequisites and resources."""
        #base case, stop when 8 tasks are selected or no tasks left
        if len(current_order) == 8 or not needed_tasks:
            if current_time < best_time:
                return current_order.copy(), current_time  #here we update our best solution
            return best_order, best_time

        #create counter to manage task counts
        task_counts = {task: needed_tasks.count(task) for task in set(needed_tasks)}

        #loop through each task in the remaining needed_tasks
        for task in list(task_counts.keys()):
            if task_counts[task] > 0:
                #check prereqs for task are satisfied globally
                if has_prerequisites(self.agent, self.map_id(task)):
                    mineral_cost = self.get_mineral_cost(task)
                    gas_cost = self.get_gas_cost(task)
                    #check enough resources available for task
                    if mineral_cost <= minerals_left and gas_cost <= gas_left:
                        #temp update state by selecting task
                        current_order.append(task)
                        current_time += self.get_time(task)
                        minerals_left -= mineral_cost
                        gas_left -= gas_cost
                        #remove one task from count for recursive call
                        remaining_tasks = needed_tasks.copy()
                        remaining_tasks.remove(task)
                        #calc upper bound for pruning
                        estimated_time = current_time + sum(
                            self.get_time(t) for t in remaining_tasks[:8 - len(current_order)]
                        )
                        #prune if estimated upper bound exceeds our best_time
                        if estimated_time < best_time:
                            best_order, best_time = self.dfbb_search(
                                remaining_tasks,
                                current_order,
                                current_time,
                                minerals_left,
                                gas_left,
                                best_order,
                                best_time
                            )
                        #backtrack state for next iteration
                        current_order.pop()
                        current_time -= self.get_time(task)
                        minerals_left += mineral_cost
                        gas_left += gas_cost

        return best_order, best_time


    def dfbb(self, needed, minerals, gas):
        """Init and execute the DFBB search with a limited chunk of tasks from needed."""
        current_order = []
        current_time = 0
        needed_chunk = []
        best_order = []
        best_time = float("inf")

        expanded_needed = []
        for key, count in needed.items():
            expanded_needed += [key] * count

        task_count = {task: 0 for task in needed.keys()}

        for task in expanded_needed:
            if len(needed_chunk) >= 10:
                break
            if (task_count[task] < needed[task] and
                    has_prerequisites(self.agent, self.map_id(task))):
                needed_chunk.append(task)
                task_count[task] += 1

        if not needed_chunk:
            return []
        best_order, best_time = self.dfbb_search(
            needed_chunk,
            current_order,
            current_time,
            minerals,
            gas,
            best_order,
            best_time
        )
        return best_order


    def generate_optimal_build_order(self, needed, dfbb_instead_of_hardcode, goal_strategy):
        """Calls the dfbb init function and retreives needed units that are written into the
           DFBB build order file before the build order is loaded. Also has an option to use hardcoded
           build orders instead of DFBB algo."""
        if dfbb_instead_of_hardcode:
            result = self.dfbb(needed, 1500, 1500)
            final_result = self.rename_needed(result)
            print("Final result for current chosen build order: ", final_result)
        else:
            if goal_strategy == "attacking":
                final_result = [
                    "COMMAND CENTER x2",
                    "SUPPLYDEPOT x10",
                    "BARRACKS x6",
                    "MARINE x25",
                    "ENGINEERINGBAY x1",
                    "FACTORY x2",
                    "FACTORYTECHLAB x2",
                    "STARPORT x1",
                    "ARMORY x1",
                    "PLANETARYFORTRESS x2",
                    "MARINE x25",
                    "SIEGETANK x15",
                    "MEDIVAC x10"
                ]
            elif goal_strategy == "upgrading":
                final_result = [
                "COMMAND CENTER x2",
                "SUPPLYDEPOT x1",
                "REFINERY x1",
                "BARRACKS x1",
                "ENGINEERINGBAY x1",
                "ARMORY x1",
                "PLANETARYFORTRESS x2",
                "TERRANINFANTRYWEAPONSLEVEL1",
                "TERRANINFANTRYARMORSLEVEL1",
                "TERRANINFANTRYWEAPONSLEVEL2",
                "TERRANINFANTRYARMORSLEVEL2",
                "COMMAND CENTER x2",
                "SUPPLYDEPOT x5",
                "REFINERY x2",
                "BARRACKS x1",
                "MARINE x5",
                "ENGINEERINGBAY x1",
                "ARMORY x1",
                "PLANETARYFORTRESS x2",
                "SCV x30",
                "MARINE x5"
                ]
            elif goal_strategy == "resources":
                final_result = build_order = [
                "COMMAND CENTER x2",
                "SUPPLYDEPOT x5",
                "SCV x25",
                "REFINERY x4",
                "COMMAND CENTER x2",
                "SUPPLYDEPOT x5",
                "SCV x25",
                "REFINERY x4",
                "BARRACKS x2",
                "MARINE x10",
                "ENGINEERINGBAY x1",
                "PLANETARYFORTRESS x4",
                ]
        if len(final_result) > 0:
            if final_result[0] == "MARINE":    
                if len(self.unit_collection.get_group(pycc.UNIT_TYPEID.TERRAN_BARRACKS)) < 1:
                    final_result[0] = "BARRACKS"
        
        file_path = "builds/DFBB_build_order"
        with open(file_path, "w") as file:
            file.write("\n".join(final_result))  #write each item on a new line in the dfbb build order file     

        if final_result:
            return True
        else:
            return False        


    def update_resources(self):
        """Updates our internal minerals and gas."""
        self.minerals = self.agent.internal_minerals
        self.gas = self.agent.internal_gas


    def calculate_needed(self, goal_strategy):
        """Calculates our needed units so that we reach our goal state unit quantities from our current state."""
        current_state = self.get_current_state()
        goal_state = self.get_goal_state(goal_strategy)

        needed = {
            "units": {},
            "buildings": {},
            "upgrades": []
        }
        #needed units
        for unit_type, goal_count in goal_state["units"].items():
            current_count = current_state["units"].get(unit_type, 0)
            needed_count = max(0, goal_count - current_count)
            needed["units"][unit_type] = needed_count
        #needed buildings
        for building_type, goal_count in goal_state["buildings"].items():
            current_count = current_state["buildings"].get(building_type, 0)
            needed_count = max(0, goal_count - current_count)
            needed["buildings"][building_type] = needed_count
        #needed upgrades
        for upgrade in goal_state.get("upgrades", []):
            if upgrade not in current_state.get("upgrades", []):
                needed["upgrades"].append(upgrade)

        return needed


    def is_needed_empty(self, needed):
        """Checks if needed is empty."""
        for unit_count in needed["units"].values():
            if unit_count > 0:
                return False
        for building_count in needed["buildings"].values():
            if building_count > 0:
                return False
        if len(needed["upgrades"]) > 0:
            return False
        return True


    def get_current_state(self):
        """Gets our current state."""
        self.update_resources()
        current_state = {
            "resources": {"minerals": self.minerals, "vespene": self.gas},
            "units":
            {"SCV": len(self.unit_collection.get_group(pycc.UNIT_TYPEID.TERRAN_SCV)),
            "MARINE": len(self.unit_collection.get_group(pycc.UNIT_TYPEID.TERRAN_MARINE)),
            "MEDIVAC": len(self.unit_collection.get_group(pycc.UNIT_TYPEID.TERRAN_MEDIVAC)),
            "SIEGETANK": len(self.unit_collection.get_group(pycc.UNIT_TYPEID.TERRAN_SIEGETANK))},
            "buildings":
            {"BARRACKS": len(self.unit_collection.get_group(pycc.UNIT_TYPEID.TERRAN_BARRACKS)),
            "FACTORY": len(self.unit_collection.get_group(pycc.UNIT_TYPEID.TERRAN_FACTORY)),
            "FACTORYTECHLAB": len(self.unit_collection.get_group(pycc.UNIT_TYPEID.TERRAN_FACTORYTECHLAB)),
            "STARPORT": len(self.unit_collection.get_group(pycc.UNIT_TYPEID.TERRAN_STARPORT)),
            "BUNKER": len(self.unit_collection.get_group(pycc.UNIT_TYPEID.TERRAN_BUNKER)),
            "PLANETARYFORTRESS": len(self.unit_collection.get_group(pycc.UNIT_TYPEID.TERRAN_PLANETARYFORTRESS)),
            "SENSORTOWER": len(self.unit_collection.get_group(pycc.UNIT_TYPEID.TERRAN_SENSORTOWER)),
            "COMMANDCENTER": len(self.unit_collection.get_group(pycc.UNIT_TYPEID.TERRAN_COMMANDCENTER)), 
            "REFINERY": len(self.unit_collection.get_group(pycc.UNIT_TYPEID.TERRAN_REFINERY)),
            "SUPPLYDEPOT": len(self.unit_collection.get_group(pycc.UNIT_TYPEID.TERRAN_SUPPLYDEPOT)),
            "ENGINEERINGBAY": len(self.unit_collection.get_group(pycc.UNIT_TYPEID.TERRAN_ENGINEERINGBAY)),
            "ARMORY": len(self.unit_collection.get_group(pycc.UNIT_TYPEID.TERRAN_ARMORY))
            }
            }
        return current_state
    
    
    def get_goal_state(self, goal_strategy):
        """Gets our goal state depending on goal strategy."""
        if goal_strategy == "attacking":
            goal_state = {
                "units": {"MARINE": 50, "SIEGETANK": 15},
                "buildings": {"BARRACKS": 6, "SUPPLYDEPOT": 10, "COMMANDCENTER": 2, "PLANETARYFORTRESS": 2}
            }
        elif goal_strategy == "upgrading":
            goal_state = {
                "units": {"SCV": 15, "MARINE": 10},
                "buildings": {"ENGINEERINGBAY": 2, "ARMORY": 2, "FACTORY": 2, "FACTORYTECHLAB": 2, "REFINERY": 2, "BARRACKS": 2, "SUPPLYDEPOT": 6, "COMMANDCENTER": 4, "PLANETARYFORTRESS": 10}
            }
        elif goal_strategy == "resources":
            goal_state = {
                "units": {"SCV": 30, "MARINE": 10},
                "buildings": {"REFINERY": 6, "SUPPLYDEPOT": 8, "BARRACKS": 2, "COMMANDCENTER": 3, "PLANETARYFORTRESS": 3}
            }
        else:
            return {}
        return goal_state


    def classify_bayesian_info(self, strategy_attack, strategy_upgrade, strategy_resource):      
        """Classifies our input from the bayesian network into three different strategies."""  
        #attacking
        goal_strategy = "attacking"
        
        if strategy_attack == "Aggressive Action" and strategy_upgrade == "Moderate Action" and strategy_resource == "No Action":
            goal_strategy = "attacking"
        elif strategy_attack == "Aggressive Action" and strategy_upgrade == "No Action" and strategy_resource == "Moderate Action":
            goal_strategy = "attacking"
        elif strategy_attack == "Aggressive Action" and strategy_upgrade == "No Action" and strategy_resource == "No Action":
            goal_strategy = "attacking"
        elif strategy_attack == "Moderate Action" and strategy_upgrade == "No Action" and strategy_resource == "No Action":
            goal_strategy = "attacking"
        elif strategy_attack == "Moderate Action" and strategy_upgrade == "Moderate Action" and strategy_resource == "No Action":
            goal_strategy = "attacking"
        #upgrading
        elif strategy_attack == "Moderate Action" and strategy_upgrade == "Aggressive Action" and strategy_resource == "No Action":
            goal_strategy = "upgrading"
        elif strategy_attack == "No Action" and strategy_upgrade == "Aggressive Action" and strategy_resource == "Moderate Action":
            goal_strategy = "upgrading"
        elif strategy_attack == "No Action" and strategy_upgrade == "Aggressive Action" and strategy_resource == "No Action":
            goal_strategy = "upgrading"
        elif strategy_attack == "No Action" and strategy_upgrade == "Moderate Action" and strategy_resource == "No Action":
            goal_strategy = "upgrading"
        elif strategy_attack == "No Action" and strategy_upgrade == "No Action" and strategy_resource == "No Action":
            goal_strategy = "upgrading"
        elif strategy_attack == "Moderate Action" and strategy_upgrade == "No Action" and strategy_resource == "Moderate Action":
            goal_strategy = "upgrading"
        elif strategy_attack == "Moderate Action" and strategy_upgrade == "Moderate Action" and strategy_resource == "Moderate Action":
            goal_strategy = "upgrading"
        #resources
        elif strategy_attack == "No Action" and strategy_upgrade == "No Action" and strategy_resource == "Aggressive Action":
            goal_strategy = "resources"
        elif strategy_attack == "No Action" and strategy_upgrade == "No Action" and strategy_resource == "Moderate Action":
            goal_strategy = "resources"
        elif strategy_attack == "No Action" and strategy_upgrade == "Moderate Action" and strategy_resource == "Moderate Action":
            goal_strategy = "resources"
        elif strategy_attack == "No Action" and strategy_upgrade == "Moderate Action" and strategy_resource == "Aggressive Action":
            goal_strategy = "resources"
        elif strategy_attack == "Moderate Action" and strategy_upgrade == "No Action" and strategy_resource == "Aggressive Action":
            goal_strategy = "resources"
        
        return goal_strategy
