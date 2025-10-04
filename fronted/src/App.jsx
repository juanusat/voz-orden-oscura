// src/App.jsx (MODIFICADO)

import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Header from './Components/Header.jsx'; // Importa el Header

import HomePage from './Components/HomePage.jsx';
import UploadPage from './Components/upload.jsx';
import ListPage from './Components/list.jsx';

function App() {
  return (
    <BrowserRouter> 
      
      <Header />

      <main>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/upload" element={<UploadPage />} />
          <Route path="/list" element={<ListPage />} />
        </Routes>
      </main>
    </BrowserRouter>
  )
}

export default App