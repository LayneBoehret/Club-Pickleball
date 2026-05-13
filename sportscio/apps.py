# Description: Application configuration for the Sportscio Django app.
from django.apps import AppConfig

class SportscioConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "sportscio"

    def ready(self):
        # Importing signals here ensures they are registered when Django starts
        import sportscio.signals