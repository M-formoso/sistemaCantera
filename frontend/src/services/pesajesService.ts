import api from './api'
import { Pesaje, PesajeCreate } from '@/types'

export const pesajesService = {
  /**
   * Obtiene todos los pesajes
   */
  async getAll(skip: number = 0, limit: number = 100): Promise<Pesaje[]> {
    const response = await api.get<Pesaje[]>('/pesajes', {
      params: { skip, limit },
    })
    return response.data
  },

  /**
   * Obtiene pesajes por rango de fechas
   */
  async getByFechas(fechaInicio: string, fechaFin: string): Promise<Pesaje[]> {
    const response = await api.get<Pesaje[]>('/pesajes/por-fecha', {
      params: { fecha_inicio: fechaInicio, fecha_fin: fechaFin },
    })
    return response.data
  },

  /**
   * Obtiene un pesaje por ID
   */
  async getById(id: string): Promise<Pesaje> {
    const response = await api.get<Pesaje>(`/pesajes/${id}`)
    return response.data
  },

  /**
   * Crea un nuevo pesaje
   */
  async create(data: PesajeCreate): Promise<Pesaje> {
    const response = await api.post<Pesaje>('/pesajes', data)
    return response.data
  },

  /**
   * Actualiza un pesaje
   */
  async update(id: string, data: Partial<PesajeCreate>): Promise<Pesaje> {
    const response = await api.put<Pesaje>(`/pesajes/${id}`, data)
    return response.data
  },

  /**
   * Elimina un pesaje (soft delete)
   */
  async delete(id: string): Promise<void> {
    await api.delete(`/pesajes/${id}`)
  },

  /**
   * Obtiene estadísticas de pesajes
   */
  async getEstadisticas(
    fechaInicio?: string,
    fechaFin?: string
  ): Promise<{
    total_pesajes: number
    total_toneladas: number
    peso_promedio: number
    por_material: { material: string; total_toneladas: number }[]
  }> {
    const response = await api.get('/pesajes/estadisticas', {
      params: { fecha_inicio: fechaInicio, fecha_fin: fechaFin },
    })
    return response.data
  },

  /**
   * Descarga el ticket PDF de un pesaje
   */
  async downloadTicketPDF(id: string, numeroPesaje: number): Promise<void> {
    const response = await api.get(`/pesajes/${id}/ticket-pdf`, {
      responseType: 'blob',
    })

    // Crear blob y descargar
    const blob = new Blob([response.data], { type: 'application/pdf' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `ticket_pesaje_${numeroPesaje}.pdf`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
  },
}
