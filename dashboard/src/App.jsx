import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom'
import DashboardPage from './pages/DashboardPage'
import PredictPage from './pages/PredictPage'
import styles from './App.module.css'

export default function App() {
  return (
    <BrowserRouter>
      <div className={styles.layout}>
        {/* Barra de Navegación */}
        <nav className={styles.sidebar}>
          <div className={styles.brand}>
            <div className={styles.brandIcon}>🧠</div>
            <div className={styles.brandText}>NeuroDash</div>
          </div>
          
          <div className={styles.navLinks}>
            <NavLink 
              to="/" 
              className={({ isActive }) => `${styles.navLink} ${isActive ? styles.activeLink : ''}`}
              end
            >
              📊 Reportes Históricos
            </NavLink>
            <NavLink 
              to="/predict" 
              className={({ isActive }) => `${styles.navLink} ${isActive ? styles.activeLink : ''}`}
            >
              🔍 Inferencia en Vivo
            </NavLink>
          </div>
        </nav>

        {/* Contenido Principal */}
        <main className={styles.mainContent}>
          <Routes>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/predict" element={<PredictPage />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}
