
from db.connection import get_connection

TABLA_RUTAS = "Riesgo..Rutas_instancias_BT_150926"

QUERY_RUTA_POR_INSTANCIA = f"""
    SELECT Ruta_Relativa_FileSystem, Nombre_Fisico_GUID, Extension, Nombre_Original_Usuario
    FROM {TABLA_RUTAS}
    WHERE Instancia_Proceso = ?
"""

def get_archivos_por_instancia(instancia: int) -> list[dict]:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(QUERY_RUTA_POR_INSTANCIA, instancia)
        rows = cursor.fetchall()
        return [
            {
                "ruta_relativa": row.Ruta_Relativa_FileSystem,
                "guid": row.Nombre_Fisico_GUID,
                "extension": row.Extension,
                "nombre_original": row.Nombre_Original_Usuario,
            }
            for row in rows
        ]
    finally:
        conn.close()
