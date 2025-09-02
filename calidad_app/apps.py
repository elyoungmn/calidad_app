from django.apps import AppConfig

class CalidadAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'calidad_app'

    def ready(self):
        import calidad_app.signals  # activa las señales
