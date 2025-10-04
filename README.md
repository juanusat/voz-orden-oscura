Voz-Orden-Oscura backend

Instalaci\u00f3n y uso r\u00e1pido:

1) Crear un entorno virtual e instalar dependencias:

```cmd
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

2) Ejecutar la aplicaci\u00f3n:

```cmd
python -m backend.run
```

La API se expondr\u00e1 en http://localhost:5702/api

Endpoints principales:
- POST /api/uploads
- GET /api/transcriptions
- POST /api/transcriptions
- POST /api/transcriptions/async
- POST /api/transcriptions/{id}/docx

Notas:
- Configure DATABASE_URL para usar PostgreSQL si lo desea.
- Aseg\u00farse de tener `ffmpeg` instalado y accesible desde PATH o configurar FFMPEG_BIN.
