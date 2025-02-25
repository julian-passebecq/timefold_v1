from timefold.solver import SolverManager, SolutionManager
from timefold.solver.config import (SolverConfig, ScoreDirectorFactoryConfig,
                                    TerminationConfig, Duration)

from .domain import *
from .constraints import define_constraints


solver_config = SolverConfig(
    solution_class=VehicleRoutePlan,
    entity_class_list=[Vehicle, Visit],
    score_director_factory_config=ScoreDirectorFactoryConfig(
        constraint_provider_function=define_constraints
    ),
    termination_config=TerminationConfig(
        spent_limit=Duration(seconds=600)
    )
)

solver_manager = SolverManager.create(solver_config)
solution_manager = SolutionManager.create(solver_manager)

