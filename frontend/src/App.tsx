import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import LoginPage from '@/pages/auth/LoginPage'
import MainLayout from '@/components/layout/MainLayout'
import ProtectedRoute from '@/components/shared/ProtectedRoute'
import PermisoRoute from '@/components/shared/PermisoRoute'
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
          <Route path="dashboard" element={<PermisoRoute permiso="permiso_dashboard"><DashboardPage /></PermisoRoute>} />

          {/* Camiones */}
          <Route path="camiones" element={<PermisoRoute permiso="permiso_camiones"><CamionesPage /></PermisoRoute>} />
          <Route path="camiones/nuevo" element={<PermisoRoute permiso="permiso_camiones"><CamionFormPage /></PermisoRoute>} />
          <Route path="camiones/:id" element={<PermisoRoute permiso="permiso_camiones"><CamionDetailPage /></PermisoRoute>} />
          <Route path="camiones/:id/editar" element={<PermisoRoute permiso="permiso_camiones"><CamionFormPage /></PermisoRoute>} />

          {/* Empresas (Clientes/Transportistas) */}
          <Route path="empresas" element={<PermisoRoute permiso="permiso_empresas"><EmpresasPage /></PermisoRoute>} />

          {/* Repuestos */}
          <Route path="repuestos" element={<PermisoRoute permiso="permiso_repuestos"><RepuestosPage /></PermisoRoute>} />
          <Route path="repuestos/nuevo" element={<PermisoRoute permiso="permiso_repuestos"><RepuestoFormPage /></PermisoRoute>} />
          <Route path="repuestos/:id/editar" element={<PermisoRoute permiso="permiso_repuestos"><RepuestoFormPage /></PermisoRoute>} />

          {/* Servicios - usa permiso de repuestos */}
          <Route path="servicios" element={<PermisoRoute permiso="permiso_repuestos"><ServiciosPage /></PermisoRoute>} />
          <Route path="servicios/nuevo" element={<PermisoRoute permiso="permiso_repuestos"><ServicioFormPage /></PermisoRoute>} />
          <Route path="servicios/:id/editar" element={<PermisoRoute permiso="permiso_repuestos"><ServicioFormPage /></PermisoRoute>} />

          {/* Pesajes y Remitos (unificados) */}
          <Route path="pesajes-remitos" element={<PermisoRoute permiso="permiso_pesajes"><PesajesRemitosPage /></PermisoRoute>} />
          <Route path="pesajes-remitos/nuevo" element={<PermisoRoute permiso="permiso_pesajes"><PesajeFormPage /></PermisoRoute>} />
          <Route path="pesajes-remitos/:id/editar" element={<PermisoRoute permiso="permiso_pesajes"><PesajeFormPage /></PermisoRoute>} />

          {/* Rutas legacy para compatibilidad */}
          <Route path="pesajes" element={<Navigate to="/pesajes-remitos" replace />} />
          <Route path="remitos" element={<Navigate to="/pesajes-remitos" replace />} />

          {/* Combustible */}
          <Route path="combustible" element={<PermisoRoute permiso="permiso_combustible"><CombustiblePage /></PermisoRoute>} />
          <Route path="combustible/carga-nueva" element={<PermisoRoute permiso="permiso_combustible"><CargaFormPage /></PermisoRoute>} />
          <Route path="combustible/suministro-nuevo" element={<PermisoRoute permiso="permiso_combustible"><SuministroFormPage /></PermisoRoute>} />

          {/* Usuarios */}
          <Route path="usuarios" element={<PermisoRoute permiso="permiso_usuarios"><UsuariosPage /></PermisoRoute>} />
          <Route path="usuarios/nuevo" element={<PermisoRoute permiso="permiso_usuarios"><UsuarioFormPage /></PermisoRoute>} />
          <Route path="usuarios/:id/editar" element={<PermisoRoute permiso="permiso_usuarios"><UsuarioFormPage /></PermisoRoute>} />

          {/* Finanzas */}
          <Route path="finanzas" element={<PermisoRoute permiso="permiso_finanzas"><FinanzasPage /></PermisoRoute>} />

          {/* Reportes */}
          <Route path="reportes" element={<PermisoRoute permiso="permiso_reportes"><div className="p-4">Módulo de Reportes (en desarrollo)</div></PermisoRoute>} />
        </Route>

        {/* Ruta 404 */}
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </Router>
  )
}

export default App
