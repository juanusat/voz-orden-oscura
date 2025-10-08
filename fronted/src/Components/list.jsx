import React, { useState, useEffect } from 'react';
import './list.css'; 

const ListPage = () => {
    const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:5702/api';
    const [files, setFiles] = useState([]);

    useEffect(() => {
        let mounted = true;
        const fetchList = async () => {
            try {
                const res = await fetch(`${API_BASE}/transcriptions?status=completed&limit=100`);
                if (!res.ok) throw new Error(`Failed to fetch: ${res.status}`);
                const json = await res.json();
                // json is an array of {id, filename, status, duration_seconds, created_at}
                if (mounted) setFiles(json.map(item => ({
                    id: item.id,
                    name: item.filename || item.id,
                    date: item.created_at || '',
                    raw: item,
                })));
            } catch (e) {
                console.error(e);
            }
        };
        fetchList();
        return () => { mounted = false };
    }, []);

    const handleDownload = (file) => {
        // file may include raw.word_doc_path with a server path; build download URL
        const raw = file.raw || {};
        let downloadUrl = null;
        if (raw.word_doc_path) {
            // word_doc_path may be a full path like "generated/docs/<id>.docx"
            const parts = raw.word_doc_path.split(/[/\\]/g);
            const filename = parts[parts.length - 1];
            downloadUrl = `${API_BASE}/transcriptions/download/${encodeURIComponent(filename)}`;
        } else {
            // no docx path known; assume this is an upload (audio) and use uploads/download
            const safeName = file.name;
            downloadUrl = `${API_BASE.replace(/\/transcriptions$/, '')}/uploads/download/${encodeURIComponent(safeName)}`;
        }
        window.open(downloadUrl, '_blank');
    };

    const generateAndDownload = async (file) => {
        const raw = file.raw || {};
        const id = raw.id;
        if (!id) {
            alert('No transcription id available');
            return;
        }
        try {
            const res = await fetch(`${API_BASE}/transcriptions/${encodeURIComponent(id)}/docx`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({}),
            });
            if (!res.ok) {
                const err = await res.json().catch(()=>null);
                throw new Error(err && err.error ? err.error : `status ${res.status}`);
            }
            const json = await res.json();
            // expected { docx_url: outpath }
            let url = json && json.docx_url;
            if (url) {
                // If docx_url is a path like generated/docs/<file>, construct download endpoint
                const parts = url.split(/[/\\]/g);
                const filename = parts[parts.length - 1];
                const downloadUrl = `${API_BASE}/transcriptions/download/${encodeURIComponent(filename)}`;
                window.open(downloadUrl, '_blank');
            } else {
                // fallback: try to download by id
                const downloadUrl = `${API_BASE}/transcriptions/download/${encodeURIComponent(id)}.docx`;
                window.open(downloadUrl, '_blank');
            }
        } catch (e) {
            console.error(e);
            alert('Error generating docx: ' + (e.message || e));
        }
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
                                        className="btn-gendoc" 
                                        onClick={() => generateAndDownload(file)}
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