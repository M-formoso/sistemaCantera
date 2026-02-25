import { useAuthStore } from '@/stores/authStore'

/**
 * Hook para verificar si el usuario actual es administrador
 */
export function useIsAdmin(): boolean {
  const { user } = useAuthStore()
  return user?.rol === 'administrador'
}
