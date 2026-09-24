from config.settings import settings
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

# Solicitudes del periodo (Cod_Mes). Se ejecuta directo contra NEGOCIO_DB_HOST / NEGOCIO_DB_NAME.
# Num_Sol es la instancia que se usa luego en QUERY_RUTA_POR_INSTANCIA.
QUERY_SOLICITUDES_POR_PERIODO = """
    SELECT C.Cod_Mes, A.Num_Sol, A.Est_Ing, A.Fec_Ing, C.Ing_Mes_PEN, C.Usu_Eje, C.Nom_Ccs, C.Fec_Des,
           C.Num_Ope, C.Tip_Doc_Cli, C.Num_Doc_Cli, C.Ruc_Emp, C.Niv_Apr_Exp, D.Nom_Cli, D.Ape_Pat, D.Ape_Mat
    FROM (
        SELECT Cod_Mes, Num_Sol, Est_Ing, Fec_Ing,
               ROW_NUMBER() OVER (PARTITION BY Num_Sol ORDER BY Fec_Ing DESC) Orden
        FROM dbo.SOL_TPO_GES
        WHERE Est_Ing LIKE '%Predictor%' AND Cod_Mes = ?
    ) A
    LEFT JOIN dbo.CRE_SOL C ON A.Num_Sol = C.Num_Sol
    LEFT JOIN dbo.CLI_MAF D ON C.Cod_Cli_Maf = D.Cod_Cli_Maf
    WHERE A.Orden = 1
      AND C.Num_Ope IS NOT NULL
"""

def get_solicitudes_por_periodo(periodo: str) -> list[dict]:
    """Solicitudes (una por Num_Sol) del periodo YYYYMM, con los datos del cliente."""
    conn = get_connection(settings.NEGOCIO_DB_HOST, settings.NEGOCIO_DB_NAME)
    try:
        cursor = conn.cursor()
        cursor.execute(QUERY_SOLICITUDES_POR_PERIODO, periodo)
        columnas = [col[0] for col in cursor.description]
        return [dict(zip(columnas, row)) for row in cursor.fetchall()]
    finally:
        conn.close()
