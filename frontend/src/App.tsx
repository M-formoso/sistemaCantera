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

// Pesajes y Remitos (unificados)
import PesajesRemitosPage from '@/pages/pesajes/PesajesRemitosPage'
import PesajeFormPage from '@/pages/pesajes/PesajeFormPage'

// Servicios
import ServiciosPage from '@/pages/servicios/ServiciosPage'
import ServicioFormPage from '@/pages/servicios/ServicioFormPage'

// Combustible
import CombustiblePage from '@/pages/combustible/CombustiblePage'
import CargaFormPage from '@/pages/combustible/CargaFormPage'
import SuministroFormPage from '@/pages/combustible/SuministroFormPage'


// Usuarios
import UsuariosPage from '@/pages/usuarios/UsuariosPage'
import UsuarioFormPage from '@/pages/usuarios/UsuarioFormPage'

// Empresas (Clientes/Transportistas)
import EmpresasPage from '@/pages/empresas/EmpresasPage'

// Finanzas
import FinanzasPage from '@/pages/finanzas/FinanzasPage'
import CuentaCorrientePage from '@/pages/finanzas/CuentaCorrientePage'

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

          {/* Empresas (Clientes/Transportistas) */}
          <Route path="empresas" element={<EmpresasPage />} />

          {/* Repuestos */}
          <Route path="repuestos" element={<RepuestosPage />} />
          <Route path="repuestos/nuevo" element={<RepuestoFormPage />} />
          <Route path="repuestos/:id/editar" element={<RepuestoFormPage />} />

          {/* Servicios */}
          <Route path="servicios" element={<ServiciosPage />} />
          <Route path="servicios/nuevo" element={<ServicioFormPage />} />
          <Route path="servicios/:id/editar" element={<ServicioFormPage />} />

          {/* Pesajes y Remitos (unificados) */}
          <Route path="pesajes-remitos" element={<PesajesRemitosPage />} />
          <Route path="pesajes-remitos/nuevo" element={<PesajeFormPage />} />
          <Route path="pesajes-remitos/:id/editar" element={<PesajeFormPage />} />

          {/* Rutas legacy para compatibilidad */}
          <Route path="pesajes" element={<Navigate to="/pesajes-remitos" replace />} />
          <Route path="remitos" element={<Navigate to="/pesajes-remitos" replace />} />

          {/* Combustible */}
          <Route path="combustible" element={<CombustiblePage />} />
          <Route path="combustible/carga-nueva" element={<CargaFormPage />} />
          <Route path="combustible/suministro-nuevo" element={<SuministroFormPage />} />

          {/* Usuarios */}
          <Route path="usuarios" element={<UsuariosPage />} />
          <Route path="usuarios/nuevo" element={<UsuarioFormPage />} />
          <Route path="usuarios/:id/editar" element={<UsuarioFormPage />} />

          {/* Finanzas */}
          <Route path="finanzas" element={<FinanzasPage />} />
          <Route path="cuenta-corriente" element={<CuentaCorrientePage />} />

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
