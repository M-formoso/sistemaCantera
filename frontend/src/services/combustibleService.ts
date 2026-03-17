import api from './api'
import { CisternaCombustible, CargaCisterna, SuministroCombustible } from '@/types'

export const combustibleService = {
  // ========== CISTERNAS ==========
  /**
   * Obtiene todas las cisternas
   */
  async getCisternas(): Promise<CisternaCombustible[]> {
    const response = await api.get<CisternaCombustible[]>('/combustible/cisternas')
    return response.data
  },

  /**
   * Obtiene una cisterna por ID
   */
  async getCisternaById(id: string): Promise<CisternaCombustible> {
    const response = await api.get<CisternaCombustible>(`/combustible/cisternas/${id}`)
    return response.data
  },

  /**
   * Crea una cisterna
   */
  async createCisterna(data: {
    nombre: string
    capacidad_total: number
    nivel_minimo: number
  }): Promise<CisternaCombustible> {
    const response = await api.post<CisternaCombustible>('/combustible/cisternas', data)
    return response.data
  },

  /**
   * Actualiza una cisterna
   */
  async updateCisterna(
    id: string,
    data: Partial<{ nombre: string; capacidad_total: number; nivel_minimo: number }>
  ): Promise<CisternaCombustible> {
    const response = await api.put<CisternaCombustible>(`/combustible/cisternas/${id}`, data)
    return response.data
  },

  // ========== CARGAS ==========
  /**
   * Obtiene todas las cargas de una cisterna
   */
  async getCargas(cisternaId?: string): Promise<CargaCisterna[]> {
    const response = await api.get<CargaCisterna[]>('/combustible/cargas', {
      params: cisternaId ? { cisterna_id: cisternaId } : undefined,
    })
    return response.data
  },

  /**
   * Registra una carga de combustible
   */
  async registrarCarga(data: {
    cisterna_id: string
    fecha: string
    litros: number
    proveedor: string
    numero_remito?: string
    precio_por_litro?: number
    observaciones?: string
  }): Promise<CargaCisterna> {
    const response = await api.post<CargaCisterna>('/combustible/cargas', data)
    return response.data
  },

  // ========== SUMINISTROS ==========
  /**
   * Obtiene todos los suministros
   */
  async getSuministros(skip: number = 0, limit: number = 100): Promise<SuministroCombustible[]> {
    const response = await api.get<SuministroCombustible[]>('/combustible/suministros', {
      params: { skip, limit },
    })
    return response.data
  },

  /**
   * Obtiene un suministro por ID
   */
  async getSuministroById(id: string): Promise<SuministroCombustible> {
    const response = await api.get<SuministroCombustible>(`/combustible/suministros/${id}`)
    return response.data
  },

  /**
   * Obtiene suministros por camión
   */
  async getSuministrosPorCamion(camionId: string): Promise<SuministroCombustible[]> {
    const response = await api.get<SuministroCombustible[]>('/combustible/suministros/por-camion', {
      params: { camion_id: camionId },
    })
    return response.data
  },

  /**
   * Registra un suministro de combustible
   */
  async registrarSuministro(data: {
    cisterna_id: string
    camion_id: string
    fecha: string
    litros: number
    kilometraje_actual?: number
    observaciones?: string
  }): Promise<SuministroCombustible> {
    const response = await api.post<SuministroCombustible>('/combustible/suministros', data)
    return response.data
  },

  /**
   * Actualiza un suministro de combustible
   */
  async updateSuministro(
    id: string,
    data: {
      litros?: number
      chofer?: string
      kilometraje?: number
      horometro?: number
      observaciones?: string
    }
  ): Promise<SuministroCombustible> {
    const response = await api.put<SuministroCombustible>(`/combustible/suministros/${id}`, data)
    return response.data
  },

  /**
   * Elimina un suministro de combustible
   */
  async deleteSuministro(id: string): Promise<void> {
    await api.delete(`/combustible/suministros/${id}`)
  },

  /**
   * Obtiene estadísticas de consumo
   */
  async getEstadisticas(
    fechaInicio?: string,
    fechaFin?: string
  ): Promise<{
    total_suministrado: number
    total_camiones: number
    promedio_por_camion: number
    por_camion: { camion_patente: string; total_litros: number }[]
  }> {
    const response = await api.get<{
      total_suministrado: number
      total_camiones: number
      promedio_por_camion: number
      por_camion: { camion_patente: string; total_litros: number }[]
    }>('/combustible/suministros/estadisticas', {
      params: { fecha_inicio: fechaInicio, fecha_fin: fechaFin },
    })
    return response.data
  },
}
