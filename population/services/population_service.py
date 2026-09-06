from .population_provider import get_population


def population_for_location(latitude: float, longitude: float) -> dict:
    return get_population(latitude, longitude)
