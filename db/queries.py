from db.connection import get_connection, get_connection_negocio

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

# Solicitudes del periodo (cre_col.cod_mes = ?). Se ejecuta contra NEGOCIO_DB_HOST / NEGOCIO_DB_NAME y lee
# PWC_SERVICIO_2 de Riesgo por servidor vinculado. Est_Ing = 'Predictor' cuando el nodo
# (2 primeros caracteres de DESCRIPCION_DETALLE) está entre 39 y 56.
# Num_Sol es la instancia que se usa luego en QUERY_RUTA_POR_INSTANCIA.
QUERY_SOLICITUDES_POR_PERIODO = """
    SELECT C.Cod_Mes, A.Num_Sol, A.Est_Ing, A.Fec_Ing, C.Ing_Mes_PEN, C.Usu_Eje, C.Nom_Ccs, C.Fec_Des,
           C.Num_Ope, C.Tip_Doc_Cli, C.Num_Doc_Cli, C.Ruc_Emp, C.Niv_Apr_Exp, D.Nom_Cli, D.Ape_Pat, D.Ape_Mat
    FROM (
        SELECT a.PER_S2 Cod_Mes, CAST(a.ADT_FECH_REG_S2 AS date) Fec_Ing, a.num_sol, a.Est_Ing
        FROM (
            SELECT b.cod_mes, b.num_sol, b.num_ope, a.*, LEFT(DESCRIPCION_DETALLE, 2) Nodo,
                   CASE WHEN LEFT(DESCRIPCION_DETALLE, 2) >= 39 AND LEFT(DESCRIPCION_DETALLE, 2) <= 56
                        THEN 'Predictor' ELSE 'No_Aplica' END Est_Ing
            FROM [SRVJADBRGO02\\SQL01DBA2019].[Riesgo].[dbo].[PWC_SERVICIO_2] a
            INNER JOIN [SRVJADBANLT01\\SQL01DBA2019].negocio.dbo.cre_col b
                    ON a.ID_SOLICITUD_S2 = b.num_sol AND b.cod_mes = ?
        ) A
        WHERE Est_Ing = 'Predictor'
    ) A
    LEFT JOIN dbo.CRE_SOL C ON A.Num_Sol = C.Num_Sol
    LEFT JOIN dbo.CLI_MAF D ON C.Cod_Cli_Maf = D.Cod_Cli_Maf
    WHERE C.Num_Ope IS NOT NULL
"""

# Columnas que devuelve QUERY_SOLICITUDES_POR_PERIODO, en el orden en que van al Excel de validación
COLUMNAS_SOLICITUD = [
    "Cod_Mes", "Num_Sol", "Est_Ing", "Fec_Ing", "Ing_Mes_PEN", "Usu_Eje", "Nom_Ccs", "Fec_Des",
    "Num_Ope", "Tip_Doc_Cli", "Num_Doc_Cli", "Ruc_Emp", "Niv_Apr_Exp", "Nom_Cli", "Ape_Pat", "Ape_Mat",
]

def get_solicitudes_por_periodo(periodo: str) -> list[dict]:
    """Solicitudes (una por Num_Sol) del periodo YYYYMM, con los datos del cliente."""
    conn = get_connection_negocio()
    try:
        cursor = conn.cursor()
        cursor.execute(QUERY_SOLICITUDES_POR_PERIODO, periodo)
        columnas = [col[0] for col in cursor.description]
        return [dict(zip(columnas, row)) for row in cursor.fetchall()]
    finally:
        conn.close()
