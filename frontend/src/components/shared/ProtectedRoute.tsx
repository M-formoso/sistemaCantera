import { useEffect } from 'react'
import { Navigate } from 'react-router-dom'
import { useAuthStore } from '@/stores/authStore'
import { authService } from '@/services/authService'

interface ProtectedRouteProps {
  children: React.ReactNode
}

export default function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { isAuthenticated, user, setUser, setLoading } = useAuthStore()

  useEffect(() => {
    // Si está autenticado pero no tiene datos de usuario, cargarlos
    if (isAuthenticated && !user) {
      setLoading(true)
      authService
        .getCurrentUser()
        .then((userData) => {
          setUser(userData)
        })
        .catch(() => {
          // Si falla, cerrar sesión
          useAuthStore.getState().logout()
        })
        .finally(() => {
          setLoading(false)
        })
    }
  }, [isAuthenticated, user, setUser, setLoading])

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  return <>{children}</>
}
