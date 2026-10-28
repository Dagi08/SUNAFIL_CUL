"""
Diagnóstico de la conexión a las BD (Negocio y Riesgo) con lo que hay en el .env.
Muestra el valor exacto leído de cada variable (repr: deja ver comillas, espacios o caracteres raros),
la cadena de conexión que se arma y si conecta.
Uso (desde la raíz del proyecto, donde está el .env):
    python -m scripts.test_conexion
"""
import re
from pathlib import Path

import pyodbc

from config.settings import settings
from db.connection import armar_conn_str

def _ocultar_pwd(conn_str: str) -> str:
    return re.sub(r"PWD=[^;]*", "PWD=***", conn_str)

def _probar(nombre: str, conn_str: str) -> None:
    print(f"\n[{nombre}]\n  {_ocultar_pwd(conn_str)}")
    try:
        with pyodbc.connect(conn_str, timeout=settings.FILE_SERVER_TIMEOUT_SECONDS) as conn:
            servidor, bd = conn.cursor().execute("SELECT @@SERVERNAME, DB_NAME()").fetchone()
        print(f"  OK -> conectado a {servidor} / {bd}")
    except pyodbc.Error as e:
        print(f"  ERROR -> {e}")

def main():
    print(f".env leído: {(Path.cwd() / '.env').resolve()} (existe: {(Path.cwd() / '.env').exists()})")
    print(f"Drivers ODBC instalados: {pyodbc.drivers()}")

    print("\nVariables de Negocio tal como se leen:")
    for var in ["NEGOCIO_DB_HOST", "NEGOCIO_DB_NAME", "NEGOCIO_DB_PORT", "NEGOCIO_DB_DRIVER",
                "NEGOCIO_DB_USER", "NEGOCIO_DB_EXTRA_PARAMS"]:
        print(f"  {var} = {getattr(settings, var)!r}")
    print(f"  NEGOCIO_DB_PASSWORD = {'<con valor>' if settings.NEGOCIO_DB_PASSWORD else '<vacío>'}")

    _probar("Negocio, como lo arma el proyecto", armar_conn_str(
        settings.NEGOCIO_DB_DRIVER, settings.NEGOCIO_DB_HOST, settings.NEGOCIO_DB_PORT,
        settings.NEGOCIO_DB_NAME, settings.NEGOCIO_DB_USER, settings.NEGOCIO_DB_PASSWORD,
        settings.NEGOCIO_DB_EXTRA_PARAMS,
    ))
    # Igual que en el otro proyecto que sí conecta (valores fijos, sin .env)
    _probar("Negocio, cadena fija", (
        "DRIVER={ODBC Driver 17 for SQL Server};SERVER=SRVJADBANLT01\\SQL01DBA2019;"
        "DATABASE=Negocio;Trusted_Connection=yes;"
    ))
    _probar("Riesgo, como lo arma el proyecto", armar_conn_str(
        settings.DB_DRIVER, settings.DB_HOST, settings.DB_PORT, settings.DB_NAME,
        settings.DB_USER, settings.DB_PASSWORD, settings.DB_EXTRA_PARAMS,
    ))

if __name__ == "__main__":
    main()
