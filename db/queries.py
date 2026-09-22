from db.connection import get_connection

TABLA_RUTAS = "Riesgo..Rutas_instancias_BT_150926"

QUERY_RUTA_POR_INSTANCIA = f"""
    SELECT Ruta_Relativa_FileSystem, Nombre_Fisico_GUID, Extension
    FROM {TABLA_RUTAS}
    WHERE Instancia_Proceso = ?
"""

def get_archivos_por_instancia(instancia: int) -> list[dict]:
    """Devuelve la lista de archivos (ruta relativa, guid, extensión) para una instancia."""
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
            }
            for row in rows
        ]
    finally:
        conn.close()
