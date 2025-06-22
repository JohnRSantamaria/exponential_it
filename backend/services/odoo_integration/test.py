from exponential_core.secrets import SecretManager

from dotenv import load_dotenv

load_dotenv(dotenv_path=".env.local")
# Instanciar el SecretManager con el secreto base
manager = SecretManager(base_secret_name="exponentialit/core")

# Obtener el secreto completo
try:
    secret = manager.get_secret()
    print("✅ Secreto obtenido correctamente:")
    print(secret)
except Exception as e:
    print("❌ Error al obtener el secreto:")
    print(e)
