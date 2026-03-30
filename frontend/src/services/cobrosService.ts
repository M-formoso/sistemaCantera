import api from './api'

// Tipos
export interface ItemCobro {
  id?: string
  cobro_id?: string
  tipo_item: string
  concepto: 'debe' | 'haber'
  monto: number
  descripcion?: string
  factura_id?: string
  remito_id?: string
  pesaje_id?: string
  banco?: string
  numero_cheque?: string
  fecha_cheque?: string
  cuit_emisor?: string
  referencia_transferencia?: string
  numero_certificado?: string
  movimiento_cc_id?: string
}

export interface CobroCliente {
  id: string
  numero_cobro: number
  empresa_id: string
  empresa_nombre?: string
  fecha: string
  monto_total: number
  monto_aplicado: number
  diferencia: number
  estado: 'borrador' | 'confirmado' | 'aplicado'
  numero_orden_pago?: string
  observaciones?: string
  created_by: string
  confirmed_by?: string
  fecha_confirmacion?: string
  anulado: boolean
  motivo_anulacion?: string
  items: ItemCobro[]
  total_haber?: number
  total_debe?: number
  esta_balanceado?: boolean
  creador_nombre?: string
}

export interface CobroClienteCreate {
  empresa_id: string
  fecha: string
  monto_total: number
  numero_orden_pago?: string
  observaciones?: string
}

export interface CobroClienteCreateWithItems extends CobroClienteCreate {
  items: ItemCobro[]
}

export interface ValidacionCobro {
  valido: boolean
  total_haber: number
  total_debe: number
  diferencia: number
  mensaje: string
  errores: string[]
}

export interface AplicarCobroResponse {
  cobro_id: string
  numero_cobro: number
  movimientos_generados: number
  saldo_a_favor?: number
  mensaje: string
}

export interface FacturaPendiente {
  id: string
  numero_factura: string
  fecha_emision: string
  total: number
  saldo_pendiente: number
}

export interface TicketPendiente {
  id: string
  numero: number
  tipo: string
  fecha: string
  material?: string
  peso_neto?: number
  importe: number
  saldo_pendiente: number
}

export interface DocumentosPendientes {
  empresa_id: string
  empresa_nombre: string
  saldo_cuenta_corriente: number
  facturas: FacturaPendiente[]
  tickets: TicketPendiente[]
  total_pendiente: number
}

// Constantes para tipos de items
export const TIPOS_ITEM_HABER = [
  { value: 'efectivo', label: 'Efectivo' },
  { value: 'transferencia', label: 'Transferencia' },
  { value: 'cheque', label: 'Cheque' },
  { value: 'e_cheque', label: 'E-Cheque' },
  { value: 'retencion_iibb', label: 'Retención IIBB' },
  { value: 'retencion_ganancias', label: 'Retención Ganancias' },
  { value: 'retencion_suss', label: 'Retención SUSS' },
]

export const TIPOS_ITEM_DEBE = [
  { value: 'factura', label: 'Factura' },
  { value: 'ticket', label: 'Ticket/Remito' },
  { value: 'saldo_favor', label: 'Saldo a Favor' },
]

export const cobrosService = {
  // Listar cobros
  async getAll(params?: {
    skip?: number
    limit?: number
    estado?: string
    empresa_id?: string
    fecha_desde?: string
    fecha_hasta?: string
  }): Promise<CobroCliente[]> {
    const response = await api.get<CobroCliente[]>('/cobros', { params })
    return response.data
  },

  // Listar cobros de un cliente
  async getByCliente(empresaId: string, skip = 0, limit = 50): Promise<CobroCliente[]> {
    const response = await api.get<CobroCliente[]>(`/cobros/cliente/${empresaId}`, {
      params: { skip, limit }
    })
    return response.data
  },

  // Obtener un cobro por ID
  async getById(id: string): Promise<CobroCliente> {
    const response = await api.get<CobroCliente>(`/cobros/${id}`)
    return response.data
  },

  // Obtener documentos pendientes de un cliente
  async getDocumentosPendientes(empresaId: string): Promise<DocumentosPendientes> {
    const response = await api.get<DocumentosPendientes>(`/cobros/documentos-pendientes/${empresaId}`)
    return response.data
  },

  // Crear cobro (solo cabecera)
  async crear(data: CobroClienteCreate): Promise<CobroCliente> {
    const response = await api.post<CobroCliente>('/cobros', data)
    return response.data
  },

  // Crear cobro con items
  async crearConItems(data: CobroClienteCreateWithItems): Promise<CobroCliente> {
    const response = await api.post<CobroCliente>('/cobros/con-items', data)
    return response.data
  },

  // Agregar item a un cobro
  async agregarItem(cobroId: string, item: ItemCobro): Promise<ItemCobro> {
    const response = await api.post<ItemCobro>(`/cobros/${cobroId}/items`, item)
    return response.data
  },

  // Eliminar item de un cobro
  async eliminarItem(cobroId: string, itemId: string): Promise<void> {
    await api.delete(`/cobros/${cobroId}/items/${itemId}`)
  },

  // Validar cobro
  async validar(cobroId: string): Promise<ValidacionCobro> {
    const response = await api.get<ValidacionCobro>(`/cobros/${cobroId}/validar`)
    return response.data
  },

  // Confirmar cobro
  async confirmar(cobroId: string): Promise<CobroCliente> {
    const response = await api.post<CobroCliente>(`/cobros/${cobroId}/confirmar`)
    return response.data
  },

  // Aplicar cobro (genera movimientos en CC y tesorería)
  async aplicar(
    cobroId: string,
    options?: {
      caja_efectivo_id?: string
      cuenta_bancaria_id?: string
    }
  ): Promise<AplicarCobroResponse> {
    const response = await api.post<AplicarCobroResponse>(`/cobros/${cobroId}/aplicar`, null, {
      params: options
    })
    return response.data
  },

  // Anular cobro
  async anular(cobroId: string, motivo: string): Promise<void> {
    await api.post(`/cobros/${cobroId}/anular`, null, {
      params: { motivo }
    })
  },
}

export default cobrosService
