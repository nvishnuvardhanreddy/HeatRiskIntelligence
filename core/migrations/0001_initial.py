from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name="DataSource",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120, unique=True)),
                ("url", models.URLField(blank=True)),
                ("description", models.TextField(blank=True)),
                ("status", models.CharField(default="LIVE", max_length=30)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name="Location",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=160)),
                ("admin_area", models.CharField(blank=True, max_length=160)),
                ("country", models.CharField(default="India", max_length=120)),
                ("latitude", models.DecimalField(decimal_places=6, max_digits=9)),
                ("longitude", models.DecimalField(decimal_places=6, max_digits=9)),
                ("source", models.CharField(default="Open-Meteo geocoding", max_length=80)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "indexes": [
                    models.Index(fields=["name"], name="core_locati_name_65ac84_idx"),
                    models.Index(fields=["latitude", "longitude"], name="core_locati_latitud_367ccc_idx"),
                ],
            },
        ),
    ]
