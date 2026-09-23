import sys
from db.queries import get_archivos_por_instancia
from file_access.name_filter import es_archivo_excluido
from file_access.file_locator import listar_archivos_cliente
from file_access.file_downloader import descargar_archivos

def main():
    if len(sys.argv) < 2:
        print("//////")
        sys.exit(1)

    instancia = int(sys.argv[1])

    todos = get_archivos_por_instancia(instancia)
    excluidos = [r for r in todos if es_archivo_excluido(r["nombre_original"])]
    print(f"Excluidos por nombre ({len(excluidos)}):")
    for r in excluidos:
        print(f"  - {r['nombre_original']}")

    archivos = listar_archivos_cliente(instancia)
    if not archivos:
        print(f"\nNo quedaron archivos por procesar para la instancia {instancia}")
        return

    resultado = descargar_archivos(instancia, archivos)

    print(f"\nResultado de descarga ({len(resultado)} archivos):")
    for archivo in resultado:
        estado = "COPIADO" if archivo["copiado"] else "FALLÓ/NO EXISTE"
        print(f"  [{estado}] {archivo['nombre_original']} -> {archivo.get('ruta_local') or archivo['ruta']}")

if __name__ == "__main__":
    main()
