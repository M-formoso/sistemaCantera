import api from './api'

// ============== TIPOS ==============

export interface ItemListaPrecio {
  id: string
  lista_id: string
  material: string
  precio_unitario: number
  factor_conversion_m3?: number | null
  created_at?: string
  updated_at?: string
}

export interface ListaPrecio {
  id: string
  nombre: string
  descripcion?: string | null
  activo: boolean
  items: ItemListaPrecio[]
  created_at?: string
  updated_at?: string
}

export interface ListaPrecioResumen {
  id: string
  nombre: string
  descripcion?: string | null
  activo: boolean
  cantidad_items: number
}

export interface ListaPrecioCreate {
  nombre: string
  descripcion?: string | null
  activo?: boolean
  items?: ItemListaPrecioCreate[]
}

export interface ListaPrecioUpdate {
  nombre?: string
  descripcion?: string | null
  activo?: boolean
}

export interface ItemListaPrecioCreate {
  material: string
  precio_unitario: number
  factor_conversion_m3?: number | null
}

export interface ItemBatchUpdate {
  material: string
  precio_unitario: number
  factor_conversion_m3?: number | null
}

export interface CalculoPrecioLista {
  precio_encontrado: boolean
  mensaje?: string
  lista_id?: string
  lista_nombre?: string
  material?: string
  peso_toneladas?: number
  cantidad_facturada?: number
  unidad?: 'tn' | 'm3'
  precio_unitario?: number
  factor_conversion?: number | null
  importe?: number
}

// ============== SERVICIO ==============

export const listasPreciosService = {
  /**
   * Obtiene la lista de materiales disponibles
   */
  async getMateriales(): Promise<string[]> {
    const response = await api.get<{ materiales: string[] }>('/listas-precios/materiales')
    return response.data.materiales
  },

  /**
   * Obtiene todas las listas de precios con sus items
   */
  async getAll(soloActivas: boolean = false): Promise<ListaPrecio[]> {
    const response = await api.get<ListaPrecio[]>('/listas-precios', {
      params: { solo_activas: soloActivas },
    })
    return response.data
  },

  /**
   * Obtiene un resumen de las listas (sin items) para selectores
   */
  async getResumen(soloActivas: boolean = true): Promise<ListaPrecioResumen[]> {
    const response = await api.get<ListaPrecioResumen[]>('/listas-precios/resumen', {
      params: { solo_activas: soloActivas },
    })
    return response.data
  },

  /**
   * Obtiene una lista por ID con todos sus items
   */
  async getById(listaId: string): Promise<ListaPrecio> {
    const response = await api.get<ListaPrecio>(`/listas-precios/${listaId}`)
    return response.data
  },

  /**
   * Crea una nueva lista de precios
   */
  async create(data: ListaPrecioCreate): Promise<ListaPrecio> {
    const response = await api.post<ListaPrecio>('/listas-precios', data)
    return response.data
  },

  /**
   * Actualiza una lista de precios (nombre, descripción, activo)
   */
  async update(listaId: string, data: ListaPrecioUpdate): Promise<ListaPrecio> {
    const response = await api.put<ListaPrecio>(`/listas-precios/${listaId}`, data)
    return response.data
  },

  /**
   * Elimina una lista de precios
   */
  async delete(listaId: string): Promise<void> {
    await api.delete(`/listas-precios/${listaId}`)
  },

  /**
   * Duplica una lista de precios
   */
  async duplicar(listaId: string, nuevoNombre: string): Promise<ListaPrecio> {
    const response = await api.post<ListaPrecio>(
      `/listas-precios/${listaId}/duplicar`,
      null,
      { params: { nuevo_nombre: nuevoNombre } }
    )
    return response.data
  },

  /**
   * Agrega un item a una lista
   */
  async agregarItem(listaId: string, item: ItemListaPrecioCreate): Promise<ItemListaPrecio> {
    const response = await api.post<ItemListaPrecio>(`/listas-precios/${listaId}/items`, item)
    return response.data
  },

  /**
   * Actualiza todos los items de una lista de una vez
   */
  async actualizarItemsBatch(listaId: string, items: ItemBatchUpdate[]): Promise<ListaPrecio> {
    const response = await api.put<ListaPrecio>(
      `/listas-precios/${listaId}/items/batch`,
      { items }
    )
    return response.data
  },

  /**
   * Elimina un item de una lista
   */
  async eliminarItem(itemId: string): Promise<void> {
    await api.delete(`/listas-precios/items/${itemId}`)
  },

  /**
   * Calcula el importe para un material y peso usando una lista
   */
  async calcular(
    listaId: string,
    material: string,
    pesoNetoKg: number
  ): Promise<CalculoPrecioLista> {
    const response = await api.get<CalculoPrecioLista>(`/listas-precios/${listaId}/calcular`, {
      params: {
        material,
        peso_neto_kg: pesoNetoKg,
      },
    })
    return response.data
  },
}
