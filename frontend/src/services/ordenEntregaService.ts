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

// Crear orden - usar el cliente api con trailing slash
export const crearOrden = async (orden: OrdenEntregaCreate): Promise<OrdenEntrega> => {
  console.log('[crearOrden] Creando orden con datos:', orden)
  const { data } = await api.post<OrdenEntrega>('/ordenes-entrega/', orden)
  console.log('[crearOrden] Orden creada:', data)
  return data
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
