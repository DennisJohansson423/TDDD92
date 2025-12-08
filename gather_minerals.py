from __future__ import annotations
from typing import TYPE_CHECKING
from config import USE_NAVIGATION, USE_RESOURCE_MANAGER

if TYPE_CHECKING:
    from modules.py_unit import PyUnit
    from agents.basic_agent import BasicAgent

import random
from commandcenter import BaseLocation
from tasks.task import Task, Status


class GatherMinerals(Task):
    """Task for gathering minerals."""

    def __init__(self, base: BaseLocation, prio: int, agent: BasicAgent):
        super().__init__(prio=prio, candidates=agent.WORKER_TYPES)
        self.fail_count = 0
        self.target = base
        
        if USE_RESOURCE_MANAGER:
            self.target_mineral_field = None
            self.assigned_worker_id = None

        if USE_NAVIGATION:
            self.nav = agent.nav

    if USE_RESOURCE_MANAGER:
        def set_target_mineral(self, mineral_field: PyUnit):
            self.target_mineral_field = mineral_field
        
        def set_assigned_worker(self, worker: PyUnit):
            """Store the assigned worker's ID for later verification."""
            self.assigned_worker_id = worker.id


    def on_start(self, py_unit: PyUnit) -> Status:
        """
        Start or restart the task.

        :return: Status.DONE if target are a mineral field. Otherwise Status.FAIL.
        """

        if USE_RESOURCE_MANAGER:
            if self.assigned_worker_id is not None and py_unit.id != self.assigned_worker_id:
                return Status.FAIL
        
            if self.target_mineral_field:
                if USE_NAVIGATION:
                    self.nav.move(self.target_mineral_field.position,py_unit.id)
                    py_unit.target_mineral = self.target_mineral_field
                else:
                    py_unit.right_click(self.target_mineral_field)
                    self.fail_count = 0
                return Status.DONE
            else:
                return Status.FAIL
        else:
            if self.target.minerals:
                if USE_NAVIGATION:
                    target = random.choice(self.target.minerals)
                    self.nav.move(target.position,py_unit.id)
                    py_unit.target_mineral = target
                else:
                    py_unit.right_click(random.choice(self.target.minerals))
                    self.fail_count = 0
                return Status.DONE
            else:
                return Status.FAIL

    def on_step(self, py_unit: PyUnit) -> Status:
        """
        Checks if the task is continuing.

        :return: Status.FAIL if target is not a mineral field or the unit have been idle for >10 ticks.
        Otherwise Status.NOT_DONE
        """
        if USE_NAVIGATION and not self.nav.is_at_pos(py_unit.id) and py_unit.target_mineral is not None  and USE_NAVIGATION:
            py_unit.right_click(py_unit.target_mineral)
            py_unit.target_mineral = None
            return Status.NOT_DONE
        if py_unit.is_idle:
            if USE_RESOURCE_MANAGER:
                if self.target_mineral_field:
                    py_unit.right_click(self.target_mineral_field)
                    self.fail_count += 1
                    if self.fail_count > 10:
                        return Status.FAIL
                    else:
                        return Status.NOT_DONE
                else:
                    return Status.FAIL
            else:    
                if self.target.minerals:
                    py_unit.right_click(random.choice(self.target.minerals))
                    self.fail_count += 1
                    if self.fail_count > 10:
                        return Status.FAIL
                    else:
                        return Status.NOT_DONE
                else:
                    return Status.FAIL
        self.fail_count = 0
        return Status.NOT_DONE
