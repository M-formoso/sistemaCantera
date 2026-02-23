import { Navigate } from 'react-router-dom'
import { useAuthStore } from '@/stores/authStore'
import { User } from '@/types'

type PermisoKey = keyof Pick<User,
  'permiso_dashboard' | 'permiso_camiones' | 'permiso_empresas' |
  'permiso_repuestos' | 'permiso_pesajes' | 'permiso_combustible' |
  'permiso_finanzas' | 'permiso_usuarios' | 'permiso_reportes'
>

interface PermisoRouteProps {
  children: React.ReactNode
  permiso: PermisoKey
}

export default function PermisoRoute({ children, permiso }: PermisoRouteProps) {
  const { user, isLoading } = useAuthStore()

  // Si está cargando, mostrar loading
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Cargando...</div>
      </div>
    )
  }

  // Si no hay usuario, esperar (ProtectedRoute lo manejará)
  if (!user) {
    return null
  }

  // Los administradores siempre tienen acceso a todo
  if (user.rol === 'administrador') {
    return <>{children}</>
  }

  // Para otros usuarios, verificar permisos
  // Si el permiso no está definido (undefined/null), asumir que tiene acceso
  const permisoValue = user[permiso]
  const tienePermiso = permisoValue === undefined || permisoValue === null || permisoValue === true

  // Verificar si tiene el permiso
  if (!tienePermiso) {
    // Redirigir al dashboard si no tiene permiso (excepto si es el dashboard mismo)
    if (permiso === 'permiso_dashboard') {
      // Si no tiene permiso al dashboard, mostrar mensaje
      return (
        <div className="flex items-center justify-center h-64">
          <div className="text-red-500">No tiene permisos para acceder al sistema. Contacte al administrador.</div>
        </div>
      )
    }
    return <Navigate to="/dashboard" replace />
  }

  return <>{children}</>
}
