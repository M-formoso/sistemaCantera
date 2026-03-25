import api from './api'

// Tipos
export interface PrecioCliente {
  id: string
  cliente_id: string
  cliente_nombre?: string
  material: string
  precio_unitario: number
  factor_conversion_m3?: number | null
  created_at?: string
  updated_at?: string
}

export interface PrecioClienteCreate {
  cliente_id: string
  material: string
  precio_unitario: number
  factor_conversion_m3?: number | null
}

export interface PrecioClienteUpdate {
  precio_unitario?: number
  factor_conversion_m3?: number | null
}

export interface CalculoPrecio {
  precio_encontrado: boolean
  mensaje?: string
  peso_toneladas?: number
  cantidad_facturada?: number
  unidad?: 'tn' | 'm3'
  precio_unitario?: number
  factor_conversion?: number | null
  importe?: number
  material?: string
}

export interface PrecioMultiple {
  material: string
  precio_unitario: number
  factor_conversion_m3?: number | null
}

export const preciosService = {
  /**
   * Obtiene la lista de materiales disponibles
   */
  async getMateriales(): Promise<string[]> {
    const response = await api.get<{ materiales: string[] }>('/precios/materiales')
    return response.data.materiales
  },

  /**
   * Obtiene todos los precios configurados
   */
  async getAll(skip: number = 0, limit: number = 100): Promise<PrecioCliente[]> {
    const response = await api.get<PrecioCliente[]>('/precios', {
      params: { skip, limit },
    })
    return response.data
  },

  /**
   * Obtiene los precios de un cliente específico
   */
  async getByCliente(clienteId: string): Promise<PrecioCliente[]> {
    const response = await api.get<PrecioCliente[]>(`/precios/cliente/${clienteId}`)
    return response.data
  },

  /**
   * Obtiene el precio para un cliente y material específico
   */
  async getByClienteMaterial(clienteId: string, material: string): Promise<PrecioCliente | null> {
    try {
      const response = await api.get<PrecioCliente | null>(
        `/precios/cliente/${clienteId}/material/${encodeURIComponent(material)}`
      )
      return response.data
    } catch {
      return null
    }
  },

  /**
   * Crea un nuevo precio
   */
  async create(data: PrecioClienteCreate): Promise<PrecioCliente> {
    const response = await api.post<PrecioCliente>('/precios', data)
    return response.data
  },

  /**
   * Crea o actualiza múltiples precios para un cliente
   */
  async createMultiple(clienteId: string, precios: PrecioMultiple[]): Promise<PrecioCliente[]> {
    const response = await api.post<PrecioCliente[]>(
      `/precios/cliente/${clienteId}/multiple`,
      precios
    )
    return response.data
  },

  /**
   * Actualiza un precio existente
   */
  async update(precioId: string, data: PrecioClienteUpdate): Promise<PrecioCliente> {
    const response = await api.put<PrecioCliente>(`/precios/${precioId}`, data)
    return response.data
  },

  /**
   * Elimina un precio
   */
  async delete(precioId: string): Promise<void> {
    await api.delete(`/precios/${precioId}`)
  },

  /**
   * Calcula el importe para un cliente, material y peso dado.
   * Útil para mostrar el cálculo en tiempo real al completar un pesaje.
   */
  async calcular(
    clienteId: string,
    material: string,
    pesoNetoKg: number
  ): Promise<CalculoPrecio> {
    const response = await api.get<CalculoPrecio>('/precios/calcular', {
      params: {
        cliente_id: clienteId,
        material,
        peso_neto_kg: pesoNetoKg,
      },
    })
    return response.data
  },
}
