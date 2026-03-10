import { Navigate } from 'react-router-dom'
import { useAuthStore } from '@/stores/authStore'
import { User } from '@/types'

type PermisoKey = keyof Pick<User,
  'permiso_dashboard' | 'permiso_camiones' | 'permiso_empresas' |
  'permiso_repuestos' | 'permiso_pesajes' | 'permiso_combustible' |
  'permiso_finanzas' | 'permiso_usuarios' | 'permiso_reportes'
>

// Mapeo de permisos a rutas
const PERMISO_RUTA_MAP: Record<PermisoKey, string> = {
  permiso_dashboard: '/dashboard',
  permiso_pesajes: '/pesajes-remitos',
  permiso_camiones: '/camiones',
  permiso_empresas: '/empresas',
  permiso_repuestos: '/repuestos',
  permiso_combustible: '/combustible',
  permiso_finanzas: '/finanzas',
  permiso_usuarios: '/usuarios',
  permiso_reportes: '/reportes',
}

// Orden de prioridad para redirigir
const PERMISOS_ORDEN: PermisoKey[] = [
  'permiso_dashboard',
  'permiso_pesajes',
  'permiso_camiones',
  'permiso_empresas',
  'permiso_repuestos',
  'permiso_combustible',
  'permiso_finanzas',
  'permiso_reportes',
  'permiso_usuarios',
]

// Función para obtener la primera ruta disponible para el usuario
export function obtenerPrimeraRutaDisponible(user: User): string {
  // Admin tiene acceso a todo
  if (user.rol === 'administrador') {
    return '/dashboard'
  }

  // Buscar el primer permiso que tenga activo
  for (const permiso of PERMISOS_ORDEN) {
    const valor = user[permiso]
    if (valor === true) {
      return PERMISO_RUTA_MAP[permiso]
    }
  }

  // Si no tiene ningún permiso, devolver dashboard (mostrará error)
  return '/dashboard'
}

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
  // Si el permiso no está definido (undefined/null), asumir que NO tiene acceso
  const permisoValue = user[permiso]
  const tienePermiso = permisoValue === true

  // Verificar si tiene el permiso
  if (!tienePermiso) {
    // Obtener la primera ruta disponible
    const primeraRuta = obtenerPrimeraRutaDisponible(user)

    // Si no tiene permiso al dashboard, redirigir a la primera ruta disponible
    if (permiso === 'permiso_dashboard') {
      // Si la primera ruta es dashboard (no tiene ningún permiso), mostrar error
      if (primeraRuta === '/dashboard') {
        return (
          <div className="flex items-center justify-center h-64">
            <div className="text-red-500">No tiene permisos para acceder al sistema. Contacte al administrador.</div>
          </div>
        )
      }
      // Redirigir a la primera ruta disponible
      return <Navigate to={primeraRuta} replace />
    }

    // Para otros módulos, redirigir a la primera ruta disponible
    return <Navigate to={primeraRuta} replace />
  }

  return <>{children}</>
}
