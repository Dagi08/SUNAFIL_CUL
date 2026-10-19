"""
Extrae la información de uno o varios Certificados Únicos Laborales (CUL) a JSON.
Uso (desde la raíz del proyecto):
    python -m scripts.extraer_cul documentos/817681/20260807_0003204512_000001.pdf
    python -m scripts.extraer_cul documentos/817681            (todos los PDF de la carpeta)
"""
import json
import sys
from pathlib import Path

from extraction.cul_parser import extraer_cul

def main():
    if len(sys.argv) < 2:
        print("Uso: python -m scripts.extraer_cul <archivo_o_carpeta>")
        sys.exit(1)

    objetivo = Path(sys.argv[1])
    rutas = sorted(objetivo.glob("*.pdf")) if objetivo.is_dir() else [objetivo]

    resultados = []
    for ruta in rutas:
        try:
            resultados.append(extraer_cul(ruta))
        except ValueError as e:
            print(f"Omitido: {e}", file=sys.stderr)

    print(json.dumps(resultados if objetivo.is_dir() else resultados[:1], ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
