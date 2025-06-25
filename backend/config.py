import os
from dotenv import load_dotenv

load_dotenv()

# Configuración de base de datos
MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
MYSQL_PORT = os.getenv('MYSQL_PORT', '3306')
MYSQL_USER = os.getenv('MYSQL_USER', 'root')
MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', 'password')
MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', 'sgsi_db')

# Configuración de seguridad
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'clave-secreta-por-defecto')
JWT_ACCESS_TOKEN_EXPIRES = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', '3600'))

# URLs de servicios
SERVICE_AUTH_URL = os.getenv('SERVICE_AUTH_URL', 'http://localhost:5001')
SERVICE_RIESGOS_URL = os.getenv('SERVICE_RIESGOS_URL', 'http://localhost:5002')
SERVICE_DOCUMENTACION_URL = os.getenv('SERVICE_DOCUMENTACION_URL', 'http://localhost:5003')
SERVICE_AUDITORIAS_URL = os.getenv('SERVICE_AUDITORIAS_URL', 'http://localhost:5004')
SERVICE_INCIDENTES_URL = os.getenv('SERVICE_INCIDENTES_URL', 'http://localhost:5005')
SERVICE_PROVEEDORES_URL = os.getenv('SERVICE_PROVEEDORES_URL', 'http://localhost:5006')
SERVICE_ROLES_URL = os.getenv('SERVICE_ROLES_URL', 'http://localhost:5007')
