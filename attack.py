from __future__ import annotations
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from modules.py_unit import PyUnit
    from agents.basic_agent import BasicAgent

from commandcenter import Point2D
from tasks.task import Task, Status

### DAVID ###
import numpy as np
from config import USE_BOIDS_POTENTIAL
if USE_BOIDS_POTENTIAL:
    from modules.potential_boids import BoidsPotential
    import commandcenter as pycc

class Attack(Task):
    """Task for attacking a position."""

    def __init__(self, pos: Point2D, prio: int, agent: BasicAgent):
        super().__init__(prio=prio, candidates=agent.COMBAT_TYPES)
        self.our_agent = agent
        self.target = pos
        self.previous_pos: Optional[Point2D] = None
        self.fails: int = 0

    def on_start(self, py_unit: PyUnit) -> Status:
        """
        Start or restart the task.

        :return: Status.DONE if the task was started, Status.FAIL if task target is not Point2D.
        """
        # Target is a coordinate
        if isinstance(self.target, Point2D):
            py_unit.attack_move(self.target)
                
        else:
            return Status.FAIL
        return Status.DONE

    def on_step(self, py_unit: PyUnit) -> Status:
        """
        Checks if the task is continuing.

        :return: Status.DONE if the unit is idle. Status.FAIL if the unit is dead. Otherwise returns Status.NOT_DONE.
        """
        ### DAVID ###
        if USE_BOIDS_POTENTIAL:
            self.potential_boids_on_step(py_unit)
            
        if py_unit.is_idle:
                return Status.DONE
            
        if not py_unit.is_alive:
            # Unit is dead
            return Status.FAIL

        return Status.NOT_DONE
        
    def potential_boids_on_step(self,py_unit: PyUnit):
        current_pos = np.array([py_unit.position.x, py_unit.position.y])
        target_pos = np.array([self.target.x, self.target.y])
        distance = np.linalg.norm(target_pos - current_pos)
        
        if distance > 30:
            py_unit.move(self.target)
            return Status.NOT_DONE
        else:
            self.our_agent.potential.get_friendly_units()
            self.our_agent.potential.get_enemy_units()
            closest_enemy = self.our_agent.potential.get_closest_enemy(py_unit)
            if closest_enemy:
                force_vector = self.our_agent.potential.combined_force(py_unit)
                new_pos = pycc.Point2D(py_unit.position.x + force_vector[0], py_unit.position.y + force_vector[1])
                py_unit.move(new_pos)
                py_unit.attack_unit(closest_enemy.unit)
            
            elif len(self.our_agent.potential.enemy_combat_units) < 1:
                py_unit.move(self.target)
    