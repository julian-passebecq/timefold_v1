from typing import Generator, TypeVar, Sequence
from datetime import date, datetime, time, timedelta
from enum import Enum
from random import Random, choice
from dataclasses import dataclass

from .domain import *

FIRST_NAMES = ("Amy", "Beth", "Chad", "Dan", "Elsa", "Flo", "Gus", "Hugo", "Ivy", "Jay")
LAST_NAMES = ("Cole", "Fox", "Green", "Jones", "King", "Li", "Poe", "Rye", "Smith", "Watt")
SERVICE_DURATION_MINUTES = (10, 20, 30, 40)
MORNING_WINDOW_START = time(8, 0)
MORNING_WINDOW_END = time(12, 0)
AFTERNOON_WINDOW_START = time(13, 0)
AFTERNOON_WINDOW_END = time(18, 0)

# Define the fixed warehouse location
WAREHOUSE_LOCATION = Location(
    latitude=47.57900943093803,
    longitude=5.576702063852337
)

@dataclass
class _DemoDataProperties:
    seed: int
    visit_count: int
    vehicle_count: int
    vehicle_start_time: time
    min_demand: int
    max_demand: int
    min_vehicle_capacity: int
    max_vehicle_capacity: int
    south_west_corner: Location
    north_east_corner: Location

    def __post_init__(self):
        if self.min_demand < 1:
            raise ValueError(f"minDemand ({self.min_demand}) must be greater than zero.")
        if self.max_demand < 1:
            raise ValueError(f"maxDemand ({self.max_demand}) must be greater than zero.")
        if self.min_demand >= self.max_demand:
            raise ValueError(f"maxDemand ({self.max_demand}) must be greater than minDemand ({self.min_demand}).")
        if self.min_vehicle_capacity < 1:
            raise ValueError(f"Number of minVehicleCapacity ({self.min_vehicle_capacity}) must be greater than zero.")
        if self.max_vehicle_capacity < 1:
            raise ValueError(f"Number of maxVehicleCapacity ({self.max_vehicle_capacity}) must be greater than zero.")
        if self.min_vehicle_capacity >= self.max_vehicle_capacity:
            raise ValueError(f"maxVehicleCapacity ({self.max_vehicle_capacity}) must be greater than "
                             f"minVehicleCapacity ({self.min_vehicle_capacity}).")
        if self.visit_count < 1:
            raise ValueError(f"Number of visitCount ({self.visit_count}) must be greater than zero.")
        if self.vehicle_count < 1:
            raise ValueError(f"Number of vehicleCount ({self.vehicle_count}) must be greater than zero.")
        if self.north_east_corner.latitude <= self.south_west_corner.latitude:
            raise ValueError(f"northEastCorner.getLatitude ({self.north_east_corner.latitude}) must be greater than "
                             f"southWestCorner.getLatitude({self.south_west_corner.latitude}).")
        if self.north_east_corner.longitude <= self.south_west_corner.longitude:
            raise ValueError(f"northEastCorner.getLongitude ({self.north_east_corner.longitude}) must be greater than "
                             f"southWestCorner.getLongitude({self.south_west_corner.longitude}).")

class DemoData(Enum):
    NEW_LOCATION = _DemoDataProperties(
        seed=0,
        visit_count=200,
        vehicle_count=50,
        vehicle_start_time=time(7, 30),
        min_demand=2,
        max_demand=4,
        min_vehicle_capacity=10,
        max_vehicle_capacity=15,
        south_west_corner=Location(
            latitude=47.57900943093803 - 0.675,
            longitude=5.576702063852337 - 0.675
        ),  # South-West corner
        north_east_corner=Location(
            latitude=47.57900943093803 + 0.675,
            longitude=5.576702063852337 + 0.675
        )   # North-East corner
    )

def doubles(random: Random, start: float, end: float) -> Generator[float, None, None]:
    while True:
        yield random.uniform(start, end)

def ints(random: Random, start: int, end: int) -> Generator[int, None, None]:
    while True:
        yield random.randrange(start, end)

T = TypeVar('T')

def values(random: Random, sequence: Sequence[T]) -> Generator[T, None, None]:
    start = 0
    end = len(sequence) - 1
    while True:
        yield sequence[random.randint(start, end)]

def generate_names(random: Random) -> Generator[str, None, None]:
    while True:
        yield f'{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}'

def generate_demo_data(demo_data_enum: DemoData = None) -> VehicleRoutePlan:
    name = "demo"
    if demo_data_enum is None:
        demo_data = choice(list(DemoData)).value
    else:
        demo_data = demo_data_enum.value
    random = Random(demo_data.seed)

    # Create a list of all possible latitude and longitude ranges
    all_lat_lon_ranges = [
        (data.value.south_west_corner, data.value.north_east_corner)
        for data in DemoData
    ]

    def random_location():
        sw, ne = random.choice(all_lat_lon_ranges)
        return Location(
            latitude=random.uniform(sw.latitude, ne.latitude),
            longitude=random.uniform(sw.longitude, ne.longitude)
        )

    demands = ints(random, demo_data.min_demand, demo_data.max_demand + 1)
    service_durations = values(random, SERVICE_DURATION_MINUTES)
    vehicle_capacities = ints(random, demo_data.min_vehicle_capacity,
                              demo_data.max_vehicle_capacity + 1)

    vehicles = [Vehicle(
        id=str(i),
        capacity=next(vehicle_capacities),
        home_location=WAREHOUSE_LOCATION,  # Fixed warehouse location
        departure_time=datetime.combine(
            date.today() + timedelta(days=1), demo_data.vehicle_start_time)
    ) for i in range(demo_data.vehicle_count)]

    names = generate_names(random)
    visits = [
        Visit(
            id=str(i),
            name=next(names),
            location=random_location(),
            demand=next(demands),
            min_start_time=datetime.combine(
                date.today() + timedelta(days=1),
                MORNING_WINDOW_START if (morning_window := random.random() > 0.5) else AFTERNOON_WINDOW_START
            ),
            max_end_time=datetime.combine(
                date.today() + timedelta(days=1),
                MORNING_WINDOW_END if morning_window else AFTERNOON_WINDOW_END
            ),
            service_duration=timedelta(minutes=next(service_durations)),
        ) for i in range(demo_data.visit_count)
    ]

    return VehicleRoutePlan(
        name=name,
        south_west_corner=min(
            (data.value.south_west_corner for data in DemoData),
            key=lambda loc: (loc.latitude, loc.longitude)
        ),
        north_east_corner=max(
            (data.value.north_east_corner for data in DemoData),
            key=lambda loc: (loc.latitude, loc.longitude)
        ),
        vehicles=vehicles,
        visits=visits
    )

def tomorrow_at(local_time: time) -> datetime:
    return datetime.combine(date.today(), local_time)
