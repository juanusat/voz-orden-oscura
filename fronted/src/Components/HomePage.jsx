import React, { useState, useEffect, useRef } from 'react';
// IMPORTANTE: Asegúrate de tener un archivo CSS para los estilos
import './HomePage.css'; 
import { useNavigate } from 'react-router-dom';

const HomePage = () => {
    // Estado para el texto transcrito y el estado de grabación
    const [isRecording, setIsRecording] = useState(false);
    const [transcript, setTranscript] = useState('En esta sección se mostrará el texto transcrito.');
    const [isTranscribing, setIsTranscribing] = useState(false);
    const [savedTranscriptionId, setSavedTranscriptionId] = useState(null);
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
    const navigate = useNavigate();
    const mediaRecorderRef = useRef(null);
    const mediaStreamRef = useRef(null);
    const chunksRef = useRef([]);

    const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:5702/api';

    const uploadAndTranscribe = async (blob, filename) => {
        try {
            const form = new FormData();
            form.append('file', blob, filename);
            const upRes = await fetch(`${API_BASE}/uploads`, { method: 'POST', body: form });
            if (!upRes.ok) throw new Error(`Upload failed: ${upRes.status}`);
            const upJson = await upRes.json();
            const uploadId = upJson.id;
            // Request transcription (try synchronous endpoint first)
            const tRes = await fetch(`${API_BASE}/transcriptions`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ upload_id: uploadId }),
            });
            if (!tRes.ok) {
                const err = await tRes.json().catch(()=>null);
                throw new Error(`Transcription request failed: ${tRes.status} ${err && err.error ? err.error : ''}`);
            }
            const tJson = await tRes.json();

            // If sync endpoint returned completed text, use it. Otherwise poll for completion.
            const transcriptionId = tJson.id || tJson.task_id || null;
            if (tJson.status === 'completed' && tJson.text) {
                setTranscript(tJson.text);
                // keep user on HomePage; record exists in backend and will appear in Listado
                setSavedTranscriptionId(tJson.id || null);
                setIsTranscribing(false);
                setSavedTranscriptionId(tJson.id || null);
                return;
            }

            if (!transcriptionId) {
                throw new Error('No transcription id returned');
            }

            // Poll until status is completed (timeout 60s)
            const poll = async () => {
                const start = Date.now();
                while (Date.now() - start < 60000) {
                    try {
                        const r = await fetch(`${API_BASE}/transcriptions/${encodeURIComponent(transcriptionId)}`);
                        if (r.ok) {
                            const j = await r.json();
                            if (j.status === 'completed' && j.text) {
                                return j;
                            }
                            if (j.status === 'failed') {
                                throw new Error(j.error || 'transcription failed');
                            }
                        }
                    } catch (e) {
                        console.warn('Polling error', e);
                    }
                    // wait 2s
                    await new Promise(res => setTimeout(res, 2000));
                }
                throw new Error('Transcription timeout');
            };

            const final = await poll();
            setTranscript(final.text || '');
            setIsTranscribing(false);
            setSavedTranscriptionId(final.id || transcriptionId || null);
        } catch (e) {
            console.error(e);
            setTranscript(`Error: ${e.message}`);
            setIsTranscribing(false);
        }
    };

    const handleStartStop = async () => {
        if (isRecording) {
            // Stop recording
            try {
                mediaRecorderRef.current && mediaRecorderRef.current.stop();
            } catch (e) {
                console.warn('Error stopping recorder', e);
            }
            setIsRecording(false);
            return;
        }

        // Start recording
        try {
            setTranscript('');
            setTimer(0);
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaStreamRef.current = stream;
            const options = {};
            const mediaRecorder = new MediaRecorder(stream, options);
            chunksRef.current = [];
            mediaRecorder.ondataavailable = (e) => {
                if (e.data && e.data.size > 0) chunksRef.current.push(e.data);
            };
            mediaRecorder.onstop = async () => {
                // assemble blob
                const blob = new Blob(chunksRef.current, { type: chunksRef.current[0]?.type || 'audio/webm' });
                const now = new Date();
                const pad = (n) => String(n).padStart(2, '0');
                const fname = `Grabación - ${now.getFullYear()}-${pad(now.getMonth()+1)}-${pad(now.getDate())}_${pad(now.getHours())}-${pad(now.getMinutes())}-${pad(now.getSeconds())}.webm`;
                // stop tracks
                try { mediaStreamRef.current && mediaStreamRef.current.getTracks().forEach(t=>t.stop()); } catch(e){}
                setIsTranscribing(true);
                await uploadAndTranscribe(blob, fname);
            };
            mediaRecorder.start();
            mediaRecorderRef.current = mediaRecorder;
            setIsRecording(true);
        } catch (e) {
            console.error('Could not start recording', e);
            alert('No se pudo iniciar la grabación: ' + (e.message || e));
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
            <div className="left-panel-home">
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
                        className="btn-home btn-clear" 
                        onClick={handleClear}
                        disabled={isRecording || isTranscribing} // No se puede borrar mientras graba o transcribe
                    >
                        Borrar
                    </button>
                    <button 
                        className={`btn-home btn-record ${isRecording ? 'recording' : ''}`}
                        onClick={handleStartStop}
                        disabled={isTranscribing}
                    >
                        {isRecording ? 'Detener' : 'Grabar'}
                    </button>
                </div>
            </div>

            <div className="right-panel-home">
                <h3 className="result-title">Resultado:</h3>
                <div className="result-box-home">
                    {isTranscribing ? (<div><strong>Transcribiendo...</strong></div>) : null}
                    {transcript}
                </div>
            </div>
        </div>
    );
};

export default HomePage;