from __future__ import annotations
from typing import TYPE_CHECKING, Optional
from config import USE_NAVIGATION, USE_RESOURCE_MANAGER

if TYPE_CHECKING:
    from modules.py_unit import PyUnit
    from agents.basic_agent import BasicAgent

from tasks.task import Task, Status


class GatherGas(Task):
    """Task for gathering gas."""

    def __init__(self, refinery: PyUnit, prio: int, agent: BasicAgent):
        super().__init__(prio=prio, candidates=agent.WORKER_TYPES)
        self.target: Optional[PyUnit] = refinery
        if USE_NAVIGATION:
            self.nav = agent.nav

        if USE_RESOURCE_MANAGER:
            self.assigned_worker_id = None    
        
    if USE_RESOURCE_MANAGER:
        def set_assigned_worker(self, worker: PyUnit):
            self.assigned_worker_id = worker.id


    def on_start(self, py_unit: PyUnit) -> Status:
        """
        Start or restart the task.

        :return: Status.DONE when the task was started.
        """
        if USE_RESOURCE_MANAGER:
            if self.assigned_worker_id is not None and py_unit.id != self.assigned_worker_id:
                return Status.FAIL

        if USE_NAVIGATION:
            self.nav.move(self.target.position,self.target.id)
            py_unit.target_gas = self.target.unit
        else:
            py_unit.right_click(self.target.unit)
        return Status.DONE

    def on_step(self, py_unit: PyUnit) -> Status:
        """
        Checks if the task is continuing.

        :return: Status.FAIL if the unit is idle, Status.NOT_DONE if the unit is alive and there are gas left
        in the refinery. Returns Status.DONE if unit is dead or the refinery is out of gas.
        """
        if USE_NAVIGATION and not self.nav.is_at_pos(py_unit.id) and py_unit.target_gas is not None:
            py_unit.right_click(py_unit.target_gas)
            py_unit.target_gas = None
            return Status.NOT_DONE
        if py_unit.is_idle:
            return Status.FAIL
        # It there still a refinery and does it have gas left in the geyser?
        if self.target.is_alive and self.target.gas_left_in_refinery:
            return Status.NOT_DONE
        else:
            return Status.DONE
