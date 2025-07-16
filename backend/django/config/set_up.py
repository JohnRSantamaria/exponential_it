import os
from decouple import config


def set_up_environment():
    settings_module = (
        "config.settings.local"
        if config("DEBUG", default=False, cast=bool)
        else "config.settings.prod"
    )
    print(f"settings_module : {settings_module}")
    os.environ["DJANGO_SETTINGS_MODULE"] = settings_module
