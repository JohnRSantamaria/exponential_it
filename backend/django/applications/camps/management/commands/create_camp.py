# applications/camps/management/commands/create_camp.py
import re
import psycopg2
import dj_database_url

from decouple import config
from camps.models import Camp
from applications.core.db_utils import build_db_config

from django.db import connections, connection
from django.db.utils import OperationalError
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import BaseCommand

from applications.core.constants import CAMP_APPS


class Command(BaseCommand):
    help = "Crea un nuevo campamento (base de datos + migraciones + registro opcional de superusuario)"

    def add_arguments(self, parser):
        default_db_config = dj_database_url.parse(config("DATABASE_PROD"))

        parser.add_argument("name", type=str, help="Nombre del campamento (slug)")
        parser.add_argument(
            "--db_name", type=str, required=True, help="Nombre de la base de datos"
        )
        parser.add_argument("--db_user", type=str, default=default_db_config["USER"])
        parser.add_argument(
            "--db_password", type=str, default=default_db_config["PASSWORD"]
        )
        parser.add_argument("--db_host", type=str, default=default_db_config["HOST"])
        parser.add_argument("--db_port", type=str, default=default_db_config["PORT"])

        # Superusuario
        parser.add_argument(
            "--with-superuser", action="store_true", help="Crea un superusuario"
        )
        parser.add_argument("--su_name", type=str, help="Nombre del superusuario")
        parser.add_argument(
            "--su_last_name", type=str, help="Apellido del superusuario"
        )
        parser.add_argument("--su_email", type=str)
        parser.add_argument("--su_password", type=str)

    def handle(self, *args, **options):
        name = options["name"]
        db_name = options["db_name"]
        db_user = options["db_user"]
        db_password = options["db_password"]
        db_host = options["db_host"]
        db_port = options["db_port"]

        if not re.match(r"^[a-zA-Z0-9_]+$", db_name):
            self.stdout.write(
                self.style.ERROR(
                    "❌ Nombre de base de datos inválido. Solo letras, números y guión bajo."
                )
            )
            return

        # 1. Crear base de datos
        self.stdout.write(f"🧱 Creando base de datos '{db_name}'...")

        try:
            base_db_config = dj_database_url.parse(config("DATABASE_PROD"))
            base_dbname = base_db_config["NAME"]

            conn = psycopg2.connect(
                dbname=base_dbname,  # o cualquier base temporal, por lo general postgres existe
                user=db_user,
                password=db_password,
                host=db_host,
                port=db_port,
            )
            conn.autocommit = True
            with conn.cursor() as cursor:
                cursor.execute(f"CREATE DATABASE {db_name} TEMPLATE template1")
            conn.close()
        except psycopg2.errors.DuplicateDatabase:
            self.stdout.write(
                self.style.WARNING(
                    f"⚠️ La base de datos '{db_name}' ya existe. Continuando..."
                )
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Error al crear la base de datos: {e}")
            )
            return

        # 2. Registrar campamento en la base principal
        camp, created = Camp.objects.get_or_create(
            name=name,
            defaults={
                "db_name": db_name,
                "db_user": db_user,
                "db_password": db_password,
                "db_host": db_host,
                "db_port": db_port,
            },
        )

        if not created:
            self.stdout.write(
                self.style.WARNING(f"⚠️ Campamento '{name}' ya estaba registrado.")
            )

        # 3. Conectar y migrar
        db_config = build_db_config(camp)
        connections.databases[db_name] = db_config

        # 4. Aplicar solo migraciones de apps del campamento
        self.stdout.write("⚙️ Aplicando migraciones en la nueva base de datos...")
        # call_command("migrate", database=db_name)
        try:
            connection.ensure_connection()
        except OperationalError as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Error al conectar a la base de datos: {e}")
            )
            return

        self.stdout.write(
            self.style.NOTICE(f"🔗 Conectado a la base de datos '{db_name}'.")
        )
        self.stdout.write(
            self.style.MIGRATE_HEADING(f"🔄 Migrando aplicaciones en '{db_name}':")
        )
        self.stdout.write(
            self.style.MIGRATE_LABEL("Aplicando migraciones de apps del campamento...")
        )

        # Aplicar migraciones solo de las apps del campamento
        if not CAMP_APPS:
            self.stdout.write(
                self.style.WARNING("⚠️ No hay apps de campamento para migrar.")
            )
            return
        self.stdout.write(
            self.style.SQL_KEYWORD("Aplicando migraciones para las siguientes apps:")
        )

        for app in CAMP_APPS:
            call_command("migrate", app, database=db_name, verbosity=0)

        self.stdout.write(
            self.style.SUCCESS(
                f"✅ Campamento '{name}' listo y migrado con base '{db_name}'."
            )
        )

        # 4. Crear superusuario (opcional)
        if options["with_superuser"]:
            self.stdout.write("👤 Preparando creación de superusuario...")

            UserModel = get_user_model()
            su_name = options.get("su_name")
            su_last_name = options.get("su_last_name", "")
            su_email = options.get("su_email")
            su_password = options.get("su_password")

            if not su_email or not su_name or not su_password:
                self.stdout.write(
                    self.style.WARNING(
                        "⚠️ Faltan datos para el superusuario. Usando modo interactivo."
                    )
                )
                call_command("createsuperuser", database=db_name)
                return

            try:
                if UserModel.objects.using(db_name).filter(is_superuser=True).exists():
                    self.stdout.write(
                        self.style.WARNING("⚠️ Ya existe un superusuario.")
                    )
                    return
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"❌ Error verificando superusuario: {e}")
                )
                return

            try:
                UserModel.objects.db_manager(db_name).create_superuser(
                    email=su_email,
                    password=su_password,
                    name=su_name,
                    last_name=su_last_name,
                )
                self.stdout.write(
                    self.style.SUCCESS("✅ Superusuario creado exitosamente.")
                )
                self.stdout.write(
                    f"🪪 Usuario: {su_name} {su_last_name} | ✉️ {su_email}"
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"❌ No se pudo crear el superusuario: {e}")
                )


# Ejemplo de uso:
# python manage.py create_camp camp_cliente --db_name=camp_cliente --db_host=localhost --db_port=5433 --db_user=saas_user --db_password=saas_pass --with-superuser --su_name=admin --su_last_name=cliente -- 
# python manage.py create_camp camp_cliente --db_name=camp_cliente --db_host=localhost --db_port=5433 --db_user=saas_user   --db_password=saas_pass
