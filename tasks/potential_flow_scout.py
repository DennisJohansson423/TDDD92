from __future__ import annotations
from typing import TYPE_CHECKING, Optional
from config import USE_NAVIGATION

if TYPE_CHECKING:
    from modules.py_unit import PyUnit
    from agents.basic_agent import BasicAgent

from commandcenter import UnitType, Point2D
from tasks.task import Task, Status
from queue import SimpleQueue
from modules.potential_flow import PotentialFlowGenerator
import math


class PotentialFlowScout(Task):
    """Task for scouting a list of bases."""

    def __init__(self, scout_bases: SimpleQueue[Point2D], prio: int, agent: BasicAgent):
        super().__init__(prio=prio, candidates=agent.WORKER_TYPES, agent=agent, restart_on_fail=False)
        self.unit_type: Optional[UnitType] = None
        self.scout_bases: SimpleQueue[Point2D] = scout_bases
        self.scout_target: Optional[Point2D] = None
        self.fails: int = 0
        self.previous_pos: Optional[Point2D] = None
        self.epsilon = 1e-6
        if USE_NAVIGATION:
            self.nav = agent.nav

    def on_start(self, py_unit: PyUnit) -> Status:
        """
        Start or restart the task.

        :return: Status.DONE if there is a list of targets and the task has been given to at suitable unit.
        Status.FAIL if unit not suitable.
        """

        self.unit_type = py_unit.unit_type.unit_typeid

        if self.scout_target:
            py_unit.move(self.scout_target)
            return Status.DONE
        # Sets first target, then removes it from list
        self.scout_target = self.scout_bases.get()

        self.flow_generator = PotentialFlowGenerator(
            agent=self.agent,
            target=self.scout_target,
            unit=py_unit.unit
        )
        # From start only support for worker scouting.
        if self.unit_type in self.candidates:
            py_unit.move(self.scout_target)
        # Features for other units could be added.
        else:
            return Status.FAIL
        
        return Status.DONE

    def on_step(self, py_unit: PyUnit) -> Status:
        """
        Checks if the task is continuing.

        :return: Status.DONE if unit is finished scouting. Status.NOT_DONE if it keeps scouting.
        Status.FAIL if unit is idle.
        """

        FLOW_ACTIVATION_DISTANCE = 15  # Set your desired activation distance

        # Check if unit is dead
        if not py_unit.is_alive:
            #print("unit is dead")
            return Status.DONE

        if not self.scout_target:
            if self.scout_bases.empty():
                return Status.DONE
            else:
                self.scout_target = self.scout_bases.get()

        # Check distance to the scout_target
        distance_to_target = py_unit.position.distance_to(self.scout_target)
        enemy_units = self.flow_generator.get_enemy_combat_units()

        # Are we near the coordinate yet? Just close enough. < distance 5 arbitrarily chosen.
        if distance_to_target < 4:
            return self.switch_target(py_unit)
        
        elif distance_to_target <= FLOW_ACTIVATION_DISTANCE or (enemy_units and min(py_unit.position.distance_to(unit.position) for unit in enemy_units) < 20):
            if USE_NAVIGATION: # BUG när belmins är avstängd
                self.nav.remove_units(py_unit.id)
            # Apply potential flow
            velocity = self.flow_generator.get_velocity(position=py_unit.position)
            magnitude = math.sqrt(velocity.real**2 + velocity.imag**2)

            if magnitude != 0:  # Avoid division by zero
                dir_x = velocity.real / magnitude
                dir_y = velocity.imag / magnitude

                # Step 6: Move the scout considering its movement speed
                step_size = py_unit.unit_type.movement_speed  # use the unit's movement speed
                new_x = py_unit.position.x + dir_x * step_size
                new_y = py_unit.position.y + dir_y * step_size
                new_point = Point2D(new_x, new_y)

                py_unit.move(new_point)
            else:
                pass
        else:
            # If outside activation distance, move directly toward the target
            if USE_NAVIGATION:
                self.nav.move(self.scout_target,py_unit.id)
            else:
                py_unit.move(self.scout_target)


        

        return Status.NOT_DONE

    def on_fail(self, py_unit, status):
        if USE_NAVIGATION:
            self.nav.remove_units(py_unit.id)
        return super().on_fail(py_unit, status)


    def switch_target(self, py_unit: PyUnit) -> Status:
        """Switch the task target to the next base in the queue"""
        #print("Switching target")
        if self.scout_bases.empty():
            # No more coordinates in list to scout.
            return Status.DONE
        else:
            # Switching target to next coordinates in list to scout.
            self.scout_target = self.scout_bases.get()
            self.flow_generator.update_target(self.scout_target)
            py_unit.move(self.scout_target)
            return Status.NOT_DONE
