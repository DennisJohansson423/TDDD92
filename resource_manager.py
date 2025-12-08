from commandcenter import BaseLocation, PLAYER_SELF, UNIT_TYPEID, BaseLocationManager
from typing import TYPE_CHECKING, Union, Any
from tasks.gather_gas import GatherGas
from tasks.gather_minerals import GatherMinerals
from modules.py_unit import PyUnit
from modules.unit_collection import UnitCollection
from tasks.task import Task, Status
import math

if TYPE_CHECKING:
    from agents.basic_agent import BasicAgent

MAX_WORKERS_PER_REFINERY = 3
MAX_WORKERS_PER_MINERAL_PATCH = 16


def init_resource_queues(agent, base_location_manager):
    """Initialize workers and resource gathering settings."""
    agent.workers = get_all_workers(agent)
    agent.gas_enabled = False
    agent.target = BaseLocation
    agent.unit_collection = agent.unit_collection
    agent.task_manager = agent.task_manager
    agent.mineral_worker_count = {}
    agent.active_gatherers = {}

    occupied_bases = base_location_manager.get_occupied_base_locations(PLAYER_SELF)
    for base in occupied_bases:
        add_base_resources(agent, base)


def add_base_resources(agent, base):
    for mineral in base.minerals:
        agent.mineral_worker_count[mineral.id] = 0
        agent.active_gatherers[mineral.id] = []
    for geyser in base.geysers:
        agent.mineral_worker_count[geyser.id] = 0
        agent.active_gatherers[geyser.id] = []


def get_all_workers(agent):
    """Retrieve all Terran SCVs belonging to the current player."""
    return [unit for unit in agent.unit_collection.get_group(UNIT_TYPEID.TERRAN_SCV)]


def get_idle_workers(agent):
    """Retrieve all idle workers."""
    return [worker for worker in agent.workers if worker.is_idle or (worker.task and worker.task.has_failed())]


def assign_worker_to_best_task(agent, worker, base_location_manager, prioritized_resource):
    """Assign a worker to the most suitable resource gathering task."""
    best_field = None
    min_time = float('inf')
    occupied_bases = base_location_manager.get_occupied_base_locations(PLAYER_SELF)

    if not occupied_bases:
        print("No valid occupied bases found")
        return
    
    for base in occupied_bases:
        if base.minerals and base.minerals[0].id not in agent.mineral_worker_count:
            add_base_resources(agent, base)
        
    for base in occupied_bases:
        if prioritized_resource == "prio_minerals":
            prioritized_fields = base.minerals
            other_fields = base.geysers
        else:
            prioritized_fields = base.geysers
            other_fields = base.minerals
   
        resource_fields = prioritized_fields + other_fields
        for field in resource_fields:
            if not can_assign_worker_to_field(agent, field):
                continue

            travel_time = calculate_travel_time(worker, field)
            resource_type = "gas" if field.unit_type == UNIT_TYPEID.TERRAN_REFINERY else "minerals"
            total_time = travel_time + average_collection_time(resource_type)

            if total_time < min_time:
                min_time = total_time
                best_field = (base, field)

    if best_field:
        base, field = best_field
        if field.unit_type == UNIT_TYPEID.TERRAN_REFINERY:
            assign_gas_task(agent, worker, field)
        else:
            mineral_field = get_closest_mineral(agent, worker, base)
            if mineral_field:
                assign_minerals_task(agent, base, mineral_field, worker)
            else:
                print("No suitable mineral field found")
    else:
        print("No suitable resource field found for worker")


def can_assign_worker_to_field(agent, field):
    """Check if we can assign another worker to this field based on max limits."""
    field_id = field.id

    if field.unit_type == UNIT_TYPEID.TERRAN_REFINERY:
        if field_id not in agent.active_gatherers:
            agent.active_gatherers[field_id] = []
        return len(agent.active_gatherers[field_id]) < MAX_WORKERS_PER_REFINERY
    else:
        if field_id not in agent.active_gatherers:
            agent.active_gatherers[field_id] = []
        return len(agent.active_gatherers[field_id]) < MAX_WORKERS_PER_MINERAL_PATCH


def assign_gas_task(agent, worker, refinery):
    """Assign a worker to collect gas from a refinery."""
    if refinery.unit_type == UNIT_TYPEID.TERRAN_REFINERY:
        task = GatherGas(refinery=refinery, prio=10, agent=agent)
        task.set_assigned_worker(worker)
        agent.task_manager.task_queue.add(task)
    else:
        print(f"Invalid refinery type: {refinery.unit_type}")


def assign_minerals_task(agent, base, mineral_field, worker):
    """Assign a worker to mine minerals."""
    mineral_id = mineral_field.id
    if mineral_id not in agent.mineral_worker_count:
        agent.mineral_worker_count[mineral_id] = 0
    if mineral_id not in agent.active_gatherers:
        agent.active_gatherers[mineral_id] = []

    agent.mineral_worker_count[mineral_id] += 1
    agent.active_gatherers[mineral_id].append(worker)

    task = GatherMinerals(base=base, prio=10, agent=agent)
    task.set_target_mineral(mineral_field)
    task.set_assigned_worker(worker)
    agent.task_manager.task_queue.add(task)


def calculate_travel_time(worker, resource_field):
    """Calculate the travel time from the worker to the resource field."""
    worker_speed = 3.15
    worker_pos = worker.unit.position
    field_pos = resource_field.position
    distance = math.sqrt((worker_pos.x - field_pos.x)**2 + (worker_pos.y - field_pos.y)**2)
    return distance / worker_speed


def average_collection_time(resource_type):
    """Return the average collection time for the specified resource type."""
    return 5.0 if resource_type == "gas" else 3.7


def get_closest_mineral(agent, worker, base):
    """Find the closest mineral field to the given worker."""
    for mineral in base.minerals:
        if mineral.id not in agent.active_gatherers:
            agent.active_gatherers[mineral.id] = []

    available_minerals = [
            mineral for mineral in base.minerals
            if len(agent.active_gatherers[mineral.id]) < MAX_WORKERS_PER_MINERAL_PATCH
        ]

    if not available_minerals:
        closest_mineral = min(
        base.minerals,
        key=lambda mineral: calculate_travel_time(worker, mineral))
        return closest_mineral
    
    closest_mineral = min(
        available_minerals,
        key=lambda mineral: calculate_travel_time(worker, mineral)
    )
    return closest_mineral