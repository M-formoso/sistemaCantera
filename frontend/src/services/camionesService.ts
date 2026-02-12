import api from './api'
import { Camion, CamionCreate } from '@/types'

export const camionesService = {
  /**
   * Obtiene todos los camiones
   */
  async getAll(soloActivos: boolean = true): Promise<Camion[]> {
    // Construir URL manualmente para evitar problema de params
    const url = `/camiones/?solo_activos=${soloActivos}&limit=500`
    const response = await api.get<Camion[]>(url)
    return response.data
  },

  /**
   * Obtiene un camión por ID
   */
  async getById(id: string): Promise<Camion> {
    const response = await api.get<Camion>(`/camiones/${id}`)
    return response.data
  },

  /**
   * Crea un nuevo camión
   */
  async create(data: CamionCreate): Promise<Camion> {
    const response = await api.post<Camion>('/camiones', data)
    return response.data
  },

  /**
   * Actualiza un camión
   */
  async update(id: string, data: Partial<CamionCreate>): Promise<Camion> {
    const response = await api.put<Camion>(`/camiones/${id}`, data)
    return response.data
  },

  /**
   * Elimina un camión (soft delete)
   */
  async delete(id: string): Promise<void> {
    await api.delete(`/camiones/${id}`)
  },

  /**
   * Obtiene servicios de un camión
   */
  async getServicios(id: string): Promise<any[]> {
    const response = await api.get(`/camiones/${id}/servicios`)
    return response.data
  },
}
