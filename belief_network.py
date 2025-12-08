from pgmpy.models import BayesianNetwork
from pgmpy.factors.discrete import TabularCPD
from pgmpy.inference import BeliefPropagation, BeliefPropagation
import commandcenter as pycc

import itertools

class BayesianNetworkModel:
    def __init__(self, agent):
        self.agent = agent
        self.internal_gas = 0
        self.internal_minerals = 0
        self.internal_supply = 0
        self.killed_enemy_units = 0
        self.killed_enemy_structures = 0
        self.lost_units = 0
        self.lost_structures = 0

        self.enemy_expansions_scouted = False
        self.enemy_gas_structures_scouted = False
        self.recent_engagements = False
        # Now we include 'Game Time' as a parent to the statuses and eventually to Win Probability.
        self.model = BayesianNetwork([

            ('Game Time', 'Combat Status'),
            ('Game Time', 'Upgrade Status'),
            ('Game Time', 'Resource Status'),

            ('Killed Structures', 'Combat Status'),
            ('Killed Units', 'Combat Status'),
            ('Army Count', 'Combat Status'),
            ('Combat Strategy', 'Combat Status'),

            ('Infantry weapons Level', 'Upgrade Status'),
            ('Qualitative Upgrades', 'Upgrade Status'),
            ('Numerical Upgrades', 'Upgrade Status'),
            ('Upgrade Strategy', 'Upgrade Status'),

            ('Structure Count', 'Resource Status'),
            ('Vespene', 'Resource Status'),
            ('Minerals', 'Resource Status'),
            ('Worker Count', 'Resource Status'),
            ('Resource Strategy', 'Resource Status'),

            ('Combat Status', 'Win Probability'),
            ('Upgrade Status', 'Win Probability'),
            ('Resource Status', 'Win Probability')
        ])

        # 'Game Time' node
        self.cpd_game_time = TabularCPD(
            variable='Game Time',
            variable_card=3,
            values=[[1/3], [1/3], [1/3]],
            state_names={'Game Time': ['early', 'mid', 'late']}
        )

        #Variables for statuses
        game_time_states = ['early', 'mid', 'late']


        killed_structures = ['fewer', 'equal', 'more']
        killed_units = ['fewer', 'equal', 'more']
        army_count = ['fewer', 'equal', 'more']
        combat_strategy_states = ['No Action', 'Moderate Action', 'Aggressive Action']
        

        infantry_weapons_level = ['fewer', 'equal', 'more']
        qualitative_upgrades = ['fewer', 'equal', 'more']
        numerical_upgrades = ['fewer', 'equal', 'more']
        upgrade_strategy_states = ['No Action', 'Moderate Action', 'Aggressive Action']


        structure_count_states = ['fewer', 'equal', 'more']
        vespene_states = ['fewer', 'equal', 'more']
        minerals_states = ['fewer', 'equal', 'more']
        worker_count_states = ['fewer', 'equal', 'more']
        resource_strategy_states = ['No Action', 'Moderate Action', 'Aggressive Action']

    
      

        def get_status_distribution(parents):
            parents_set = set(parents)
            # parents could look like ('fewer', 'fewer', 'fewer', 'No Action', 'early')
            
            p_low = 0
            p_medium = 0
            p_high = 0

            if 'Aggressive Action' in parents_set:
                p_medium += 500
                p_high += 2500

            elif 'Moderate Action' in parents_set:
                p_medium += 500

            if 'No Action' in parents_set:
                p_low += 500

            if 'fewer' in parents_set:
                p_low += 900
                p_medium += 300

            if 'equal' in parents_set:
                p_medium += 900

            if 'more' in parents_set:
                p_high += 900

            if 'early' in parents_set:
                p_low += 900

            if 'mid' in parents_set:
                p_medium += 900

            if 'late' in parents_set:
                p_high += 900       
        
            total = p_low + p_medium + p_high
            p_low /= total
            p_medium /= total
            p_high /= total

            return [p_low, p_medium, p_high]


        combat_status_combinations = list(itertools.product(
            killed_structures,
            killed_units,
            army_count,
            combat_strategy_states,
            game_time_states
        ))
        

        combat_low_values = []
        combat_medium_values = []
        combat_high_values = []

        for combo in combat_status_combinations:
            p = get_status_distribution(combo)
            combat_low_values.append(p[0])
            combat_medium_values.append(p[1])
            combat_high_values.append(p[2])

        self.cpd_combat_status = TabularCPD(
            variable='Combat Status',
            variable_card=3,
            #values blir listor
            values=[
                combat_low_values, combat_medium_values, combat_high_values
            ],
            evidence=['Killed Structures', 'Killed Units', 'Army Count', 'Combat Strategy', 'Game Time'],
            evidence_card=[3, 3, 3, 3, 3],
            state_names={
                'Combat Status': ['low', 'medium', 'high'],
                'Killed Structures': ['fewer', 'equal', 'more'],
                'Killed Units': ['fewer', 'equal', 'more'],
                'Army Count': ['fewer', 'equal', 'more'],
                'Combat Strategy': ['No Action', 'Moderate Action', 'Aggressive Action'],
                'Game Time': ['early', 'mid', 'late']
            }
        )


        upgrade_status_combinations = list(itertools.product(
            infantry_weapons_level,
            qualitative_upgrades,
            numerical_upgrades,
            upgrade_strategy_states,
            game_time_states
        ))
 

        upgrade_low_values = []
        upgrade_medium_values = []
        upgrade_high_values = []

        for combo in upgrade_status_combinations:
            p = get_status_distribution(combo)
            upgrade_low_values.append(p[0])
            upgrade_medium_values.append(p[1])
            upgrade_high_values.append(p[2])


        self.cpd_upgrade_status = TabularCPD(
            variable='Upgrade Status',
            variable_card=3,
            values=[
                upgrade_low_values, upgrade_medium_values, upgrade_high_values
            ],
            evidence=['Infantry weapons Level', 'Qualitative Upgrades', 'Numerical Upgrades', 'Upgrade Strategy', 'Game Time'],
            evidence_card=[3, 3, 3, 3, 3],
            state_names={
                'Upgrade Status': ['low', 'medium', 'high'],
                'Infantry weapons Level': ['fewer', 'equal', 'more'],
                'Qualitative Upgrades': ['fewer', 'equal', 'more'],
                'Numerical Upgrades': ['fewer', 'equal', 'more'],
                'Upgrade Strategy': ['No Action', 'Moderate Action', 'Aggressive Action'],
                'Game Time': ['early', 'mid', 'late']
            }
        )



        resource_status_combinations = list(itertools.product(
            structure_count_states,
            vespene_states,
            minerals_states,
            worker_count_states,
            resource_strategy_states,
            game_time_states
        ))

        resource_low_values = []
        resource_medium_values = []
        resource_high_values = []

        for combo in resource_status_combinations:
            p = get_status_distribution(combo)
            resource_low_values.append(p[0])
            resource_medium_values.append(p[1])
            resource_high_values.append(p[2])


        self.cpd_resource_status = TabularCPD(
            variable='Resource Status',
            variable_card=3,
            values=[
                resource_low_values, resource_medium_values, resource_high_values
            ],
            evidence=['Structure Count', 'Vespene', 'Minerals', 'Worker Count', 'Resource Strategy', 'Game Time'],
            evidence_card=[3, 3, 3, 3, 3, 3],
            state_names={
                'Resource Status': ['low', 'medium', 'high'],
                'Structure Count': ['fewer', 'equal', 'more'],
                'Vespene': ['fewer', 'equal', 'more'],
                'Minerals': ['fewer', 'equal', 'more'],
                'Worker Count': ['fewer', 'equal', 'more'],
                'Resource Strategy': ['No Action', 'Moderate Action', 'Aggressive Action'],
                'Game Time': ['early', 'mid', 'late']
            }
        )



        def get_win_probability(combat_status, upgrade_status, resource_status):
            base_win_prob = 50
            base_lose_prob = 50

            if combat_status == 'high':
                base_win_prob += 1200
            elif combat_status == 'medium':
                base_lose_prob +=0
            elif combat_status == 'low':
                base_lose_prob += 1200

            if upgrade_status == 'high':
                base_win_prob += 800
            elif upgrade_status == 'medium':
                base_lose_prob +=0
            elif upgrade_status == 'low':
                base_lose_prob += 800

            if resource_status == 'high':
                base_win_prob += 800
            elif resource_status == 'medium':
                base_lose_prob +=0    
            elif resource_status == 'low':
                base_lose_prob += 800

            total = base_win_prob + base_lose_prob
            base_win_prob /= total
            base_lose_prob /= total
            
            return [base_win_prob, base_lose_prob]



        win_status_combinations = list(itertools.product(
            ['low', 'medium', 'high'],
            ['low', 'medium', 'high'],
            ['low', 'medium', 'high']
        ))

        win_values = []
        lose_values = []
        

        for combo in win_status_combinations:
            combat_status, upgrade_status, resource_status = combo
            prob = get_win_probability(combat_status, upgrade_status, resource_status)
            win_values.append(prob[0])
            lose_values.append(prob[1])

        
        
        self.cpd_win_probability = TabularCPD(
            variable='Win Probability',
            variable_card=2,
            values=[
                win_values, lose_values
            ],
            evidence=['Combat Status', 'Upgrade Status', 'Resource Status'],
            evidence_card=[3, 3, 3],
            state_names={
                'Win Probability': ['win', 'lose'], 
                'Combat Status': ['low', 'medium', 'high'],
                'Upgrade Status': ['low', 'medium', 'high'],
                'Resource Status': ['low', 'medium', 'high']
            }
        )




        
        # Uniform priors for parent nodes remain the same
        state_values = ['fewer', 'equal', 'more']
        self.cpd_structure_count = TabularCPD('Structure Count', 3, [[1/3], [1/3], [1/3]], state_names={'Structure Count': state_values})
        self.cpd_killed_structures = TabularCPD('Killed Structures', 3, [[1/3], [1/3], [1/3]], state_names={'Killed Structures': state_values})
        self.cpd_army_count = TabularCPD('Army Count', 3, [[1/3], [1/3], [1/3]], state_names={'Army Count': state_values})
        self.cpd_killed_units = TabularCPD('Killed Units', 3, [[1/3], [1/3], [1/3]], state_names={'Killed Units': state_values})
        self.cpd_infantry_weapons_level = TabularCPD('Infantry weapons Level', 3, [[1/3], [1/3], [1/3]], state_names={'Infantry weapons Level': state_values})
        self.cpd_qualitative_upgrades = TabularCPD('Qualitative Upgrades', 3, [[1/3], [1/3], [1/3]], state_names={'Qualitative Upgrades': state_values})
        self.cpd_numerical_upgrades = TabularCPD('Numerical Upgrades', 3, [[1/3], [1/3], [1/3]], state_names={'Numerical Upgrades': state_values})
        self.cpd_vespene = TabularCPD('Vespene', 3, [[1/3], [1/3], [1/3]], state_names={'Vespene': state_values})
        self.cpd_minerals = TabularCPD('Minerals', 3, [[1/3], [1/3], [1/3]], state_names={'Minerals': state_values})
        self.cpd_worker_count = TabularCPD('Worker Count', 3, [[1/3], [1/3], [1/3]], state_names={'Worker Count': state_values})

        strategy_states_list = ['No Action', 'Moderate Action', 'Aggressive Action']
        self.cpd_combat_strategy = TabularCPD('Combat Strategy', 3, [[1/3], [1/3], [1/3]], state_names={'Combat Strategy': strategy_states_list})
        self.cpd_upgrade_strategy = TabularCPD('Upgrade Strategy', 3, [[1/3], [1/3], [1/3]], state_names={'Upgrade Strategy': strategy_states_list})
        self.cpd_resource_strategy = TabularCPD('Resource Strategy', 3, [[1/3], [1/3], [1/3]], state_names={'Resource Strategy': strategy_states_list})

    
        self.model.add_cpds(
            self.cpd_game_time,
            self.cpd_combat_status,
            self.cpd_killed_structures,
            self.cpd_army_count, 
            self.cpd_killed_units,
            self.cpd_upgrade_status, 
            self.cpd_infantry_weapons_level, 
            self.cpd_qualitative_upgrades, 
            self.cpd_numerical_upgrades,
            self.cpd_resource_status, 
            self.cpd_structure_count, 
            self.cpd_vespene, 
            self.cpd_minerals, 
            self.cpd_worker_count,
            self.cpd_combat_strategy, 
            self.cpd_upgrade_strategy, 
            self.cpd_resource_strategy,
            self.cpd_win_probability
        )

        assert self.model.check_model(), "The model is incorrect"

        self.infer = BeliefPropagation(self.model)

    

    def calculate_action_cost(self, combination):
        action_costs = {
            'No Action': 0,
            'Moderate Action': 1,
            'Aggressive Action': 2
        }
        return sum(action_costs[action] for action in combination)


    def estimate_best_strategy(self, evidence):
        best_strategy_combination = None

        query_result = self.infer.query(variables=['Combat Strategy', 'Upgrade Strategy', 'Resource Strategy'], evidence=evidence)
    
        values = query_result.values.flatten()  # Flatten in case it's multidimensional 0.039033231809385734
        states = query_result.state_names

        state_combinations = [states[var] for var in query_result.variables]
        combinations = list(itertools.product(*state_combinations))
        results = list(zip(combinations, values))
        sorted_results = sorted(results, key=lambda x: x[1], reverse=True)
        

        for combo, prob in sorted_results:
            if self.calculate_action_cost(combo) <= 3:
                best_strategy_combination = combo
                break
        
        return best_strategy_combination
    


    def on_unit_destroyed(self, unit):
        """Tracks units and structures destroyed."""
        if unit.owner == pycc.PLAYER_SELF:
            if 'Structure' in unit.unit_type_data.attributes:
                self.lost_structures += 1
            else:
                self.lost_units += 1
        elif unit.owner == pycc.PLAYER_ENEMY:
            if 'Structure' in unit.unit_type_data.attributes:
                self.killed_enemy_structures += 1
            else:
                self.killed_enemy_units += 1


    def get_my_units(self):
        """Returns all units owned by the agent."""
        return self.agent.unit_collection.get_group(pycc.PLAYER_SELF)

    def get_structure_count(self):
        """Returns the number of structures the agent owns."""
        my_units = self.get_my_units()
        structure_units = [unit for unit in my_units if unit.unit_type.is_building]
        return len(structure_units)

    def get_killed_structures(self):
        """Returns the number of enemy structures destroyed."""
        return self.killed_enemy_structures

    def estimate_enemy_units_killed(self):
        """Estimates the number of enemy units killed (which is our lost units)."""
        return self.lost_units

    def estimate_enemy_killed_structures(self):
        """Estimates the number of enemy structures killed (which is our lost structures)."""
        return self.lost_structures

    def get_army_count(self):
        """Returns the number of army units (excluding workers and structures) the agent has."""
        my_units = self.get_my_units()
        army_units = [unit for unit in my_units if not unit.unit_type.is_worker and not unit.unit_type.is_building]
        return len(army_units)

    def get_units_killed(self):
        """Returns the number of enemy units killed."""
        return self.killed_enemy_units

    def get_worker_count(self):
        """Returns the number of worker units the agent owns."""
        my_units = self.get_my_units()
        worker_units = [unit for unit in my_units if unit.unit_type.is_worker]
        return len(worker_units)

    def get_infantry_weapon_level(self):
        """Returns the infantry weapons upgrade level for the agent."""
        upgrades = self.agent.UPGRADES
        if pycc.UPGRADE_ID.TERRANINFANTRYWEAPONSLEVEL3 in upgrades:
            return 3
        elif pycc.UPGRADE_ID.TERRANINFANTRYWEAPONSLEVEL2 in upgrades:
            return 2
        elif pycc.UPGRADE_ID.TERRANINFANTRYWEAPONSLEVEL1 in upgrades:
            return 1
        else:
            return 0

    def get_qualitative_upgrades(self):
        """Returns the number of qualitative upgrades the agent has."""
        upgrades = self.agent.UPGRADES
        count = 0
        qualitative_upgrades = [
            pycc.UPGRADE_ID.STIMPACK,                  
            pycc.UPGRADE_ID.SHIELDWALL,              
            pycc.UPGRADE_ID.PUNISHERGRENADES,         
            pycc.UPGRADE_ID.PERSONALCLOAKING,        
            pycc.UPGRADE_ID.BANSHEECLOAK,             
            pycc.UPGRADE_ID.BANSHEESPEED,            
            pycc.UPGRADE_ID.TERRANBUILDINGARMOR,      
            pycc.UPGRADE_ID.DRILLCLAWS,              
            pycc.UPGRADE_ID.INFERNALPREIGNITERS,      
        ]
        for upgrade in qualitative_upgrades:
            if upgrade in upgrades:
                count += 1
        return count

    def get_numerical_upgrades(self):
        """Returns the total level of numerical upgrades the agent has."""
        upgrades = self.agent.UPGRADES
        level = 0
        numerical_upgrades = [
            pycc.UPGRADE_ID.TERRANINFANTRYWEAPONSLEVEL1,
            pycc.UPGRADE_ID.TERRANINFANTRYWEAPONSLEVEL2,
            pycc.UPGRADE_ID.TERRANINFANTRYWEAPONSLEVEL3,
            pycc.UPGRADE_ID.TERRANINFANTRYARMORSLEVEL1,
            pycc.UPGRADE_ID.TERRANINFANTRYARMORSLEVEL2,
            pycc.UPGRADE_ID.TERRANINFANTRYARMORSLEVEL3,
        ]
        for upgrade in numerical_upgrades:
            if upgrade in upgrades:
                level += 1
        return level

    def get_game_time(self):
        """Returns the current game time in minutes."""
        return self.agent.current_frame / (22.4 * 60) 

    def get_game_stage(self):
        """Determines the current stage of the game."""
        game_time = self.get_game_time()  # In minutes
        if game_time < 1:
            return 'early'
        elif 1 <= game_time < 2:
            return 'mid'
        else:
            return 'late'

    def collect_evidence(self):
        """Collects the necessary evidence from the game state."""
        # Agent's own state
        agent_minerals = self.agent.internal_minerals
        agent_vespene = self.agent.internal_gas
        agent_worker_count = self.get_worker_count()
        agent_infantry_weapon_level = self.get_infantry_weapon_level()
        agent_qualitative_upgrades = self.get_qualitative_upgrades()
        agent_numerical_upgrades = self.get_numerical_upgrades()
        agent_structure_count = self.get_structure_count()
        agent_killed_structures = self.get_killed_structures()
        agent_army_count = self.get_army_count()
        agent_units_killed = self.get_units_killed()

        # Estimate enemy state
        estimated_enemy_state = self.estimate_enemy_state()

        
        enemy_worker_count_estimate = estimated_enemy_state['Enemy Worker Count']
        enemy_structure_count = estimated_enemy_state['Enemy Structure Count']
        enemy_minerals_estimate = estimated_enemy_state['Enemy Minerals']
        enemy_vespene_estimate = estimated_enemy_state['Enemy Vespene']
        enemy_army_count = estimated_enemy_state['Enemy Army Count']


        enemy_infantry_weapon_level_estimate = self.get_enemy_infantry_weapon_level()
        enemy_qualitative_upgrades_estimate = self.get_enemy_qualitative_upgrades()
        enemy_numerical_upgrades_estimate = self.get_enemy_numerical_upgrades()

        # Enemy units killed and structures destroyed (estimated as our losses)
        enemy_killed_structures = self.estimate_enemy_killed_structures()
        enemy_units_killed = self.estimate_enemy_units_killed()

        evidence = {
            'Structure Count': self.determine_variable(agent_structure_count, enemy_structure_count),
            'Killed Structures': self.determine_variable(agent_killed_structures, enemy_killed_structures),
            'Army Count': self.determine_variable(agent_army_count, enemy_army_count),
            'Killed Units': self.determine_variable(agent_units_killed, enemy_units_killed),
            'Infantry weapons Level': self.determine_variable(agent_infantry_weapon_level, enemy_infantry_weapon_level_estimate),
            'Qualitative Upgrades': self.determine_variable(agent_qualitative_upgrades, enemy_qualitative_upgrades_estimate),
            'Numerical Upgrades': self.determine_variable(agent_numerical_upgrades, enemy_numerical_upgrades_estimate),
            'Vespene': self.determine_variable(agent_vespene, enemy_vespene_estimate),
            'Minerals': self.determine_variable(agent_minerals, enemy_minerals_estimate),
            'Worker Count': self.determine_variable(agent_worker_count, enemy_worker_count_estimate),

            'Win Probability' : 'win'
        }

        return evidence

    def determine_variable(self, agent_value, enemy_value):
        if agent_value < enemy_value:
            return 'fewer'
        elif agent_value == enemy_value:
            return 'equal'
        else:
            return 'more'

    def estimate_enemy_state(self):
        """Estimates the enemy's state using the EnemyStateEstimator."""
        game_time_stage = self.get_game_stage()
        enemy_expansions_observed = self.have_observed_enemy_expansions()

        estimated_enemy_state = self.agent.enemy_state_estimator.estimate_enemy_state(
            game_time_stage,
            enemy_expansions_observed,
        )

        enemy_worker_count_mapping = {'low': 12, 'medium': 24, 'high': 30}
        enemy_structure_count_mapping = {'low': 5, 'medium': 15, 'high': 30}
        enemy_minerals_mapping = {'low': 1000, 'medium': 2000, 'high': 3000}
        enemy_vespene_mapping = {'low': 1000, 'medium': 2000, 'high': 3000}
        enemy_army_count_mapping = {'low': 5, 'medium': 25, 'high': 40}

        estimated_enemy_state_numeric = {
            'Enemy Worker Count': enemy_worker_count_mapping[estimated_enemy_state['Enemy Worker Count']],
            'Enemy Structure Count': enemy_structure_count_mapping[estimated_enemy_state['Enemy Structure Count']],
            'Enemy Minerals': enemy_minerals_mapping[estimated_enemy_state['Enemy Minerals']],
            'Enemy Vespene': enemy_vespene_mapping[estimated_enemy_state['Enemy Vespene']],
            'Enemy Army Count': enemy_army_count_mapping[estimated_enemy_state['Enemy Army Count']]
        }

        return estimated_enemy_state_numeric
    



    ###scout

    def have_observed_enemy_expansions(self):
        """Returns 'yes' if the agent has scouted enemy expansions, 'no' otherwise."""
        return 'no'


    def get_enemy_infantry_weapon_level(self):
        return 0

    def get_enemy_qualitative_upgrades(self):
        return 0

    def get_enemy_numerical_upgrades(self):
        return 0



class EnemyStateEstimator:
    def __init__(self):
        self.model = BayesianNetwork([
            ('Game Time', 'Enemy Worker Count'),
            ('Game Time', 'Enemy Structure Count'),
            ('Game Time', 'Enemy Army Count'),
            ('Game Time', 'Enemy Minerals'),
            ('Game Time', 'Enemy Vespene'),

            ('Enemy Expansions Observed', 'Enemy Worker Count'),
            ('Enemy Expansions Observed', 'Enemy Structure Count'),
            ('Enemy Expansions Observed', 'Enemy Minerals'),
            ('Enemy Expansions Observed', 'Enemy Vespene'),

            ('Enemy Worker Count', 'Enemy Minerals'),
            ('Enemy Worker Count', 'Enemy Vespene'),
            
            ('Enemy Minerals', 'Enemy Army Count'),
            ('Enemy Vespene', 'Enemy Army Count'),
        ])


        game_time_states = ['early', 'mid', 'late']
        enemy_expansions_observed_states = ['no', 'yes']

        enemy_worker_count_states = ['low', 'medium', 'high']
        enemy_structure_count_states = ['low', 'medium', 'high']
        enemy_minerals_states = ['low', 'medium', 'high']
        enemy_vespene_states = ['low', 'medium', 'high']



        def get_status_distribution(parents):
            parents_set = set(parents)
            
            p_low = 100
            p_medium = 100
            p_high = 100

            if 'high' in parents_set:
                p_medium += 500
                p_high += 2500

            if 'medium' in parents_set:
                p_medium += 1000

            if 'low' in parents_set:
                p_low += 2500
                p_medium += 500

            if 'yes' in parents_set:
                p_medium += 300
                p_high += 1000

            if 'no' in parents_set:
                p_low += 1000
                p_medium += 300

            if 'early' in parents_set:
                p_low += 1500
                p_medium += 900

            if 'mid' in parents_set:
                p_medium += 300
                p_medium += 900
                p_high += 300 

            if 'late' in parents_set:
                p_medium += 900
                p_high += 1500   

            total = p_low + p_medium + p_high
            p_low /= total
            p_medium /= total
            p_high /= total

            return [p_low, p_medium, p_high]


        # 'Game Time' node
        self.cpd_game_time = TabularCPD(
            variable='Game Time',
            variable_card=3,
            values=[[1/3], [1/3], [1/3]],
            state_names={'Game Time': ['early', 'mid', 'late']}
        )

        # 'Enemy Expansions Observed' node
        self.cpd_enemy_expansions_observed = TabularCPD(
            variable='Enemy Expansions Observed',
            variable_card=2,
            values=[[0.5], [0.5]],
            state_names={'Enemy Expansions Observed': ['no', 'yes']}
        )


        enemy_worker_combinations = list(itertools.product(
                game_time_states,
                enemy_expansions_observed_states
        ))


        enemy_worker_low_values = []
        enemy_worker_medium_values = []
        enemy_worker_high_values = []

        for combo in enemy_worker_combinations:
            p = get_status_distribution(combo)
            enemy_worker_low_values.append(p[0])
            enemy_worker_medium_values.append(p[1])
            enemy_worker_high_values.append(p[2])



        # 'Enemy Worker Count' CPD
        self.cpd_enemy_worker_count = TabularCPD(
            variable='Enemy Worker Count',
            variable_card=3,
            values=[
                enemy_worker_low_values, enemy_worker_medium_values, enemy_worker_high_values
            ],
            evidence=['Game Time', 'Enemy Expansions Observed'],
            evidence_card=[3, 2],
            state_names={
                'Enemy Worker Count': ['low', 'medium', 'high'],
                'Game Time': ['early', 'mid', 'late'],
                'Enemy Expansions Observed': ['no', 'yes']
            }
        )




        enemy_structures_combinations = list(itertools.product(
                game_time_states,
                enemy_expansions_observed_states
        ))


        enemy_structures_low_values = []
        enemy_structures_medium_values = []
        enemy_structures_high_values = []

        for combo in enemy_structures_combinations:
            p = get_status_distribution(combo)
            enemy_structures_low_values.append(p[0])
            enemy_structures_medium_values.append(p[1])
            enemy_structures_high_values.append(p[2])



        # 'Enemy Structure Count' CPD
        self.cpd_enemy_structure_count = TabularCPD(
            variable='Enemy Structure Count',
            variable_card=3,
            values=[
                enemy_structures_low_values, enemy_structures_medium_values, enemy_structures_high_values
            ],
            evidence=['Game Time', 'Enemy Expansions Observed'],
            evidence_card=[3, 2],
            state_names={
                'Enemy Structure Count': ['low', 'medium', 'high'],
                'Game Time': ['early', 'mid', 'late'],
                'Enemy Expansions Observed': ['no', 'yes']
            }
        )



        enemy_minerals_combinations = list(itertools.product(
                game_time_states,
                enemy_worker_count_states,
                enemy_expansions_observed_states
        ))


        enemy_minerals_low_values = []
        enemy_minerals_medium_values = []
        enemy_minerals_high_values = []

        for combo in enemy_minerals_combinations:
            p = get_status_distribution(combo)
            enemy_minerals_low_values.append(p[0])
            enemy_minerals_medium_values.append(p[1])
            enemy_minerals_high_values.append(p[2])



        # 'Enemy Minerals' CPD
        self.cpd_enemy_minerals = TabularCPD(
            variable='Enemy Minerals',
            variable_card=3,
            values=[
                enemy_minerals_low_values, enemy_minerals_medium_values, enemy_minerals_high_values
            ],
            evidence=['Game Time', 'Enemy Worker Count', 'Enemy Expansions Observed'],
            evidence_card=[3, 3, 2],
            state_names={
                'Enemy Minerals': ['low', 'medium', 'high'],
                'Game Time': ['early', 'mid', 'late'],
                'Enemy Worker Count': ['low', 'medium', 'high'],
                'Enemy Expansions Observed': ['no', 'yes']
            }
        )



        enemy_vespene_combinations = list(itertools.product(
                game_time_states,
                enemy_worker_count_states,
                enemy_expansions_observed_states
        ))


        enemy_vespene_low_values = []
        enemy_vespene_medium_values = []
        enemy_vespene_high_values = []

        for combo in enemy_vespene_combinations:
            p = get_status_distribution(combo)
            enemy_vespene_low_values.append(p[0])
            enemy_vespene_medium_values.append(p[1])
            enemy_vespene_high_values.append(p[2])



        # 'Enemy Vespene' CPD
        self.cpd_enemy_vespene = TabularCPD(
            variable='Enemy Vespene',
            variable_card=3,
            values=[
               enemy_vespene_low_values, enemy_vespene_medium_values, enemy_vespene_high_values
            ],
            evidence=['Game Time', 'Enemy Worker Count', 'Enemy Expansions Observed'],
            evidence_card=[3, 3, 2],
            state_names={
                'Enemy Vespene': ['low', 'medium', 'high'],
                'Game Time': ['early', 'mid', 'late'],
                'Enemy Worker Count': ['low', 'medium', 'high'],
                'Enemy Expansions Observed': ['no', 'yes']
            }
        )



        enemy_army_count_combinations = list(itertools.product(
                game_time_states,
                enemy_minerals_states,
                enemy_vespene_states
        ))


        enemy_army_count_low_values = []
        enemy_army_count_medium_values = []
        enemy_army_count_high_values = []

        for combo in enemy_army_count_combinations:
            p = get_status_distribution(combo)
            enemy_army_count_low_values.append(p[0])
            enemy_army_count_medium_values.append(p[1])
            enemy_army_count_high_values.append(p[2])



        self.cpd_enemy_army_count = TabularCPD(
            variable='Enemy Army Count',
            variable_card=3, 
            values=
            [
                enemy_army_count_low_values, enemy_army_count_medium_values, enemy_army_count_high_values
            ],
            evidence=['Game Time', 'Enemy Minerals', 'Enemy Vespene'],
            evidence_card=[3, 3, 3],
            state_names={
                'Enemy Army Count': ['low', 'medium', 'high'],
                'Game Time': ['early', 'mid', 'late'],
                'Enemy Minerals': ['low', 'medium', 'high'],
                'Enemy Vespene': ['low', 'medium', 'high']
            }
        )


        self.model.add_cpds(
            self.cpd_game_time,
            self.cpd_enemy_expansions_observed,
            self.cpd_enemy_worker_count,
            self.cpd_enemy_structure_count,
            self.cpd_enemy_minerals,
            self.cpd_enemy_vespene,
            self.cpd_enemy_army_count
        )

        # Check if the model is valid
        assert self.model.check_model(), "The model is incorrect"

        # Set up inference
        self.infer = BeliefPropagation(self.model)

    def estimate_enemy_state(self, game_time, enemy_expansions_observed):
        
        evidence = {
            'Game Time': game_time,
            'Enemy Expansions Observed': enemy_expansions_observed,
        }


        enemy_worker_posterior = self.infer.query(['Enemy Worker Count'], evidence=evidence)
        enemy_structure_posterior = self.infer.query(['Enemy Structure Count'], evidence=evidence)
        enemy_minerals_posterior = self.infer.query(['Enemy Minerals'], evidence=evidence)
        enemy_vespene_posterior = self.infer.query(['Enemy Vespene'], evidence=evidence)
        enemy_army_posterior = self.infer.query(['Enemy Army Count'], evidence=evidence)


        enemy_worker_index = enemy_worker_posterior.values.argmax()
        enemy_structure_index = enemy_structure_posterior.values.argmax()
        enemy_minerals_index = enemy_minerals_posterior.values.argmax()
        enemy_vespene_index = enemy_vespene_posterior.values.argmax()
        enemy_army_index = enemy_army_posterior.values.argmax()

        states = ['low', 'medium', 'high']

        estimated_state = {
            'Enemy Worker Count': states[enemy_worker_index],
            'Enemy Structure Count': states[enemy_structure_index],
            'Enemy Minerals': states[enemy_minerals_index],
            'Enemy Vespene': states[enemy_vespene_index],
            'Enemy Army Count': states[enemy_army_index]
        }


        #print(enemy_worker_posterior.values)
        #print(enemy_structure_posterior.values)
        #print(enemy_minerals_posterior.values)
        #print(enemy_vespene_posterior.values)
        #print(enemy_army_posterior.values)
        #print(estimated_state)


        return estimated_state
