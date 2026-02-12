import api from './api'
import { Remito } from '@/types'

export const remitosService = {
  /**
   * Obtiene todos los remitos
   */
  async getAll(skip: number = 0, limit: number = 100): Promise<Remito[]> {
    const response = await api.get<Remito[]>('/remitos', {
      params: { skip, limit },
    })
    return response.data
  },

  /**
   * Obtiene un remito por ID
   */
  async getById(id: string): Promise<Remito> {
    const response = await api.get<Remito>(`/remitos/${id}`)
    return response.data
  },

  /**
   * Genera un remito desde un pesaje
   */
  async generarDesdePesaje(pesajeId: string): Promise<Remito> {
    const response = await api.post<Remito>('/remitos/generar-desde-pesaje', {
      pesaje_id: pesajeId,
    })
    return response.data
  },

  /**
   * Crea un remito manualmente
   */
  async create(data: {
    pesaje_id: string
    numero_remito?: string
    observaciones?: string
  }): Promise<Remito> {
    const response = await api.post<Remito>('/remitos', data)
    return response.data
  },

  /**
   * Elimina un remito (soft delete)
   */
  async delete(id: string): Promise<void> {
    await api.delete(`/remitos/${id}`)
  },

  /**
   * Descarga el PDF de un remito
   */
  async downloadPDF(id: string): Promise<Blob> {
    const response = await api.get<Blob>(`/remitos/${id}/pdf`, {
      responseType: 'blob',
    })
    return response.data
  },
}
