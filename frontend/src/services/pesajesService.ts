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
  cliente_id?: string  // Obligatorio si no se cargó al iniciar
  material?: string    // Obligatorio si no se cargó al iniciar
  chofer?: string
  observaciones?: string
  precio_unitario?: number
  flete?: number
  precio_fijo?: number
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
  camion_tipo?: string
  camion_año?: number
  cliente_id?: string
  cliente_nombre?: string
  chofer_habitual?: string
  acoplado?: string
  pesaje_pendiente_id?: string
  pesaje_pendiente_numero?: number
  pesaje_pendiente_tara?: number
  pesaje_pendiente_fecha?: string
}

export const pesajesService = {
  /**
   * Obtiene todos los pesajes
   * @param skip - Offset para paginación
   * @param limit - Límite de resultados
   * @param incluirCancelados - Si es true, incluye pesajes cancelados
   * @param soloCancelados - Si es true, solo retorna cancelados (para auditoría)
   */
  async getAll(
    skip: number = 0,
    limit: number = 100,
    incluirCancelados: boolean = false,
    soloCancelados: boolean = false
  ): Promise<Pesaje[]> {
    const response = await api.get<Pesaje[]>('/pesajes', {
      params: { skip, limit, incluir_cancelados: incluirCancelados, solo_cancelados: soloCancelados },
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
   * @param id - ID del pesaje
   * @param numeroPesaje - Número de pesaje para el nombre del archivo
   * @param copias - Número de copias: 1=original, 2=duplicado, 3=triplicado
   */
  async downloadTicketPDF(id: string, numeroPesaje: number, copias: 1 | 2 | 3 = 1): Promise<void> {
    const response = await api.get<Blob>(`/pesajes/${id}/ticket-pdf`, {
      params: { copias },
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
   * Cancela un pesaje (soft-delete con auditoría)
   * Requiere motivo obligatorio (mínimo 10 caracteres)
   */
  async cancelarPesaje(pesajeId: string, motivo: string): Promise<Pesaje> {
    const response = await api.post<Pesaje>(`/pesajes/${pesajeId}/cancelar`, { motivo })
    return response.data
  },

  /**
   * Obtiene pesajes cancelados (para auditoría)
   */
  async getCancelados(skip: number = 0, limit: number = 100): Promise<Pesaje[]> {
    const response = await api.get<Pesaje[]>('/pesajes', {
      params: { skip, limit, solo_cancelados: true },
    })
    return response.data
  },

  /**
   * Sincroniza un pesaje con la cuenta corriente del cliente
   * Útil para pesajes históricos que no tienen movimiento registrado
   */
  async sincronizarCuentaCorriente(pesajeId: string): Promise<{
    status: 'creado' | 'ya_existe' | 'sin_cliente' | 'no_completado' | 'error'
    movimiento_id?: string
    message?: string
  }> {
    const response = await api.post<{
      status: 'creado' | 'ya_existe' | 'sin_cliente' | 'no_completado' | 'error'
      movimiento_id?: string
      message?: string
    }>(`/pesajes/${pesajeId}/sincronizar-cuenta-corriente`)
    return response.data
  },
}
