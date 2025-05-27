from django.conf import settings


def build_db_config(camp) -> dict:
    """
    Recibe una instancia de Camp y retorna el diccionario de configuración
    de base de datos compatible con Django.
    """
    use_ssl = camp.db_host != "localhost"

    return {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": camp.db_name,
        "USER": camp.db_user,
        "PASSWORD": camp.db_password,
        "HOST": camp.db_host,
        "PORT": str(camp.db_port),
        "TIME_ZONE": settings.TIME_ZONE,
        "CONN_HEALTH_CHECKS": True,
        "CONN_MAX_AGE": 300,  # keep connections open for 5 minutes
        "AUTOCOMMIT": True,
        "ATOMIC_REQUESTS": True,  # Each request will be a transaction
        "OPTIONS": {
            "sslmode": "require" if use_ssl else "disable",
        },
    }
