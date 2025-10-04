# SPEC for Voz-Orden-Oscura — Extensiones y utilidades añadidas

## Resumen de cambios (alto nivel)
- **Todas las transcripciones se persisten en una base de datos** (registro completo con metadatos, timestamps, hablantes, estado de tarea).
- El **backend ofrece endpoints** para listar/consultar transcripciones guardadas y para generar/descargar una transcripción en formato **Word (.docx)** a pedido.
- El backend **acepta cualquier archivo multimedia** (audio/video). Si es necesario, **convierte** al formato de audio requerido (wav/16k/mono u otro configurable) antes de procesar la transcripción.
- El frontend puede:
  - **Grabar desde el micrófono** y enviar la grabación como `Blob`.
  - **Subir archivos de audio o video**; el video será procesado extrayendo su pista de audio en backend.
- Se documentan nuevos campos DB, endpoints, flujo de conversión, y ejemplos de uso.

---

## Cambios en la arquitectura / componentes nuevos

### Backend (Flask)
- Nuevas responsabilidades:
  - Conversión automática de formatos (ffmpeg).
  - Extracción de audio desde video (ffmpeg).
  - Normalización (sample rate, canales).
  - Persistencia de transcripciones y tareas en DB (SQLite por defecto, configurable).
  - Generación on-demand de archivos Word (.docx).
  - Recepción de blobs desde frontend (grabaciones en navegador).
- Nuevos módulos sugeridos dentro de `app/`:
  - `services/convert.py` — wrappers de ffmpeg para convertir/extraer/normalizar.
  - `services/docx_generator.py` — generación de .docx (python-docx).
  - `models/transcription_model.py` — ORM/serializador para persistencia.
  - `blueprints/transcriptions_api.py` — endpoints CRUD y descarga .docx.

### Frontend (React + Vite)
- Nuevas capacidades UI:
  - Componente `MicrophoneRecorder.jsx` para grabar y enviar Blob.
  - UI para listar transcripciones guardadas y descargar `.docx`.
  - Selector para subir audio o video (video -> backend extrae audio).

---

## Esquema de datos y base de datos

### Entidad principal: Transcription
- **Tabla**: `transcriptions`
- Campos sugeridos:
  - `id` (UUID, PK)
  - `upload_id` (UUID, referencia al archivo original)
  - `filename` (string) — nombre original o generado
  - `content_type` (string) — MIME del original (audio/* o video/*)
  - `audio_path` (string) — ruta local al audio ya convertido/normalizado
  - `duration_seconds` (float)
  - `language` (string, ISO-639-1)
  - `text` (text) — transcripción completa
  - `segments` (JSON) — lista de segmentos con `{start, end, text, speaker_id}`
  - `speakers` (JSON) — metadatos de hablantes si aplica `{speaker_id: {label, confidence}}`
  - `status` (string) — `queued|processing|completed|failed`
  - `error` (text, nullable)
  - `created_at` (datetime UTC)
  - `updated_at` (datetime UTC)
  - `transcriber` (string) — e.g., `faster_whisper`
  - `word_doc_path` (string, nullable) — ruta del .docx generado si existe
- Índices: `created_at`, `status`, `upload_id`

### Entidad auxiliar: Uploads (opcional)
- `uploads` con metadatos del archivo original:
  - `id`, `filename`, `content_type`, `size`, `stored_at`, `original_path`

---

## Nuevos endpoints HTTP (API)
Base URL: `http://localhost:5702/api`

### A) Gestión de uploads (sin cambios importantes, + acepta blobs/video)
- `POST /api/uploads`
  - Acepta `multipart/form-data` con `file` o envíos `blob` (campo `file`) desde navegador.
  - Opcional: `language`.
  - Backend: valida, guarda en `uploads/`, detecta MIME, si video → marca `is_video` y extrae audio.
  - Response: metadata del upload (id, filename, content_type, size, uploaded_at).

### B) Listar transcripciones (persistidas)
- `GET /api/transcriptions`
  - Query params opcionales: `status`, `limit`, `offset`, `from_date`, `to_date`
  - Response: lista paginada de transcripciones con campos clave (`id`, `filename`, `status`, `duration_seconds`, `created_at`).

### C) Obtener transcripción (detallada)
- `GET /api/transcriptions/{transcription_id}`
  - Response 200:
  ```json
  {
    "id": "...",
    "filename": "...",
    "status": "completed",
    "text": "...",
    "duration_seconds": 123.4,
    "segments": [ { "start": 0.0, "end": 3.2, "text": "Hola", "speaker": "spk0" } ],
    "speakers": { "spk0": { "label": null, "confidence": 0.95 } },
    "created_at": "..."
  }
  ```

### D) Solicitar transcripción síncrona (como antes)
- `POST /api/transcriptions`
  - Body: `{ "upload_id": "uuid" }`
  - Backend: asegura que `audio_path` existe (convierte/extract si necesario), procesa (faster-whisper pipeline), guarda en tabla `transcriptions` (status/segments/text), devuelve resultado final.
  - Response 200: transcripción guardada (idéntica al GET).

### E) Solicitar transcripción asíncrona (cola)
- `POST /api/transcriptions/async`
  - Body: `{ "upload_id": "uuid", "callback_url": "... (opcional)" }`
  - Response 202: `{ "task_id": "uuid", "status": "queued" }`
  - Worker: actualiza `transcriptions.status` según avance; al finalizar completa `text`, `segments`, `speakers`, `word_doc_path` si se generó.

### F) Generar/Descargar Word (.docx)
- `POST /api/transcriptions/{transcription_id}/docx`
  - Genera (si no existe) el `.docx` con la transcripción formateada y devuelve metadata: `{ "docx_url": "/downloads/..." }`
  - Opcional: parámetros de formato en body (`include_timestamps`, `speaker_labels`, `title`, `author`)
  - Response 201 (o 200 si ya existe) con ruta/URL de descarga.
- `GET /api/downloads/docx/{filename}` (o servir archivos estáticos desde nginx)
  - Devuelve el archivo `.docx` para descargar

### G) Upload directo de blob desde navegador
- `POST /api/uploads/blob`
  - Acepta `Content-Type: application/octet-stream` o `multipart/form-data` con Blob y campos `filename`, `content_type`
  - Mismo flujo de almacenamiento y conversión que `POST /api/uploads`

---

## Flujo detallado de procesamiento (upload → docx)

1. Cliente sube archivo (audio/video) o envía blob del micrófono.
2. Backend guarda el archivo en `uploads/` y crea registro en `uploads` DB.
3. Backend detecta tipo MIME:
   - Si video: ejecuta extracción de audio con `ffmpeg` → guarda `audio_path`.
   - Si audio pero no en formato esperado: convierte/normaliza (sample rate, canales, codec) → guarda `audio_path`.
4. Crea/actualiza registro en `transcriptions` con `status = queued`.
5. Si petición síncrona: el proceso de transcripción se ejecuta inmediatamente; si async: encola tarea en worker (Redis + RQ/Celery).
6. Pipeline de transcripción (`faster_whisper`):
   - Aplica VAD (e.g., `webrtcvad`) para segmentación.
   - Extrae embeddings de voz por segmento (Silero o pyannote embeddings).
   - Ejecuta `faster-whisper` por chunk para obtener texto y timestamps.
   - Clusteriza embeddings para obtener `speaker_id` por segmento.
   - Consolida segmentos, asigna etiquetas de hablante, calcula duración.
7. Guarda en DB: `text`, `segments` (JSON), `speakers`, `status = completed`, `updated_at`.
8. Si se pidió generación de `.docx`:
   - `docx_generator` formatea la transcripción (opcional: timestamps y etiquetas) y guarda `word_doc_path`.
9. Si `callback_url` fue provisto para async, backend hace POST con resultado (o URL para descargar .docx).

---

## Conversión y extracción (implementación)

### `services/convert.py` (responsabilidades)
- `ensure_audio(path_in: str) -> path_out: str`
  - Detecta MIME (ffprobe), si es video extrae audio:
    - `ffmpeg -i input.mp4 -vn -acodec pcm_s16le -ar 16000 -ac 1 output.wav`
  - Si audio y no cumple requerimientos (sampling, mono, codec) → convertir/normalizar:
    - `ffmpeg -i input.xxx -acodec pcm_s16le -ar 16000 -ac 1 output.wav`
  - Devuelve ruta a audio normalizado listo para ASR.
- Manejar errores y límites (tamaño, duración máxima configurada).

### Recomendaciones ffmpeg
- Formato objetivo por defecto: `wav`, PCM S16LE, 16 kHz, mono (para compatibilidad y buena latencia).
- Permitir configurar `SAMPLE_RATE`, `CHANNELS`, `FORMAT` en `config.py`.

---

## Generación de .docx

### `services/docx_generator.py`
- Dependencia: `python-docx`
- API:
  - `generate_docx(transcription: TranscriptionModel, output_path: str, options: dict) -> str`
    - `options` puede incluir:
      - `include_timestamps: bool`
      - `speaker_labels: bool`
      - `title: str`, `author: str`
- Formato sugerido en el documento:
  - Portada con título, autor, fecha y duración.
  - Cuerpo con bloques:
    - Si `speaker_labels` habilitado: `Speaker 1 [00:00:00 - 00:00:10]: Texto...`
    - Si no: texto continuo con timestamps en paréntesis o al final de párrafo.
- Guardar archivo en `generated/` o `storage/docs/` y persistir `word_doc_path` en DB.

---

## Frontend: grabación desde micrófono y envío

### Componente sugerido: `MicrophoneRecorder.jsx`
- Usa Web API `MediaRecorder`:
  - `navigator.mediaDevices.getUserMedia({ audio: true })`
  - `const mediaRecorder = new MediaRecorder(stream)`
  - Capturar `dataavailable` event y concatenar blobs.
- Al terminar la grabación:
  - Crear `FormData()`, `form.append('file', blob, 'recording.webm')` o `application/octet-stream`
  - Enviar a `POST /api/uploads` o `POST /api/uploads/blob`
- Nota: algunos navegadores generan `webm`/`ogg` blobs; backend debe convertir (ffmpeg) a formato objetivo.

### Consideraciones
- Pedir permisos de micrófono de forma clara en UI.
- Mostrar estado de grabación y progreso de upload/transcripción.
- Posible previsualización/reproducción del blob antes de enviar.

---

## Soporte de video (subida y extracción de audio)
- Frontend permite seleccionar archivos `video/*`.
- Backend, en `services/convert.py`, detecta video y ejecuta extracción de audio como se describió.
- El sistema guarda tanto `original_path` (video) como `audio_path` (extraído) para trazabilidad.

---

## Variables de entorno adicionales (para nuevas utilidades)
- `DATABASE_URL=sqlite:///data.db` (o PostgreSQL en producción)
- `FFMPEG_BIN=/usr/bin/ffmpeg` (ruta a ffmpeg)
- `MAX_AUDIO_DURATION_SECONDS=7200` (2 horas, ej. configurable)
- `DOCX_STORAGE_PATH=./generated/docs`
- `TRANSCRIPTION_WORKER=celery|rq` (qué sistema de colas usar)
- `REDIS_URL=redis://localhost:6379/0` (si se usa cola)
- `ALLOW_VIDEO_UPLOADS=true|false` (configurable)
- `ALLOWED_MIME_TYPES=audio/*,video/*` (lista)
- `DEFAULT_SAMPLE_RATE=16000`
- `DEFAULT_CHANNELS=1`

---

## Dependencias adicionales recomendadas
Agregar a `requirements.txt` o a la configuración del entorno:
```
python-docx
ffmpeg-python        # opcional wrapper
ffprobe/ffmpeg       # binarios instalados en el sistema
celery or rq         # worker queue
redis                # si usa redis
sqlalchemy or flask-sqlalchemy
alembic              # migraciones si usas postgres
python-magic         # detectar MIME
pydantic             # validación alternativa
```

Ya listadas anteriormente: `faster-whisper`, `webrtcvad`, `silero-vad`, `pyannote-audio` (opcional).

---

## Endpoints y flujos de ejemplo (ejemplos concretos)

### Subir blob grabado por navegador (Ejemplo fetch)
```js
// blob: obtén del MediaRecorder
const form = new FormData();
form.append('file', blob, 'recording.webm'); // o .ogg/.wav según navegador
form.append('language', 'es');

fetch('http://localhost:5702/api/uploads', {
  method: 'POST',
  body: form
})
  .then(res => res.json())
  .then(data => {
    // data.id -> iniciar transcripción síncrona o async
  });
```

### Subir video y solicitar transcripción async
```js
// upload video via multipart then request transcription asyncrona
// 1) upload
// 2) POST /api/transcriptions/async { upload_id: '...' , callback_url: 'https://...' }
```

### Descargar .docx de una transcripción existente
```js
// Solicitar creación (si no existe)
POST /api/transcriptions/{id}/docx
// Recibe { docx_url: "/downloads/docx/...." }
// Luego GET la URL para descargar
```

---

## Testing (nuevas pruebas sugeridas)
- Tests unitarios:
  - `convert.ensure_audio` con diferentes formatos (mp3, m4a, mp4, webm).
  - `docx_generator` produce archivos .docx válidos con distintas opciones.
  - Persistencia DB: crear/leer transcriptions.
- Tests de integración:
  - Upload + extracción de audio de un video + transcripción end-to-end (mockear ASR para velocidad).
  - Blob upload desde frontend simulado (requests con octet-stream) → procesar.
- Tests de carga:
  - Subir varios archivos concurrentes y comprobar que la cola procesa y DB se mantiene consistente.

---

## Consideraciones de seguridad y límites adicionales
- **Validación de archivos**: comprobar extensiones y MIME; escanear posibles archivos maliciosos.
- **Límites de duración y tamaño**: rechazar uploads que excedan `MAX_AUDIO_DURATION_SECONDS` o `MAX_CONTENT_LENGTH`.
- **Sanitizar metadata**: no ejecutar comandos shell con inputs no validados (usar ffmpeg-python o subprocess con args seguros).
- **Protección contra SSRF**: validar `callback_url` (permitir solo dominios/ips permitidos en producción).
- **Autenticación y autorización**: endpoints que devuelven transcripciones deben requerir token si la aplicación no es pública.
- **Permisos de archivos**: asegurar que carpetas donde se escriben no expongan archivos arbitrarios; servir descargas mediante rutas controladas.

---

## Ejemplo minimal de modelo ORM (SQLAlchemy) — esquema resumido
```py
from sqlalchemy import Column, String, Float, DateTime, Text, JSON
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
import uuid

class Transcription(Base):
    __tablename__ = "transcriptions"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    upload_id = Column(String, index=True)
    filename = Column(String)
    content_type = Column(String)
    audio_path = Column(String)
    duration_seconds = Column(Float)
    language = Column(String(8))
    text = Column(Text)
    segments = Column(JSON)
    speakers = Column(JSON)
    status = Column(String, default="queued", index=True)
    error = Column(Text, nullable=True)
    transcriber = Column(String)
    word_doc_path = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

---

## Notas finales y próximos pasos
- Esta especificación amplía la original para soportar:
  - Persistencia de todas las transcripciones;
  - Generación y descarga de `.docx`;
  - Aceptación de blobs grabados por navegador y archivos de video (con extracción automática de audio);
  - Conversión automática de formatos.
- La elección de `faster-whisper` se mantiene como motor ASR.
- Puedo ahora:
  - Generar los blueprints Flask mínimos (endpoints CRUD, upload, transcribe, docx) con ejemplos de implementación de `convert.py` y `docx_generator.py`.
  - Crear migraciones/seed para la base de datos y ejemplos de tests.
  - Generar el componente React `MicrophoneRecorder.jsx` listo para usar con el endpoint de uploads.
