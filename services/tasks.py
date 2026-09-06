from celery import shared_task

from .weather_service import get_current


@shared_task
def refresh_weather(latitude, longitude):
    """Optional Celery hook for scheduled weather refresh jobs."""
    return get_current(latitude, longitude)
