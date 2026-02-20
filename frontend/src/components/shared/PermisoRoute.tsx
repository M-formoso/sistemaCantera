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
  const { user } = useAuthStore()

  // Si no hay usuario, esperar a que cargue
  if (!user) {
    return null
  }

  // Verificar si tiene el permiso
  if (!user[permiso]) {
    // Redirigir al dashboard si no tiene permiso
    return <Navigate to="/dashboard" replace />
  }

  return <>{children}</>
}
