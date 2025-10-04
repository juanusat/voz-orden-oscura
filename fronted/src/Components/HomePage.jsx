import React, { useState, useEffect } from 'react';
// IMPORTANTE: Asegúrate de tener un archivo CSS para los estilos
import './HomePage.css'; 

const HomePage = () => {
    // Estado para el texto transcrito y el estado de grabación
    const [isRecording, setIsRecording] = useState(false);
    const [transcript, setTranscript] = useState('En esta sección se mostrará el texto transcrito.');
    const [timer, setTimer] = useState(0); // Para el cronómetro (segundos)

    // Función para formatear el tiempo (MM:SS)
    const formatTime = (seconds) => {
        const minutes = String(Math.floor(seconds / 60)).padStart(2, '0');
        const secs = String(seconds % 60).padStart(2, '0');
        return `${minutes}:${secs}`;
    };

    // --- Lógica del Cronómetro (Timer) ---
    useEffect(() => {
        let interval = null;
        if (isRecording) {
            interval = setInterval(() => {
                setTimer(prevTime => prevTime + 1);
            }, 1000);
        } else {
            clearInterval(interval);
        }
        
        // Limpieza al desmontar o detener la grabación
        return () => clearInterval(interval);
    }, [isRecording]);


    // --- Funciones de Botones ---

    const handleStartStop = () => {
        setIsRecording(prev => !prev); // Alterna el estado

        // TODO: Aquí irá la lógica de iniciar/detener la Web Speech API
        if (isRecording) {
            // Lógica para DETENER el reconocimiento
        } else {
            // Lógica para INICIAR el reconocimiento
            // También reiniciamos el temporizador y el texto al iniciar
            setTimer(0);
            setTranscript('');
        }
    };

    const handleClear = () => {
        setTranscript('En esta sección se mostrará el texto transcrito.');
        setTimer(0);
        setIsRecording(false);
        // TODO: Lógica para detener cualquier reconocimiento activo si lo hay
    };

    return (
        <div className="speech-container">
            <div className="left-panel">
                <h1 className="title-text">¡Hola! Soy tu asistente virtual de reconocimiento de voz</h1>
                <p className="instruction-text">
                    Haga clic en el botón '{isRecording ? 'Detener grabación' : 'Iniciar grabación'}' para empezar a grabar el audio. 
                    Si desea detenerlo, vuelva a presionar el botón.
                </p>

                <div className="timer-box">
                    Tiempo de grabación
                    <div className="timer-display">{formatTime(timer)}</div>
                </div>

                <div className="controls">
                    <button 
                        className="btn btn-clear" 
                        onClick={handleClear}
                        disabled={isRecording} // No se puede borrar mientras graba
                    >
                        Borrar
                    </button>
                    <button 
                        className={`btn btn-record ${isRecording ? 'recording' : ''}`}
                        onClick={handleStartStop}
                    >
                        {isRecording ? 'Detener grabación' : 'Iniciar grabación'}
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

export default HomePage;