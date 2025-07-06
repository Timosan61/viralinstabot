"""
Модуль для анализа видео с помощью AI Vision и генерации сценариев.
"""

from .scenario_generator import ScenarioGenerator, get_scenario_generator, initialize_scenario_generator

__all__ = [
    'ScenarioGenerator',
    'get_scenario_generator',
    'initialize_scenario_generator'
]