from django.db import models


class Location(models.Model):
    """Saved public location metadata; coordinates remain portable on SQLite."""
    name = models.CharField(max_length=160)
    admin_area = models.CharField(max_length=160, blank=True)
    country = models.CharField(max_length=120, default="India")
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    source = models.CharField(max_length=80, default="Open-Meteo geocoding")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [models.Index(fields=["name"]), models.Index(fields=["latitude", "longitude"])]


class DataSource(models.Model):
    name = models.CharField(max_length=120, unique=True)
    url = models.URLField(blank=True)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=30, default="LIVE")
    updated_at = models.DateTimeField(auto_now=True)

