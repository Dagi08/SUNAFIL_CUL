import logging
import pyodbc
from config.settings import settings

logger = logging.getLogger(__name__)

def get_connection(host: str | None = None, database: str | None = None):
    """
    Conexión a SQL Server. Por defecto usa DB_HOST/DB_NAME (Riesgo: rutas de archivos);
    se puede apuntar a otro servidor/BD, p. ej. Negocio para las solicitudes del periodo.
    """
    host = host or settings.DB_HOST
    database = database or settings.DB_NAME

    conn_parts = [
        f"DRIVER={{{settings.DB_DRIVER}}}"
    ]

    if settings.DB_PORT:
        conn_parts.append(f"SERVER={host},{settings.DB_PORT}")
    else:
        conn_parts.append(f"SERVER={host}")

    conn_parts.append(f"DATABASE={database}")

    if settings.DB_USER and settings.DB_PASSWORD:
        conn_parts.append(f"UID={settings.DB_USER}")
        conn_parts.append(f"PWD={settings.DB_PASSWORD}")
    else:
        conn_parts.append("Trusted_Connection=yes")

    if settings.DB_EXTRA_PARAMS:
        conn_parts.append(settings.DB_EXTRA_PARAMS)

    conn_str = ";".join(conn_parts)

    # No se imprime conn_str completo para no exponer credenciales
    logger.info(f"Conectando a {host} / {database}")

    return pyodbc.connect(conn_str, timeout=settings.FILE_SERVER_TIMEOUT_SECONDS)
