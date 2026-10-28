# SUNAFIL_CUL

Valida los documentos laborales que adjuntan los clientes en sus solicitudes de un periodo:

- **SUNAFIL** ("Verifica tu Chamba")
- **CUL** (Certificado Único Laboral del MTPE)
- **BOLETA** de pago

Por cada solicitud descarga sus archivos, extrae el texto (OCR si es escaneo o foto), detecta qué documentos tiene,
lee la identidad y la experiencia laboral del CUL, compara el RUC del empleador con el registrado en la solicitud
y deja **una fila por solicitud** en `resultados/validacion_<periodo>.xlsx`.

## Uso

```bash
python main.py 202608              # todas las solicitudes del periodo (YYYYMM)
python main.py 202608 --limite 5   # solo las primeras 5 (para pruebas)
```

Otros scripts (desde la raíz del proyecto):

| Script | Para qué |
|---|---|
| `python -m scripts.test_conexion` | Diagnostica la conexión a las BD de Negocio y Riesgo con lo que hay en el `.env` |
| `python -m scripts.extraer_cul <pdf_o_carpeta>` | Extrae un CUL a JSON sin BD ni file server |
| `python -m scripts.test_ocr <archivo_o_carpeta>` | Prueba el OCR sobre archivos locales |
| `python -m scripts.procesar_descargados [instancia ...]` | Reprocesa lo ya descargado en `documentos/<periodo>/<instancia>/` sin consultar la BD (en el Excel solo se llena `Num_Sol` de los datos de la solicitud). También borra los archivos sin CUL ni SUNAFIL |

## Flujo

1. **Solicitudes del periodo** – BD Negocio (`db/queries.py`, `QUERY_SOLICITUDES_POR_PERIODO`). Se toma una fila por `Num_Sol` (= instancia).
2. Por cada solicitud:
   1. **Archivos de la instancia** – BD Riesgo (`Rutas_instancias_BT_150926`).
   2. **Filtro por nombre** – se descartan los que no se validan: hoja resumen, pagaré, contratos, cronograma, desgravamen, etc. (`file_access/name_filter.py`).
   3. **Ruta en el file server** y **copia local** a `documentos/<periodo>/<instancia>/`.
   4. **Extracción de texto** (`extraction/ocr_extractor.py`): texto nativo del PDF; OCR con Tesseract para escaneos, imágenes y fotos dentro de Word. Se guarda `logs/extraccion/<periodo>/<instancia>_<fecha>.log` y `.json`.
   5. **Clasificación** SUNAFIL / CUL / BOLETA (`classification/rule_classifier.py`).
   6. **Lectura del CUL** (`extraction/cul_parser.py`): identidad (RENIEC) y experiencia laboral (Planillas Electrónicas). El detalle se guarda junto al PDF como `<archivo>.json`; los datos de SUNAFIL, como `<archivo>_sunafil.json`.
   7. **Fila en el Excel** (`storage/excel_writer.py`).
   8. **Limpieza**: se borran las copias locales de los archivos que no tienen CUL ni SUNAFIL (ver [Carpetas](#carpetas)).
3. Al final muestra cuántas solicitudes se procesaron y cuáles fallaron (detalle en `logs/app.log`).

## Carpetas

Cada periodo tiene sus propias carpetas, que se crean solas al correr `main.py <periodo>`:

```
resultados/validacion_<periodo>.xlsx            reporte del periodo
documentos/<periodo>/<instancia>/               archivos con CUL o SUNAFIL + sus JSON
logs/extraccion/<periodo>/<instancia>_<fecha_hora>.log / .json   texto extraído de todos los archivos
logs/app.log                                    log general (se acumulan todas las corridas)
```

- Al terminar cada solicitud se **borran** de `documentos/` los archivos que no contienen CUL ni SUNAFIL
  (son copias, el original sigue en el file server). Su texto queda en `logs/extraccion/`.
- No se borran los archivos que dieron error al extraer (no se sabe qué contienen), para poder revisarlos.
- Si la carpeta de la instancia queda vacía, también se borra.
- Volver a correr un periodo reescribe sus archivos y JSON y actualiza las filas del Excel; no toca otros periodos.

## Reporte `validacion_<periodo>.xlsx`

Hoja `Validacion`, una fila por solicitud (`Num_Sol`). Si se vuelve a correr el periodo, la fila de la solicitud se
actualiza, no se duplica.

### Columnas

| Columnas | Origen |
|---|---|
| `Cod_Mes`, `Num_Sol`, `Est_Ing`, `Fec_Ing`, `Ing_Mes_PEN`, `Usu_Eje`, `Nom_Ccs`, `Fec_Des`, `Num_Ope`, `Tip_Doc_Cli`, `Num_Doc_Cli`, `Ruc_Emp`, `Niv_Apr_Exp`, `Nom_Cli`, `Ape_Pat`, `Ape_Mat` | Query de solicitudes del periodo (BD Negocio) |
| `SUNAFIL`, `CUL`, `BOLETA` | SI / NO según los documentos encontrados |
| `RUC_CUL` | RUC del empleador tomado del CUL |
| `RUC_SUNAFIL`, `FECHA_INGRESO_SUNAFIL`, `FECHA_VERIFICACION_SUNAFIL` | Datos de la constancia SUNAFIL "Verifica tu Chamba" |
| `OBSERVACION` | OK / Regularizar SUNAFIL / CUL |
| `MENSAJE` | Detalle adicional sobre el RUC |

### SUNAFIL / CUL / BOLETA

**SI** si la frase aparece en cualquier archivo de la solicitud (sin distinguir mayúsculas, tildes ni saltos de línea):

| Columna | Frase buscada |
|---|---|
| SUNAFIL | `VERIFICA TU CHAMBA` |
| CUL | `CERTIFICADO UNICO LABORAL` |
| BOLETA | `BOLETA` |

### OBSERVACION

| Condición | Valor |
|---|---|
| La solicitud tiene **CUL** o **SUNAFIL** | `OK` |
| No tiene ninguno de los dos | `Regularizar SUNAFIL / CUL` |

### RUC_CUL

Se compara `Ruc_Emp` de la solicitud con los RUC de la experiencia laboral del CUL (solo dígitos, así que espacios o
formato numérico no afectan):

1. Si `Ruc_Emp` **coincide** con algún RUC del CUL (vigente o no) → ese RUC.
2. Si no coincide, o `Ruc_Emp` está vacío → **regla de selección**:
   - el registro cuyo campo *Hasta* dice "El empleador no ha registrado información." (empleador vigente);
     si hay varios, el de fecha *Desde* más antigua;
   - si ninguno está vigente, el primer registro de la tabla (el CUL lista primero el más reciente).
3. Sin CUL legible o sin experiencia laboral → vacío.

### RUC_SUNAFIL / FECHA_INGRESO_SUNAFIL / FECHA_VERIFICACION_SUNAFIL

Se leen de las páginas que dicen "VERIFICA TU CHAMBA", aunque la constancia venga dentro de un PDF con otros documentos
(DNI, multas, etc.). Funciona con texto nativo y con OCR (capturas o escaneos) (`extraction/sunafil_parser.py`):

| Columna | De dónde sale |
|---|---|
| `FECHA_VERIFICACION_SUNAFIL` | "Resultado de Verificación": "se le informa que al **07 de mayo de 2026**, ..." → 07/05/2026 |
| `RUC_SUNAFIL` | El RUC de esa misma frase ("... con número de RUC **20555241811**."); si no se lee, el de la primera fila de la tabla |
| `FECHA_INGRESO_SUNAFIL` | Columna "Fecha de Ingreso" de la fila de la tabla con ese RUC |

- Si la solicitud tiene más de una constancia, se usa la de fecha de verificación más reciente.
- Sin constancia SUNAFIL, o si el OCR no logra leer un dato, la celda queda vacía.
- Todas las filas de la tabla se guardan en `documentos/<periodo>/<instancia>/<archivo>_sunafil.json`.

### MENSAJE

| Condición | Valor |
|---|---|
| `Ruc_Emp` vacío y hay CUL | `Regularizar CUL - ANALITICA` |
| `Ruc_Emp` empieza con **10** (persona natural / independiente, no figura en planilla) y no coincide con ningún RUC del CUL, haya o no CUL | `Independiente - RUC 10` |
| Cualquier otro caso | vacío |

### Casos especiales

- **Solicitud sin archivos** (sin registros en BD, todos excluidos por nombre o ninguno se pudo copiar): igual se
  registra, con SUNAFIL / CUL / BOLETA en NO, `RUC_CUL` vacío y `OBSERVACION` = `Regularizar SUNAFIL / CUL`
  (`MENSAJE` = `Independiente - RUC 10` si `Ruc_Emp` empieza con 10).
- **CUL escaneado o dentro de un Word**: `CUL` = SI (el OCR encuentra el título) y `OBSERVACION` = OK, pero su
  identidad y experiencia laboral no se pueden leer: `RUC_CUL` queda vacío y en el log aparece
  "No se pudo extraer el CUL de ...". Solo se leen los datos de CUL en PDF digital.
- **Solicitud que falla con error** (BD, file server, Excel abierto, etc.): no se escribe en el Excel; aparece en la
  lista "Con error" al final y en `logs/app.log`.
- **BOLETA** se detecta solo por la palabra, así que puede marcar SI si aparece en otro tipo de documento.
- Si un Excel del periodo se generó con una versión anterior (otras columnas), el proceso se detiene y pide
  renombrarlo o eliminarlo.

## JSON de SUNAFIL

`documentos/<periodo>/<instancia>/<archivo>_sunafil.json`, junto al archivo:

```json
{
  "archivo": "documentos/<periodo>/<instancia>/<archivo>.pdf",
  "nombre_original": "...",
  "pagina": 3,
  "ruc": "20...",
  "fecha_ingreso": "dd/mm/aaaa",
  "fecha_verificacion": "dd/mm/aaaa",
  "registros": [{"ruc": "20...", "fecha_ingreso": "dd/mm/aaaa"}]
}
```

## JSON del CUL

`documentos/<periodo>/<instancia>/<archivo>.json`, junto al PDF:

```json
{
  "archivo": "20260807_0003204512_000001.pdf",
  "identidad": {
    "nombres": "...", "apellidos": "...", "nacionalidad": "PERU",
    "tipo_documento": "DOCUMENTO NACIONAL DE IDENTIDAD", "numero_documento": "...",
    "fecha_nacimiento": "dd/mm/aaaa", "domicilio": "...", "fuente": "RENIEC"
  },
  "experiencia_laboral": {
    "fuente": "Planillas Electrónicas",
    "registros": [
      {"ruc": "20...", "razon_social": "...", "desde": "dd/mm/aaaa", "hasta": "El empleador no ha registrado información."},
      {"ruc": "20...", "razon_social": "...", "desde": "dd/mm/aaaa", "hasta": "dd/mm/aaaa"}
    ]
  },
  "nombre_original": "..."
}
```

## Instalación

Requiere Python 3.14, [ODBC Driver 17 for SQL Server](https://learn.microsoft.com/sql/connect/odbc/download-odbc-driver-for-sql-server)
y [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki) con el idioma español (`spa.traineddata` en la
carpeta `tessdata`).

```bash
uv sync          # o: pip install -e .
```

### `.env` (en la raíz del proyecto)

```ini
# BD Riesgo: rutas de archivos por instancia
DB_HOST=SERVIDOR\INSTANCIA
DB_NAME=Riesgo
DB_DRIVER=ODBC Driver 17 for SQL Server
DB_PORT=
# Usuario y contraseña vacíos = autenticación de Windows
DB_USER=
DB_PASSWORD=
DB_EXTRA_PARAMS=

# BD Negocio: solicitudes del periodo
NEGOCIO_DB_HOST=SERVIDOR\INSTANCIA
NEGOCIO_DB_NAME=Negocio
NEGOCIO_DB_PORT=
NEGOCIO_DB_USER=
NEGOCIO_DB_PASSWORD=
NEGOCIO_DB_EXTRA_PARAMS=
# Opcional, por defecto se usa DB_DRIVER
# NEGOCIO_DB_DRIVER=

FILE_SERVER_BASE_PATH=\\servidor\carpeta
FILE_SERVER_TIMEOUT_SECONDS=30
DOWNLOAD_BASE_PATH=./documentos

# Ruta propia de cada PC (carpeta de instalación o el tesseract.exe)
PATH_TESSERACT=C:\Users\<usuario>\AppData\Local\Tesseract-OCR
OCR_LANG=spa

# Opcionales
RESULTADOS_DIR=resultados
LOG_DIR=logs
LOG_LEVEL=INFO
```

`.env`, `documentos/`, `logs/` y `resultados/` no se suben al repositorio.
