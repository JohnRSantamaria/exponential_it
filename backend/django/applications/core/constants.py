# applications/core/constants.py

# Apps que solo existen en las bases de datos de campamentos
CAMP_APPS = ["schedule", "activities"]


# Apps que deben vivir SOLO en la base de datos central
CENTRAL_APPS = [
    "users",
    "services",
    "camps",
    "core",
    "admin",
    "auth",
    "contenttypes",
    "sessions",
    "oauth2_provider",
]
