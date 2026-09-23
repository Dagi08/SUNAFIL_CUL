import pyodbc
from config.settings import settings  

def get_connection():
    conn_parts = [
        f"DRIVER={{{settings.DB_DRIVER}}}"
    ]

    if settings.DB_PORT:
        conn_parts.append(f"SERVER={settings.DB_HOST},{settings.DB_PORT}")
    else:
        conn_parts.append(f"SERVER={settings.DB_HOST}")

    conn_parts.append(f"DATABASE={settings.DB_NAME}")

    if settings.DB_USER and settings.DB_PASSWORD:
        conn_parts.append(f"UID={settings.DB_USER}")
        conn_parts.append(f"PWD={settings.DB_PASSWORD}")
    else:
        conn_parts.append("Trusted_Connection=yes")

    if settings.DB_EXTRA_PARAMS:
        conn_parts.append(settings.DB_EXTRA_PARAMS)

    conn_str = ";".join(conn_parts)

    print(f" Intentando conectar a: {conn_str}") 

    return pyodbc.connect(conn_str, timeout=settings.FILE_SERVER_TIMEOUT_SECONDS)
