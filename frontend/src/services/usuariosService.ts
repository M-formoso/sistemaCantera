import api from './api'
import { User, UsuarioCreate, UsuarioUpdate, PaginatedResponse } from '@/types'

export const usuariosService = {
  /**
   * Obtiene todos los usuarios con paginación
   */
  async getAll(params?: {
    skip?: number
    limit?: number
    activo?: boolean
    rol?: 'administrador' | 'operador' | 'solo_lectura'
  }): Promise<PaginatedResponse<User>> {
    const response = await api.get<PaginatedResponse<User>>('/usuarios', { params })
    return response.data
  },

  /**
   * Obtiene un usuario por ID
   */
  async getById(id: string): Promise<User> {
    const response = await api.get<User>(`/usuarios/${id}`)
    return response.data
  },

  /**
   * Crea un nuevo usuario
   */
  async create(data: UsuarioCreate): Promise<User> {
    const response = await api.post<User>('/usuarios', data)
    return response.data
  },

  /**
   * Actualiza un usuario
   */
  async update(id: string, data: UsuarioUpdate): Promise<User> {
    const response = await api.put<User>(`/usuarios/${id}`, data)
    return response.data
  },

  /**
   * Elimina un usuario
   */
  async delete(id: string): Promise<void> {
    await api.delete(`/usuarios/${id}`)
  },

  /**
   * Resetea la contraseña de un usuario
   */
  async resetPassword(id: string, newPassword: string): Promise<{ message: string }> {
    const response = await api.put<{ message: string }>(
      `/usuarios/${id}/reset-password`,
      null,
      { params: { new_password: newPassword } }
    )
    return response.data
  },
}
