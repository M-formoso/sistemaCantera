import api from './api'
import { Empresa, EmpresaCreate } from '@/types'

// Tipos para camiones de clientes
export interface CamionCliente {
  id: string
  cliente_id: string
  patente: string
  descripcion?: string
  chofer_habitual?: string
  activo: boolean
  created_at: string
  updated_at: string
}

export interface CamionClienteCreate {
  patente: string
  descripcion?: string
  chofer_habitual?: string
}

export interface CamionClienteUpdate {
  patente?: string
  descripcion?: string
  chofer_habitual?: string
  activo?: boolean
}

export interface BusquedaClientePorPatente {
  encontrado: boolean
  cliente_id?: string
  cliente_nombre?: string
  cliente_cuit?: string
  cliente_direccion?: string
  cliente_telefono?: string
  camion_id?: string
  camion_patente?: string
  camion_descripcion?: string
  chofer_habitual?: string
}

export const empresasService = {
  /**
   * Obtiene todas las empresas
   * @param tipo - Filtrar por tipo (cliente/transportista)
   * @param soloActivos - Si es true, solo retorna empresas activas (default: true)
   */
  async getAll(tipo?: 'cliente' | 'transportista', soloActivos: boolean = true): Promise<Empresa[]> {
    const params: Record<string, any> = { limit: 500, solo_activos: soloActivos }
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
    const params: Record<string, any> = { q: nombre }
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
   * Desactiva una empresa (soft delete)
   */
  async delete(id: string): Promise<Empresa> {
    const response = await api.delete<Empresa>(`/empresas/${id}`)
    return response.data
  },

  /**
   * Reactiva una empresa desactivada
   */
  async reactivar(id: string): Promise<Empresa> {
    const response = await api.put<Empresa>(`/empresas/${id}`, { activo: true })
    return response.data
  },

  // ============== CAMIONES DE CLIENTES ==============

  /**
   * Obtiene los camiones/patentes de un cliente
   */
  async getCamiones(clienteId: string): Promise<CamionCliente[]> {
    const response = await api.get<CamionCliente[]>(`/empresas/${clienteId}/camiones`)
    return response.data
  },

  /**
   * Agrega un camión/patente a un cliente
   */
  async agregarCamion(clienteId: string, data: CamionClienteCreate): Promise<CamionCliente> {
    const response = await api.post<CamionCliente>(`/empresas/${clienteId}/camiones`, data)
    return response.data
  },

  /**
   * Actualiza un camión de cliente
   */
  async actualizarCamion(camionId: string, data: CamionClienteUpdate): Promise<CamionCliente> {
    const response = await api.put<CamionCliente>(`/empresas/camiones/${camionId}`, data)
    return response.data
  },

  /**
   * Elimina un camión de cliente
   */
  async eliminarCamion(camionId: string): Promise<void> {
    await api.delete(`/empresas/camiones/${camionId}`)
  },

  /**
   * Busca un cliente por la patente de uno de sus camiones
   */
  async buscarClientePorPatente(patente: string): Promise<BusquedaClientePorPatente> {
    const response = await api.get<BusquedaClientePorPatente>(
      `/empresas/camiones/buscar-patente/${encodeURIComponent(patente)}`
    )
    return response.data
  },

  /**
   * Asigna una lista de precios a un cliente
   */
  async asignarListaPrecio(empresaId: string, listaPrecioId: string | null): Promise<{
    message: string
    empresa_id: string
    empresa_nombre: string
    lista_precio_id: string | null
    lista_precio_nombre: string | null
  }> {
    const response = await api.put(`/empresas/${empresaId}/lista-precio`, null, {
      params: listaPrecioId ? { lista_precio_id: listaPrecioId } : {}
    })
    return response.data
  },
}
