// src/main.jsx (MODIFICADO)

import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
//import './index.css'
import App from './App.jsx'
// import Header from './Components/Header.jsx' <-- ¡Eliminado de aquí!

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App /> {/* Solo renderizamos App */}
  </StrictMode>,
)