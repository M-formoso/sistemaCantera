import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import LoginPage from '@/pages/auth/LoginPage'
import MainLayout from '@/components/layout/MainLayout'
import ProtectedRoute from '@/components/shared/ProtectedRoute'
import DashboardPage from '@/pages/dashboard/DashboardPage'

// Camiones
import CamionesPage from '@/pages/camiones/CamionesPage'
import CamionFormPage from '@/pages/camiones/CamionFormPage'
import CamionDetailPage from '@/pages/camiones/CamionDetailPage'

// Repuestos
import RepuestosPage from '@/pages/repuestos/RepuestosPage'
import RepuestoFormPage from '@/pages/repuestos/RepuestoFormPage'

// Pesajes
import PesajesPage from '@/pages/pesajes/PesajesPage'
import PesajeFormPage from '@/pages/pesajes/PesajeFormPage'

// Servicios
import ServiciosPage from '@/pages/servicios/ServiciosPage'
import ServicioFormPage from '@/pages/servicios/ServicioFormPage'

// Combustible
import CombustiblePage from '@/pages/combustible/CombustiblePage'
import CargaFormPage from '@/pages/combustible/CargaFormPage'
import SuministroFormPage from '@/pages/combustible/SuministroFormPage'

// Remitos
import RemitosPage from '@/pages/remitos/RemitosPage'

function App() {
  return (
    <Router>
      <Routes>
        {/* Ruta pública */}
        <Route path="/login" element={<LoginPage />} />

        {/* Rutas protegidas */}
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <MainLayout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<DashboardPage />} />

          {/* Camiones */}
          <Route path="camiones" element={<CamionesPage />} />
          <Route path="camiones/nuevo" element={<CamionFormPage />} />
          <Route path="camiones/:id" element={<CamionDetailPage />} />
          <Route path="camiones/:id/editar" element={<CamionFormPage />} />

          {/* Repuestos */}
          <Route path="repuestos" element={<RepuestosPage />} />
          <Route path="repuestos/nuevo" element={<RepuestoFormPage />} />
          <Route path="repuestos/:id/editar" element={<RepuestoFormPage />} />

          {/* Servicios */}
          <Route path="servicios" element={<ServiciosPage />} />
          <Route path="servicios/nuevo" element={<ServicioFormPage />} />
          <Route path="servicios/:id/editar" element={<ServicioFormPage />} />

          {/* Pesajes */}
          <Route path="pesajes" element={<PesajesPage />} />
          <Route path="pesajes/nuevo" element={<PesajeFormPage />} />
          <Route path="pesajes/:id/editar" element={<PesajeFormPage />} />

          {/* Remitos */}
          <Route path="remitos" element={<RemitosPage />} />

          {/* Combustible */}
          <Route path="combustible" element={<CombustiblePage />} />
          <Route path="combustible/carga-nueva" element={<CargaFormPage />} />
          <Route path="combustible/suministro-nuevo" element={<SuministroFormPage />} />

          {/* Pendientes */}
          <Route path="reportes" element={<div className="p-4">Módulo de Reportes (en desarrollo)</div>} />
        </Route>

        {/* Ruta 404 */}
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </Router>
  )
}

export default App
