import api from './api'

export interface OrdenEntrega {
  id: string
  numero_orden: number
  fecha_entrega: string
  cliente_id?: string
  cliente_nombre?: string
  cliente_nombre_completo?: string
  material: string
  cantidad_cargas: number
  cargas_entregadas: number
  cargas_pendientes?: number
  peso_estimado_carga?: number
  peso_total_estimado?: number
  peso_total_entregado?: number
  estado: 'pendiente' | 'en_proceso' | 'completada' | 'cancelada'
  porcentaje_completado?: number
  solicitante?: string
  contacto_cliente?: string
  telefono_contacto?: string
  direccion_entrega?: string
  observaciones?: string
  created_at: string
  updated_at: string
}

export interface OrdenEntregaCreate {
  fecha_entrega: string
  cliente_id?: string
  cliente_nombre?: string
  material: string
  cantidad_cargas: number
  peso_estimado_carga?: number
  solicitante?: string
  contacto_cliente?: string
  telefono_contacto?: string
  direccion_entrega?: string
  observaciones?: string
}

export interface OrdenEntregaUpdate {
  fecha_entrega?: string
  cliente_id?: string
  cliente_nombre?: string
  material?: string
  cantidad_cargas?: number
  peso_estimado_carga?: number
  solicitante?: string
  contacto_cliente?: string
  telefono_contacto?: string
  direccion_entrega?: string
  observaciones?: string
  estado?: 'pendiente' | 'en_proceso' | 'completada' | 'cancelada'
}

export interface PesajeResumen {
  id: string
  numero_pesaje: number
  fecha: string
  peso_neto: number
  material?: string
  chofer?: string
  patente?: string
}

export interface OrdenEntregaConPesajes extends OrdenEntrega {
  pesajes: PesajeResumen[]
}

// Obtener todas las órdenes
export const getOrdenes = async (
  estado?: string,
  fechaDesde?: string,
  fechaHasta?: string
): Promise<OrdenEntrega[]> => {
  const params: Record<string, string> = {}
  if (estado) params.estado = estado
  if (fechaDesde) params.fecha_desde = fechaDesde
  if (fechaHasta) params.fecha_hasta = fechaHasta

  const { data } = await api.get<OrdenEntrega[]>('/ordenes-entrega/', { params })
  return data
}

// Obtener órdenes pendientes
export const getOrdenesPendientes = async (): Promise<OrdenEntrega[]> => {
  const { data } = await api.get<OrdenEntrega[]>('/ordenes-entrega/pendientes')
  return data
}

// Obtener una orden por ID
export const getOrden = async (id: string): Promise<OrdenEntrega> => {
  const { data } = await api.get<OrdenEntrega>(`/ordenes-entrega/${id}`)
  return data
}

// Obtener orden con pesajes
export const getOrdenConPesajes = async (id: string): Promise<OrdenEntregaConPesajes> => {
  const { data } = await api.get<OrdenEntregaConPesajes>(`/ordenes-entrega/${id}/detalle`)
  return data
}

// Crear orden - IMPORTANTE: usar trailing slash para evitar redirect 307
export const crearOrden = async (orden: OrdenEntregaCreate): Promise<OrdenEntrega> => {
  const url = 'https://backend-production-ee51.up.railway.app/api/v1/ordenes-entrega/'
  const token = localStorage.getItem('access_token')

  console.log('[crearOrden] 1. Iniciando...')
  console.log('[crearOrden] 2. URL:', url)
  console.log('[crearOrden] 3. Token exists:', !!token)
  console.log('[crearOrden] 4. Token value (primeros 20 chars):', token?.substring(0, 20))
  console.log('[crearOrden] 5. Body:', JSON.stringify(orden))

  const headers = {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`,
  }
  console.log('[crearOrden] 6. Headers:', JSON.stringify(headers))

  console.log('[crearOrden] 7. A punto de ejecutar fetch...')

  try {
    console.log('[crearOrden] 8. Dentro del try, ejecutando fetch AHORA')

    const response = await fetch(url, {
      method: 'POST',
      headers: headers,
      body: JSON.stringify(orden),
    })

    console.log('[crearOrden] 9. Fetch completado!')
    console.log('[crearOrden] 10. Response status:', response.status)
    console.log('[crearOrden] 11. Response ok:', response.ok)

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Error desconocido' }))
      console.error('[crearOrden] Error response:', errorData)
      throw new Error(errorData.detail || `HTTP ${response.status}`)
    }

    const data = await response.json()
    console.log('[crearOrden] 12. Success:', data)
    return data
  } catch (error: any) {
    console.error('[crearOrden] CATCH - Error:', error)
    console.error('[crearOrden] CATCH - Error.name:', error?.name)
    console.error('[crearOrden] CATCH - Error.message:', error?.message)
    throw error
  }
}

// Actualizar orden
export const actualizarOrden = async (id: string, orden: OrdenEntregaUpdate): Promise<OrdenEntrega> => {
  const { data } = await api.put<OrdenEntrega>(`/ordenes-entrega/${id}`, orden)
  return data
}

// Registrar entrega (asociar pesaje)
export const registrarEntrega = async (ordenId: string, pesajeId: string): Promise<OrdenEntrega> => {
  const { data } = await api.post<OrdenEntrega>(`/ordenes-entrega/${ordenId}/registrar-entrega/${pesajeId}`)
  return data
}

// Desasociar pesaje
export const desasociarPesaje = async (ordenId: string, pesajeId: string): Promise<OrdenEntrega> => {
  const { data } = await api.delete<OrdenEntrega>(`/ordenes-entrega/${ordenId}/desasociar-pesaje/${pesajeId}`)
  return data
}

// Cancelar orden
export const cancelarOrden = async (id: string): Promise<OrdenEntrega> => {
  const { data } = await api.post<OrdenEntrega>(`/ordenes-entrega/${id}/cancelar`)
  return data
}

// Completar orden manualmente
export const completarOrden = async (id: string): Promise<OrdenEntrega> => {
  const { data } = await api.post<OrdenEntrega>(`/ordenes-entrega/${id}/completar`)
  return data
}

// Eliminar orden
export const eliminarOrden = async (id: string): Promise<void> => {
  await api.delete(`/ordenes-entrega/${id}`)
}

export const ordenEntregaService = {
  getOrdenes,
  getOrdenesPendientes,
  getOrden,
  getOrdenConPesajes,
  crearOrden,
  actualizarOrden,
  registrarEntrega,
  desasociarPesaje,
  cancelarOrden,
  completarOrden,
  eliminarOrden,
}

export default ordenEntregaService
