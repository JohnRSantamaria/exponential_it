from django.db import models


from applications.core.db_utils import decrypt_value, encrypt_value


class Camp(models.Model):
    name = models.CharField(max_length=100, unique=True)
    db_name = models.CharField(max_length=100, unique=True)
    db_user = models.CharField(max_length=100)
    _db_password = models.BinaryField(db_column="db_password")  # almacenado cifrado
    db_host = models.CharField(max_length=100, default="localhost")
    db_port = models.IntegerField(default=5432)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Campamento"
        verbose_name_plural = "Campamentos"

    @property
    @property
    def db_password(self):
        return decrypt_value(self._db_password)

    @db_password.setter
    def db_password(self, value: str):
        self._db_password = encrypt_value(value)

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
