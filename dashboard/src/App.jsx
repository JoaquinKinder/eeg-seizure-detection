import { BrowserRouter, Routes, Route, NavLink, Navigate } from 'react-router-dom'
import PredictPage from './pages/PredictPage'
import ProcessingPage from './pages/ProcessingPage'
import HistoryPage from './pages/HistoryPage'
import styles from './App.module.css'

export default function App() {
  return (
    <BrowserRouter>
      <div className={styles.layout}>
        {/* Navbar Superior */}
        <nav className={styles.navbar}>
          <div className={styles.brand}>
            <div className={styles.brandIcon}>⚕️</div>
            <div className={styles.brandText}>EEG Analyzer</div>
          </div>
          
          <div className={styles.navLinks}>
            <NavLink 
              to="/processing" 
              className={({ isActive }) => `${styles.navLink} ${isActive ? styles.activeLink : ''}`}
            >
              Procesamiento de Señal
            </NavLink>
            <NavLink 
              to="/history" 
              className={({ isActive }) => `${styles.navLink} ${isActive ? styles.activeLink : ''}`}
            >
              Registros Históricos
            </NavLink>
            <NavLink 
              to="/predict" 
              className={({ isActive }) => `${styles.navLink} ${isActive ? styles.activeLink : ''}`}
            >
              Predicción de Crisis
            </NavLink>
          </div>
        </nav>

        {/* Contenido Principal */}
        <main className={styles.mainContent}>
          <Routes>
            <Route path="/" element={<Navigate to="/processing" replace />} />
            <Route path="/processing" element={<ProcessingPage />} />
            <Route path="/history" element={<HistoryPage />} />
            <Route path="/predict" element={<PredictPage />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}
