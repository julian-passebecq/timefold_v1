from timefold.solver.score import ConstraintFactory, HardSoftScore, constraint_provider

from .domain import *

# Constraint names
VEHICLE_CAPACITY = "vehicleCapacity"
MINIMIZE_TRAVEL_TIME = "minimizeTravelTime"
SERVICE_FINISHED_AFTER_MAX_END_TIME = "serviceFinishedAfterMaxEndTime"
BALANCE_LOAD = "balanceLoad"
LIMIT_DRIVING_TIME = "limitDrivingTime"
MINIMIZE_MAX_LOAD = "minimizeMaxLoad"
ENCOURAGE_FULL_UTILIZATION = "encourageFullUtilization"
MINIMIZE_VEHICLE_COUNT = "minimizeVehicleCount"



ENABLE_TIME_WINDOW_CONSTRAINTS = True
ENABLE_LOAD_BALANCING = False
ENABLE_DRIVING_TIME_LIMIT = False
ENABLE_MINIMIZE_MAX_LOAD = False
ENABLE_ENCOURAGE_FULL_UTILIZATION = False
ENABLE_MINIMIZE_VEHICLE_COUNT = True








# Driving time limit in seconds (e.g., 3 hours = 10800 seconds)
DRIVING_TIME_LIMIT_SECONDS = 3 * 60 * 60      # Adjust as needed

# Load thresholds
MAX_LOAD_PER_VEHICLE = 15                     # Example threshold for minimizing max load
MIN_LOAD_THRESHOLD = 5                        # Example threshold for encouraging full utilization

@constraint_provider
def define_constraints(factory: ConstraintFactory):
    constraints = [
        # Hard constraints
        vehicle_capacity(factory),
    ]

    if ENABLE_TIME_WINDOW_CONSTRAINTS:
        constraints.append(service_finished_after_max_end_time(factory))

    if ENABLE_DRIVING_TIME_LIMIT:
        constraints.append(limit_driving_time(factory))

    # Soft constraints
    constraints.append(minimize_travel_time(factory))

    if ENABLE_LOAD_BALANCING:
        constraints.append(balance_load(factory))

    if ENABLE_MINIMIZE_MAX_LOAD:
        constraints.append(minimize_max_load(factory))

    if ENABLE_ENCOURAGE_FULL_UTILIZATION:
        constraints.append(encourage_full_utilization(factory))

    if ENABLE_MINIMIZE_VEHICLE_COUNT:
        constraints.append(minimize_vehicle_count(factory))

    return constraints


##############################################
# Hard constraints
##############################################

def vehicle_capacity(factory: ConstraintFactory):
    return (factory.for_each(Vehicle)
            .filter(lambda vehicle: vehicle.calculate_total_demand() > vehicle.capacity)
            .penalize(HardSoftScore.of(1, 0),  # ONE_HARD equivalent
                      lambda vehicle: vehicle.calculate_total_demand() - vehicle.capacity)
            .as_constraint(VEHICLE_CAPACITY)
            )


def service_finished_after_max_end_time(factory: ConstraintFactory):
    return (factory.for_each(Visit)
            .filter(lambda visit: visit.is_service_finished_after_max_end_time())
            .penalize(HardSoftScore.of(1, 0),  # ONE_HARD equivalent
                      lambda visit: visit.service_finished_delay_in_minutes())
            .as_constraint(SERVICE_FINISHED_AFTER_MAX_END_TIME)
            )


def limit_driving_time(factory: ConstraintFactory):
    return (factory.for_each(Vehicle)
            .filter(lambda vehicle: vehicle.total_driving_time_seconds > DRIVING_TIME_LIMIT_SECONDS)
            .penalize(HardSoftScore.of(1, 0),  # ONE_HARD equivalent
                      lambda vehicle: vehicle.total_driving_time_seconds - DRIVING_TIME_LIMIT_SECONDS)
            .as_constraint(LIMIT_DRIVING_TIME)
            )


##############################################
# Soft constraints
##############################################

def minimize_travel_time(factory: ConstraintFactory):
    return (
        factory.for_each(Vehicle)
        .penalize(HardSoftScore.of(0, 1),  # ONE_SOFT equivalent
                  lambda vehicle: vehicle.calculate_total_driving_time_seconds())
        .as_constraint(MINIMIZE_TRAVEL_TIME)
    )


def balance_load(factory: ConstraintFactory):
    """
    Balance the load among vehicles by penalizing higher loads more significantly.
    """
    return (
        factory.for_each(Vehicle)
        .penalize(HardSoftScore.of(0, 5),  # Increased weight for stronger influence
                  lambda vehicle: vehicle.total_demand)
        .as_constraint(BALANCE_LOAD)
    )


def minimize_max_load(factory: ConstraintFactory):
    """
    Minimize the maximum load across all vehicles.
    """
    return (
        factory.for_each(Vehicle)
        .filter(lambda vehicle: vehicle.total_demand > MAX_LOAD_PER_VEHICLE)
        .penalize(HardSoftScore.of(0, 10),
                  lambda vehicle: vehicle.total_demand - MAX_LOAD_PER_VEHICLE)
        .as_constraint(MINIMIZE_MAX_LOAD)
    )


def encourage_full_utilization(factory: ConstraintFactory):
    """
    Encourage vehicles to reach a minimum load threshold.
    """
    return (
        factory.for_each(Vehicle)
        .filter(lambda vehicle: vehicle.total_demand < MIN_LOAD_THRESHOLD)
        .penalize(HardSoftScore.of(0, 3),
                  lambda vehicle: MIN_LOAD_THRESHOLD - vehicle.total_demand)
        .as_constraint(ENCOURAGE_FULL_UTILIZATION)
    )


def minimize_vehicle_count(factory: ConstraintFactory):
    """
    Minimize the number of vehicles used.
    """
    return (
        factory.for_each(Vehicle)
        .filter(lambda vehicle: len(vehicle.visits) > 0)
        .penalize(HardSoftScore.of(0, 20))
        .as_constraint(MINIMIZE_VEHICLE_COUNT)
    )
