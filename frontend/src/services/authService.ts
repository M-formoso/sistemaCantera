import api from './api'
import { LoginCredentials, TokenResponse, User } from '@/types'

export const authService = {
  /**
   * Login de usuario
   */
  async login(credentials: LoginCredentials): Promise<TokenResponse> {
    const response = await api.post<TokenResponse>('/auth/login', credentials)
    return response.data
  },

  /**
   * Obtiene información del usuario actual
   */
  async getCurrentUser(): Promise<User> {
    const response = await api.get<User>('/auth/me')
    return response.data
  },

  /**
   * Refresca el access token
   */
  async refreshToken(refreshToken: string): Promise<{ access_token: string }> {
    const response = await api.post<{ access_token: string }>('/auth/refresh', { refresh_token: refreshToken })
    return response.data
  },

  /**
   * Cambia la contraseña del usuario actual
   */
  async changePassword(oldPassword: string, newPassword: string): Promise<void> {
    await api.put('/auth/change-password', {
      old_password: oldPassword,
      new_password: newPassword,
    })
  },
}
