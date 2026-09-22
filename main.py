

import sys
from file_access.file_locator import listar_archivos_cliente

def main():
    if len(sys.argv) < 2:
        print("Uso: python test_file_locator.py <instancia>")
        sys.exit(1)

    instancia = int(sys.argv[1])
    archivos = listar_archivos_cliente(instancia)

    if not archivos:
        print(f"No se encontraron registros para la instancia {instancia}")
        return

    print(f"Archivos encontrados ({len(archivos)}):")
    for archivo in archivos:
        estado = "OK" if archivo["existe"] else "NO ENCONTRADO"
        print(f"  [{estado}] {archivo['ruta']}")

if __name__ == "__main__":
    main()
