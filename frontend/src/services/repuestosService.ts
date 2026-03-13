import api from './api'
import { Repuesto, RepuestoCreate, MovimientoStock } from '@/types'

export const repuestosService = {
  /**
   * Obtiene todos los repuestos
   */
  async getAll(soloActivos: boolean = true): Promise<Repuesto[]> {
    const response = await api.get<Repuesto[]>('/repuestos', {
      params: { solo_activos: soloActivos, limit: 500 },
    })
    return response.data
  },

  /**
   * Obtiene repuestos con stock bajo
   */
  async getStockBajo(): Promise<Repuesto[]> {
    const response = await api.get<Repuesto[]>('/repuestos/stock-bajo')
    return response.data
  },

  /**
   * Obtiene un repuesto por ID
   */
  async getById(id: string): Promise<Repuesto> {
    const response = await api.get<Repuesto>(`/repuestos/${id}`)
    return response.data
  },

  /**
   * Crea un nuevo repuesto
   */
  async create(data: RepuestoCreate): Promise<Repuesto> {
    const response = await api.post<Repuesto>('/repuestos', data)
    return response.data
  },

  /**
   * Actualiza un repuesto
   */
  async update(id: string, data: Partial<RepuestoCreate>): Promise<Repuesto> {
    const response = await api.put<Repuesto>(`/repuestos/${id}`, data)
    return response.data
  },

  /**
   * Elimina un repuesto (soft delete)
   */
  async delete(id: string): Promise<void> {
    await api.delete(`/repuestos/${id}`)
  },

  /**
   * Obtiene movimientos de stock de un repuesto
   */
  async getMovimientos(id: string): Promise<MovimientoStock[]> {
    const response = await api.get<MovimientoStock[]>(`/repuestos/${id}/movimientos`)
    return response.data
  },

  /**
   * Registra entrada de stock
   */
  async registrarEntrada(
    id: string,
    cantidad: number,
    observaciones?: string
  ): Promise<MovimientoStock> {
    const response = await api.post<MovimientoStock>(`/repuestos/${id}/entrada`, {
      cantidad,
      observaciones,
    })
    return response.data
  },

  /**
   * Registra salida de stock
   */
  async registrarSalida(
    id: string,
    cantidad: number,
    observaciones?: string
  ): Promise<MovimientoStock> {
    const response = await api.post<MovimientoStock>(`/repuestos/${id}/salida`, {
      cantidad,
      observaciones,
    })
    return response.data
  },

  /**
   * Obtiene repuestos disponibles para un equipo
   * Incluye los asignados al equipo y los generales (sin asignación)
   */
  async getByEquipo(camionId: string, incluirGenerales: boolean = true): Promise<Repuesto[]> {
    const response = await api.get<Repuesto[]>(`/repuestos/por-equipo/${camionId}`, {
      params: { incluir_generales: incluirGenerales },
    })
    return response.data
  },

  /**
   * Obtiene los equipos asignados a un repuesto
   */
  async getEquiposAsignados(repuestoId: string): Promise<{ id: string; identificador: string; categoria: string; legacy: boolean }[]> {
    const response = await api.get<{ id: string; identificador: string; categoria: string; legacy: boolean }[]>(`/repuestos/${repuestoId}/equipos`)
    return response.data
  },

  /**
   * Actualiza la lista de equipos asignados a un repuesto
   */
  async updateEquiposAsignados(repuestoId: string, equiposIds: string[]): Promise<{ message: string }> {
    const response = await api.put<{ message: string }>(`/repuestos/${repuestoId}/equipos`, {
      equipos_ids: equiposIds,
    })
    return response.data
  },

  /**
   * Asigna un repuesto a un equipo específico
   */
  async asignarAEquipo(repuestoId: string, equipoId: string): Promise<{ message: string }> {
    const response = await api.post<{ message: string }>(`/repuestos/${repuestoId}/equipos/${equipoId}`)
    return response.data
  },

  /**
   * Desasigna un repuesto de un equipo
   */
  async desasignarDeEquipo(repuestoId: string, equipoId: string): Promise<{ message: string }> {
    const response = await api.delete<{ message: string }>(`/repuestos/${repuestoId}/equipos/${equipoId}`)
    return response.data
  },
}
