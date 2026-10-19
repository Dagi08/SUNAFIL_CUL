import logging
import pyodbc
from config.settings import settings

logger = logging.getLogger(__name__)

def _conectar(driver, host, port, database, user, password, extra_params):
    conn_parts = [
        f"DRIVER={{{driver}}}"
    ]

    if port:
        conn_parts.append(f"SERVER={host},{port}")
    else:
        conn_parts.append(f"SERVER={host}")

    conn_parts.append(f"DATABASE={database}")

    if user and password:
        conn_parts.append(f"UID={user}")
        conn_parts.append(f"PWD={password}")
    else:
        conn_parts.append("Trusted_Connection=yes")

    if extra_params:
        conn_parts.append(extra_params)

    conn_str = ";".join(conn_parts)

    # No se imprime conn_str completo para no exponer credenciales
    logger.info(f"Conectando a {host} / {database}")

    return pyodbc.connect(conn_str, timeout=settings.FILE_SERVER_TIMEOUT_SECONDS)

def get_connection():
    """BD de Riesgo (rutas de archivos): variables DB_* del .env."""
    return _conectar(
        settings.DB_DRIVER,
        settings.DB_HOST,
        settings.DB_PORT,
        settings.DB_NAME,
        settings.DB_USER,
        settings.DB_PASSWORD,
        settings.DB_EXTRA_PARAMS,
    )

def get_connection_negocio():
    """BD de Negocio (solicitudes del periodo): variables NEGOCIO_DB_* del .env."""
    return _conectar(
        settings.NEGOCIO_DB_DRIVER,
        settings.NEGOCIO_DB_HOST,
        settings.NEGOCIO_DB_PORT,
        settings.NEGOCIO_DB_NAME,
        settings.NEGOCIO_DB_USER,
        settings.NEGOCIO_DB_PASSWORD,
        settings.NEGOCIO_DB_EXTRA_PARAMS,
    )
