import { Link } from 'react-router-dom';
import OrdenOscura from '/ORDEN-OSCURA.svg'; // Asegúrate de que la ruta sea correcta
import './Header.css'; // Opcional: para estilos
import KeyboardVoiceIcon from '@mui/icons-material/KeyboardVoice';
import DriveFolderUploadIcon from '@mui/icons-material/DriveFolderUpload';
import ArticleIcon from '@mui/icons-material/Article';

const Header = () => {
    return (
        <header className="app-header">
            <nav>
                <div className='logo-container'>
                    <a href="" target="_blank">
                        <img src={OrdenOscura} className="logo" alt="Vite logo" />
                    </a>
                </div>
                <div className='links-container'>
                    <div className="item-link">
                        <Link to="/">
                        <KeyboardVoiceIcon />Inicio
                        </Link>
                    </div>
                    <div className="item-link">
                        
                        <Link to="/upload">
                        <DriveFolderUploadIcon />Subir</Link>
                    </div>
                    <div className="item-link">
                        <Link to="/list">
                        <ArticleIcon />
                        Listado</Link>
                    </div>
                    
                </div>

            </nav>
        </header>
    );
};

export default Header;