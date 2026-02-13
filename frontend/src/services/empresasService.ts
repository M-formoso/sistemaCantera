import api from './api'
import { Empresa, EmpresaCreate } from '@/types'

export const empresasService = {
  /**
   * Obtiene todas las empresas
   */
  async getAll(tipo?: 'cliente' | 'transportista'): Promise<Empresa[]> {
    const params: Record<string, any> = { limit: 500 }
    if (tipo) {
      params.tipo = tipo
    }
    const response = await api.get<Empresa[]>('/empresas', { params })
    return response.data
  },

  /**
   * Obtiene solo clientes
   */
  async getClientes(): Promise<Empresa[]> {
    const response = await api.get<Empresa[]>('/empresas/clientes')
    return response.data
  },

  /**
   * Obtiene solo transportistas
   */
  async getTransportistas(): Promise<Empresa[]> {
    const response = await api.get<Empresa[]>('/empresas/transportistas')
    return response.data
  },

  /**
   * Busca empresas por nombre (para autocompletado)
   */
  async buscar(nombre: string, tipo?: 'cliente' | 'transportista'): Promise<Empresa[]> {
    const params: Record<string, any> = { nombre }
    if (tipo) {
      params.tipo = tipo
    }
    const response = await api.get<Empresa[]>('/empresas/buscar', { params })
    return response.data
  },

  /**
   * Obtiene una empresa por ID
   */
  async getById(id: string): Promise<Empresa> {
    const response = await api.get<Empresa>(`/empresas/${id}`)
    return response.data
  },

  /**
   * Crea una nueva empresa
   */
  async create(data: EmpresaCreate): Promise<Empresa> {
    const response = await api.post<Empresa>('/empresas', data)
    return response.data
  },

  /**
   * Actualiza una empresa
   */
  async update(id: string, data: Partial<EmpresaCreate>): Promise<Empresa> {
    const response = await api.put<Empresa>(`/empresas/${id}`, data)
    return response.data
  },

  /**
   * Elimina una empresa (soft delete)
   */
  async delete(id: string): Promise<void> {
    await api.delete(`/empresas/${id}`)
  },
}
