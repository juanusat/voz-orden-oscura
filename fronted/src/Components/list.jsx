import React, { useState } from 'react';
import './list.css'; 

// Datos de ejemplo para el listado de archivos
const initialFiles = [
    {
        id: 1,
        name: 'transcripcion_20241219_162644.docx',
        date: '19/12/2024 16:26:44',
        type: 'docx',
    },
    {
        id: 2,
        name: 'audio_reunion_cliente_0501.mp3',
        date: '05/01/2025 10:30:00',
        type: 'mp3',
    },
    {
        id: 3,
        name: 'transcripcion_podcast_epi1.txt',
        date: '01/01/2025 12:00:00',
        type: 'txt',
    },
];

const ListPage = () => {
    // En una aplicación real, estos datos vendrían de una API (fetch)
    const [files, setFiles] = useState(initialFiles);

    const handleDownload = (fileName) => {
        // En un entorno de producción, aquí se realizaría la llamada a la API
        // para obtener el archivo o el enlace de descarga.
        alert(`Iniciando descarga de: ${fileName}`);
        
        // Simulación de descarga: crea un enlace temporal y lo pulsa
        // const downloadUrl = `/api/download/${fileName}`; // URL real del archivo
        // window.open(downloadUrl, '_blank');
    };

    return (
        <div className="list-container">
            <h1>Archivos disponibles</h1>
            
            <div className="files-table-wrapper">
                <table className="files-table">
                    <thead>
                        <tr className="table-header-row">
                            <th className="column-hash">#</th>
                            <th className="column-name">Nombre del Archivo</th>
                            <th className="column-date">Fecha de Creación</th> {/* Añadido para mejor contexto */}
                            <th className="column-actions">Acciones</th>
                        </tr>
                    </thead>
                    <tbody>
                        {files.map((file, index) => (
                            <tr key={file.id} className="table-data-row">
                                <td className="column-hash">{index + 1}</td>
                                <td className="column-name">{file.name}</td>
                                <td className="column-date">{file.date}</td>
                                <td className="column-actions">
                                    <button 
                                        className="btn-download" 
                                        onClick={() => handleDownload(file.name)}
                                    >
                                        Descargar
                                    </button>
                                </td>
                            </tr>
                        ))}
                        
                        {/* Mensaje si no hay archivos */}
                        {files.length === 0 && (
                            <tr>
                                <td colSpan="4" style={{ textAlign: 'center', padding: '20px' }}>
                                    No hay archivos disponibles.
                                </td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default ListPage;