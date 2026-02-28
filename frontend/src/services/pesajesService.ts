import api from './api'
import { Pesaje, PesajeCreate } from '@/types'

// Tipos para flujo de doble pesaje
export interface PesajeIniciarCreate {
  tipo_entrega: 'propio' | 'transportista'
  camion_id?: string
  transportista_id?: string
  patente_externa?: string
  transportista?: string
  cliente_id?: string
  cliente_nombre?: string
  acoplado?: string
  chofer?: string
  peso_tara: number
  material?: string
  operario?: string
  observaciones?: string
  orden_entrega_id?: string
  fecha?: string
}

export interface PesajeCompletarCreate {
  peso_bruto: number
  material?: string
  chofer?: string
  observaciones?: string
  precio_unitario?: number
  importe_total?: number
  orden_entrega_id?: string
}

export interface PesajePendiente {
  id: string
  numero_pesaje: number
  fecha: string
  estado: 'pendiente'
  tipo_entrega: 'propio' | 'transportista'
  camion_id?: string
  camion_patente?: string
  patente_externa?: string
  cliente_id?: string
  cliente_nombre?: string
  transportista_id?: string
  transportista_nombre?: string
  peso_tara: number
  material?: string
  chofer?: string
  acoplado?: string
  minutos_esperando?: number
}

export interface BusquedaPatenteResult {
  encontrado: boolean
  tipo?: 'propio' | 'cliente' | 'transportista'
  camion_id?: string
  camion_patente?: string
  camion_marca?: string
  camion_modelo?: string
  camion_descripcion?: string
  cliente_id?: string
  cliente_nombre?: string
  chofer_habitual?: string
  pesaje_pendiente_id?: string
  pesaje_pendiente_numero?: number
  pesaje_pendiente_tara?: number
  pesaje_pendiente_fecha?: string
}

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
    const response = await api.get<{
      total_pesajes: number
      total_toneladas: number
      peso_promedio: number
      por_material: { material: string; total_toneladas: number }[]
    }>('/pesajes/estadisticas', {
      params: { fecha_inicio: fechaInicio, fecha_fin: fechaFin },
    })
    return response.data
  },

  /**
   * Descarga el ticket PDF de un pesaje
   */
  async downloadTicketPDF(id: string, numeroPesaje: number): Promise<void> {
    const response = await api.get<Blob>(`/pesajes/${id}/ticket-pdf`, {
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

  // ============== FLUJO DOBLE PESAJE ==============

  /**
   * Obtiene pesajes pendientes (solo tara registrada)
   */
  async getPendientes(): Promise<PesajePendiente[]> {
    const response = await api.get<PesajePendiente[]>('/pesajes/pendientes')
    return response.data
  },

  /**
   * Busca información por patente del camión
   */
  async buscarPorPatente(patente: string): Promise<BusquedaPatenteResult> {
    const response = await api.get<BusquedaPatenteResult>(`/pesajes/buscar-patente/${encodeURIComponent(patente)}`)
    return response.data
  },

  /**
   * Inicia un nuevo pesaje (solo tara - camión vacío)
   */
  async iniciarPesaje(data: PesajeIniciarCreate): Promise<Pesaje> {
    const response = await api.post<Pesaje>('/pesajes/iniciar', data)
    return response.data
  },

  /**
   * Completa un pesaje pendiente (peso bruto - camión cargado)
   */
  async completarPesaje(pesajeId: string, data: PesajeCompletarCreate): Promise<Pesaje> {
    const response = await api.post<Pesaje>(`/pesajes/${pesajeId}/completar`, data)
    return response.data
  },

  /**
   * Cancela un pesaje pendiente
   */
  async cancelarPendiente(pesajeId: string): Promise<void> {
    await api.delete(`/pesajes/${pesajeId}/cancelar`)
  },
}
