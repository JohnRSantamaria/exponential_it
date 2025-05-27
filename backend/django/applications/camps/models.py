from cryptography.fernet import Fernet
from django.db import models
from cryptography.fernet import Fernet, InvalidToken
from decouple import config


class Camp(models.Model):
    name = models.CharField(max_length=100, unique=True)
    db_name = models.CharField(max_length=100, unique=True)
    db_user = models.CharField(max_length=100)
    _db_password = models.BinaryField(db_column="db_password")  # almacenado cifrado
    db_host = models.CharField(max_length=100, default="localhost")
    db_port = models.IntegerField(default=5432)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Campamento"
        verbose_name_plural = "Campamentos"

    @property
    def db_password(self):
        try:
            key = config("CAMP_CRYPTO_KEY").encode()
            return Fernet(key).decrypt(self._db_password).decode()
        except (InvalidToken, TypeError):
            return ""

    @db_password.setter
    def db_password(self, value: str):
        key = config("CAMP_CRYPTO_KEY").encode()
        self._db_password = Fernet(key).encrypt(value.encode())

    def get_db_config(self):
        return {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": self.db_name,
            "USER": self.db_user,
            "PASSWORD": self.db_password,
            "HOST": self.db_host,
            "PORT": str(self.db_port),
            "CONN_MAX_AGE": 300,
            "AUTOCOMMIT": True,
            "OPTIONS": {
                "sslmode": "require" if self.db_host != "localhost" else "disable",
            },
        }
