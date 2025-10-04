import React, { useState, useRef } from 'react';
// IMPORTANTE: Puedes reutilizar (o adaptar) los estilos CSS de SpeechRecorder.css 
// o crear un archivo nuevo como AudioConverter.css
import './upload.css'; 

const UploadPage = () => {
    // Estado para manejar el archivo seleccionado y el texto de resultado
    const [selectedFile, setSelectedFile] = useState(null);
    const [fileName, setFileName] = useState('Ningún archivo seleccionado');
    const [transcript, setTranscript] = useState('En esta sección se mostrará el texto transcrito.');
    const fileInputRef = useRef(null); // Referencia para el input de archivo oculto

    // --- Manejo de Archivo Seleccionado ---

    const handleFileChange = (event) => {
        const file = event.target.files[0];
        if (file) {
            setSelectedFile(file);
            setFileName(file.name);
        }
    };

    const handleDrop = (event) => {
        event.preventDefault();
        const file = event.dataTransfer.files[0];
        if (file && file.type.startsWith('audio/')) { // Validación simple de tipo de archivo
            setSelectedFile(file);
            setFileName(file.name);
        } else {
            alert("Por favor, arrastre un archivo de audio válido.");
        }
    };

    const handleDragOver = (event) => {
        event.preventDefault(); // Necesario para permitir el "drop"
    };

    // --- Lógica de Botones ---

    const handleRealizarTranscripcion = () => {
        if (!selectedFile) {
            alert("Por favor, selecciona un archivo de audio primero.");
            return;
        }
        
        // TODO: Aquí iría la lógica real para enviar el archivo 
        // a un servidor (backend) que maneje la transcripción. 
        setTranscript(`Iniciando transcripción de: ${fileName}...\n(La lógica de backend es necesaria para el procesamiento real)`);
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
            <div className="left-panel">
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
                        accept="audio/*" // Solo acepta archivos de audio
                        onChange={handleFileChange} 
                        ref={fileInputRef}
                        style={{ display: 'none' }}
                    />
                    
                    <div className="file-selector-row">
                        <button 
                            className="btn-select-file" 
                            onClick={() => fileInputRef.current.click()}
                        >
                            Elegir desde el ordenador
                        </button>
                        <span className="file-name-display">{fileName}</span>
                    </div>
                </div>

                <div className="controls">
                    <button 
                        className="btn btn-clear" 
                        onClick={handleClear}
                    >
                        Borrar
                    </button>
                    
                    <button 
                        className="btn btn-transcribe" 
                        onClick={handleRealizarTranscripcion}
                        disabled={!selectedFile} // Deshabilitado si no hay archivo
                    >
                        Realizar transcripción
                    </button>
                    
                    <button 
                        className="btn btn-convert" 
                        onClick={handleConvertVideo}
                    >
                        Convertir video a MP3
                    </button>
                </div>
            </div>

            <div className="right-panel">
                <h3 className="result-title">Resultado:</h3>
                <div className="result-box">
                    {transcript}
                </div>
            </div>
        </div>
    );
};

export default UploadPage;