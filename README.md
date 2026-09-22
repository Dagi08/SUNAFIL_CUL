validacion-cul-sunafil/
├── config/
│   ├── settings.py          # rutas base, credenciales DB, timeouts, flags de entorno
│   └── logging_config.py    # configuración centralizada de logging (formato, nivel, rotación)
│
├── db/
│   ├── connection.py        # conexión a la BD donde está la instancia del cliente
│   └── queries.py           # query para obtener instancia → ruta de archivos en file server
│
├── file_access/
│   ├── file_locator.py      # dado instancia, resuelve ruta(s) en file server
│   └── file_reader.py       # lee archivo crudo según extensión (PDF/PNG/DOCX) → bytes/páginas
│
├── extraction/
│   ├── base_extractor.py    # interfaz abstracta: extract(page) -> texto/estructura
│   ├── ocr_extractor.py     # implementación actual (pytesseract/PaddleOCR + pdfplumber/PyMuPDF)
│   └── donut_extractor.py   # placeholder a futuro, misma interfaz que base_extractor
│
├── classification/
│   ├── base_classifier.py   # interfaz abstracta: classify(texto_o_output) -> tipo/campos
│   ├── rule_classifier.py   # reglas/regex actuales (CUL/SUNAFIL/OTRO)
│   └── llm_classifier.py    # placeholder si más adelante usas Claude API
│
├── pipeline/
│   ├── orchestrator.py      # orquesta: instancia → ruta → lectura → extracción → clasificación → log/BD
│   └── segmenter.py         # agrupa páginas consecutivas en sub-documentos
│
├── models/
│   └── document.py          # dataclasses: Documento, Pagina, ResultadoClasificacion, etc.
│
├── storage/
│   ├── log_writer.py        # escribe el .log preliminar de lo extraído por archivo/página
│   └── result_writer.py     # a futuro: inserción en Snowflake/SQL Server
│
├── scripts/
│   └── run_batch.py         # entry point: recorre instancias, llama al orchestrator
│
├── logs/                    # salida de .log generados (no versionar)
│
├── tests/
│   ├── test_extraction.py
│   ├── test_classification.py
│   └── test_segmenter.py
│
├── requirements.txt
└── README.md
