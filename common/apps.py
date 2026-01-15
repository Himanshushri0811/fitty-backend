from django.apps import AppConfig


class CommonConfig(AppConfig):
    name = 'common'

    def ready(self):
        # Database connection is now handled in settings.py to ensure single registration
        pass
