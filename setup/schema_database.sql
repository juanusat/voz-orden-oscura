-- Schema PostgreSQL para Voz-Orden-Oscura
-- Basado en docs/SPEC.md
-- Incluye tablas: uploads, transcriptions
-- Recomendación: ejecutar en una base de datos PostgreSQL 12+

-- Habilitar extensiones útiles
CREATE EXTENSION IF NOT EXISTS pgcrypto; -- gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS "uuid-ossp"; -- opcional, para uuid_generate_v4()

-- Tabla: uploads
CREATE TABLE IF NOT EXISTS uploads (
	id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
	filename TEXT NOT NULL,
	content_type TEXT NOT NULL,
	size_bytes BIGINT NOT NULL DEFAULT 0,
	stored_at TEXT NOT NULL, -- ruta o ubicación relativa en disco
	original_path TEXT, -- ruta al archivo original si difiere
	is_video BOOLEAN NOT NULL DEFAULT FALSE,
	metadata JSONB, -- metadatos detectados (ffprobe, etc.)
	created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
	updated_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_uploads_filename ON uploads (filename);
CREATE INDEX IF NOT EXISTS idx_uploads_created_at ON uploads (created_at);

-- Tabla: transcriptions
CREATE TABLE IF NOT EXISTS transcriptions (
	id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
	upload_id UUID REFERENCES uploads(id) ON DELETE SET NULL,
	filename TEXT, -- nombre original o generado
	content_type TEXT,
	audio_path TEXT, -- ruta local al audio convertido/normalizado
	duration_seconds DOUBLE PRECISION,
	language VARCHAR(8), -- ISO-639-1 o similar
	text TEXT, -- transcripción completa
	segments JSONB, -- lista de segmentos: [{start, end, text, speaker_id}, ...]
	speakers JSONB, -- {speaker_id: {label, confidence}}
	status VARCHAR(32) NOT NULL DEFAULT 'queued', -- queued|processing|completed|failed
	error TEXT,
	transcriber TEXT,
	word_doc_path TEXT,
	created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
	updated_at TIMESTAMPTZ
);

-- Índices recomendados
CREATE INDEX IF NOT EXISTS idx_transcriptions_status ON transcriptions (status);
CREATE INDEX IF NOT EXISTS idx_transcriptions_created_at ON transcriptions (created_at);
CREATE INDEX IF NOT EXISTS idx_transcriptions_upload_id ON transcriptions (upload_id);

-- Función auxiliar para actualizar updated_at
CREATE OR REPLACE FUNCTION set_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
	NEW.updated_at = now();
	RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers para mantener updated_at
CREATE TRIGGER trg_uploads_updated_at
BEFORE UPDATE ON uploads
FOR EACH ROW
EXECUTE FUNCTION set_updated_at_column();

CREATE TRIGGER trg_transcriptions_updated_at
BEFORE UPDATE ON transcriptions
FOR EACH ROW
EXECUTE FUNCTION set_updated_at_column();

-- Opcional: vista resumida de transcripciones para listados
CREATE OR REPLACE VIEW transcriptions_list AS
SELECT
  id,
  COALESCE(filename, uploads.filename) AS filename,
  status,
  duration_seconds,
  created_at
FROM transcriptions
LEFT JOIN uploads ON transcriptions.upload_id = uploads.id
ORDER BY created_at DESC;

-- Política de retención/limpieza (ejemplo): borrar archivos marcados como failed antiguos
-- Esto es un ejemplo y se debe ejecutar manualmente o programar en cron/job
-- DELETE FROM transcriptions WHERE status = 'failed' AND created_at < now() - interval '90 days';

-- Comentarios adicionales:
-- - Se recomienda crear roles/privilegios específicos para la aplicación.
-- - Para integridad avanzada y search full-text, considerar índices GIN sobre columnas JSONB y tsvector sobre `text`.

