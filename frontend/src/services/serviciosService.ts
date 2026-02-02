import api from './api'
import { Servicio, ServicioCreate } from '@/types'

export const serviciosService = {
  /**
   * Obtiene todos los servicios
   */
  async getAll(skip: number = 0, limit: number = 100): Promise<Servicio[]> {
    const response = await api.get<Servicio[]>('/servicios', {
      params: { skip, limit },
    })
    return response.data
  },

  /**
   * Obtiene servicios programados (próximos 7 días)
   */
  async getProgramados(): Promise<Servicio[]> {
    const response = await api.get<Servicio[]>('/servicios/programados')
    return response.data
  },

  /**
   * Obtiene servicios por camión
   */
  async getPorCamion(camionId: string): Promise<Servicio[]> {
    const response = await api.get<Servicio[]>('/servicios/por-camion', {
      params: { camion_id: camionId },
    })
    return response.data
  },

  /**
   * Obtiene un servicio por ID
   */
  async getById(id: string): Promise<Servicio> {
    const response = await api.get<Servicio>(`/servicios/${id}`)
    return response.data
  },

  /**
   * Crea un nuevo servicio con repuestos
   */
  async create(data: ServicioCreate): Promise<Servicio> {
    const response = await api.post<Servicio>('/servicios', data)
    return response.data
  },

  /**
   * Actualiza un servicio
   */
  async update(id: string, data: Partial<ServicioCreate>): Promise<Servicio> {
    const response = await api.put<Servicio>(`/servicios/${id}`, data)
    return response.data
  },

  /**
   * Elimina un servicio (soft delete)
   */
  async delete(id: string): Promise<void> {
    await api.delete(`/servicios/${id}`)
  },
}
