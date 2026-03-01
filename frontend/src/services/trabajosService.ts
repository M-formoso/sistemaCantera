import api from './api'
import { Trabajo, TrabajoCreate } from '@/types'

export const trabajosService = {
  /**
   * Obtiene todos los trabajos
   */
  async getAll(camionId?: string): Promise<Trabajo[]> {
    const params: any = { limit: 500 }
    if (camionId) params.camion_id = camionId
    const response = await api.get<Trabajo[]>('/trabajos', { params })
    return response.data
  },

  /**
   * Obtiene trabajos de un equipo específico
   */
  async getByEquipo(camionId: string): Promise<Trabajo[]> {
    const response = await api.get<Trabajo[]>(`/trabajos/por-equipo/${camionId}`)
    return response.data
  },

  /**
   * Obtiene un trabajo por ID
   */
  async getById(id: string): Promise<Trabajo> {
    const response = await api.get<Trabajo>(`/trabajos/${id}`)
    return response.data
  },

  /**
   * Crea un nuevo trabajo
   */
  async create(data: TrabajoCreate): Promise<Trabajo> {
    const response = await api.post<Trabajo>('/trabajos', data)
    return response.data
  },

  /**
   * Actualiza un trabajo
   */
  async update(id: string, data: Partial<TrabajoCreate>): Promise<Trabajo> {
    const response = await api.put<Trabajo>(`/trabajos/${id}`, data)
    return response.data
  },

  /**
   * Elimina un trabajo
   */
  async delete(id: string): Promise<void> {
    await api.delete(`/trabajos/${id}`)
  },
}
