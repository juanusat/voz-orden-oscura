import React, { useState, useRef } from 'react';
// IMPORTANTE: Puedes reutilizar (o adaptar) los estilos CSS de SpeechRecorder.css 
// o crear un archivo nuevo como AudioConverter.css
import './upload.css'; 

const UploadPage = () => {
    // Estado para manejar el archivo seleccionado y el texto de resultado
    const [selectedFile, setSelectedFile] = useState(null);
    const [fileName, setFileName] = useState('Ningún archivo seleccionado');
    const [isVideo, setIsVideo] = useState(false);
    const [detectedMime, setDetectedMime] = useState(null);
    const [transcript, setTranscript] = useState('En esta sección se mostrará el texto transcrito.');
    const fileInputRef = useRef(null); // Referencia para el input de archivo oculto

    // --- Manejo de Archivo Seleccionado ---

    const handleFileChange = (event) => {
        const file = event.target.files[0];
        if (file) {
            setSelectedFile(file);
            setFileName(file.name);
            const mime = file.type || null;
            setDetectedMime(mime);
            setIsVideo(mime ? mime.startsWith('video/') : false);
        }
    };

    const handleDrop = (event) => {
        event.preventDefault();
        const file = event.dataTransfer.files[0];
        if (!file) {
            alert("No se detectó archivo en el arrastre.");
            return;
        }
        // Accept both audio and video
        const mime = file.type || '';
        if (mime.startsWith('audio/') || mime.startsWith('video/')) {
            setSelectedFile(file);
            setFileName(file.name);
            setDetectedMime(mime);
            setIsVideo(mime.startsWith('video/'));
        } else {
            alert("Por favor, arrastre un archivo de audio o video válido.");
        }
    };

    const handleDragOver = (event) => {
        event.preventDefault(); // Necesario para permitir el "drop"
    };

    // --- Lógica de Botones ---

    const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:5702/api';

    const handleRealizarTranscripcion = async () => {
        if (!selectedFile) {
            alert("Por favor, selecciona un archivo de audio primero.");
            return;
        }
        setTranscript(`Iniciando transcripción de: ${fileName}...`);
        try {
            const form = new FormData();
            form.append('file', selectedFile, selectedFile.name);
            // inform backend if this is a video so it can extract audio
            form.append('is_video', isVideo ? '1' : '0');
            if (detectedMime) form.append('original_mime', detectedMime);

            const upRes = await fetch(`${API_BASE}/uploads`, {
                method: 'POST',
                body: form,
            });
            if (!upRes.ok) throw new Error(`Upload failed: ${upRes.status}`);
            const upJson = await upRes.json();
            const uploadId = upJson.id;

            // Request synchronous transcription (blocks until result)
            const tRes = await fetch(`${API_BASE}/transcriptions`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ upload_id: uploadId }),
            });
            if (!tRes.ok) {
                const err = await tRes.json().catch(()=> null);
                throw new Error(`Transcription failed: ${tRes.status} ${err && err.error ? err.error : ''}`);
            }
            const tJson = await tRes.json();
            setTranscript(tJson.text || JSON.stringify(tJson));
        } catch (e) {
            console.error(e);
            setTranscript(`Error: ${e.message}`);
        }
    };

    const handleClear = () => {
        setSelectedFile(null);
        setFileName('Ningún archivo seleccionado');
        setTranscript('En esta sección se mostrará el texto transcrito.');
        // Limpiar el input de archivo si es necesario
        if (fileInputRef.current) {
            fileInputRef.current.value = null;
        }
    };
    
    // Este botón es un placeholder ya que la conversión a MP3 es una función de backend
    const handleConvertVideo = () => {
        alert("La conversión de video a MP3 requiere un servicio de backend.");
    };


    return (
        <div className="converter-container">
            <div className="left-panel-upload">
                <h1 className="title-text">Transforma un archivo de audio a un archivo de texto...</h1>
                <p className="instruction-text">
                    Seleccione el archivo y haga clic en el botón "Realizar transcripción" para realizar la transformación.
                </p>

                {/* Zona de Arrastre y Soltar (Drag and Drop) */}
                <div 
                    className="drag-drop-area"
                    onDrop={handleDrop}
                    onDragOver={handleDragOver}
                >
                    <p>Arrastre el archivo a esta zona o</p>
                    
                    {/* Input de archivo Oculto */}
                    <input 
                        type="file" 
                        accept="audio/*,video/*" // Acepta audio y video
                        onChange={handleFileChange} 
                        ref={fileInputRef}
                        style={{ display: 'none' }}
                    />
                    
                    <div className="file-selector-row">
                        <button 
                            className="bton-select-file" 
                            onClick={() => fileInputRef.current.click()}
                        >
                            Elegir desde el ordenador
                        </button>
                        <span className="file-name-display">{fileName}</span>
                        {detectedMime ? <div style={{ fontSize: 12, color: '#666' }}>Tipo detectado: {detectedMime}{isVideo ? ' (video)' : ' (audio)'}</div> : null}
                    </div>
                </div>

                <div className="controls">
                    <button 
                        className="bton btn-clear-upload" 
                        onClick={handleClear}
                    >
                        Borrar
                    </button>
                    
                    <button 
                        className="bton btn-transcribe-upload" 
                        onClick={handleRealizarTranscripcion}
                        disabled={!selectedFile} // Deshabilitado si no hay archivo
                    >
                        Realizar transcripción
                    </button>
                    
                    <button 
                        className="bton btn-convert-upload" 
                        onClick={handleConvertVideo}
                    >
                        Convertir video a MP3
                    </button>
                </div>
            </div>

            <div className="right-panel-upload">
                <h3 className="result-title">Resultado:</h3>
                <div className="result-box-upload">
                    {transcript}
                </div>
            </div>
        </div>
    );
};

export default UploadPage;