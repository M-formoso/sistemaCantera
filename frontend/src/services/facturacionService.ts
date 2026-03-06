import api from './api'

// Tipos
export interface Factura {
  id: string
  numero_factura: string
  punto_venta: number
  tipo_comprobante: string
  empresa_id: string
  empresa_nombre?: string
  fecha_emision: string
  fecha_vencimiento?: string
  subtotal: number
  descuento: number
  iva_21: number
  iva_10_5: number
  iva_27: number
  percepciones_iibb: number
  percepciones_iva: number
  otros_impuestos: number
  total: number
  saldo_pendiente: number
  estado: 'pendiente' | 'parcial' | 'pagada' | 'anulada'
  cae?: string
  cae_vencimiento?: string
  factura_original_id?: string
  observaciones?: string
  anulada: boolean
  created_at: string
  porcentaje_pagado?: number
  esta_pagada?: boolean
  remitos?: RemitoParaFactura[]
  pagos?: PagoFactura[]
}

export interface RemitoParaFactura {
  id: string
  numero_remito: number
  fecha: string
  cliente: string
  producto: string
  peso_neto: number
  importe: number
  saldo_pendiente: number
  facturado: boolean
}

export interface PagoFactura {
  id: string
  factura_id: string
  fecha: string
  monto: number
  forma_pago: string
  banco?: string
  numero_cheque?: string
  fecha_cheque?: string
  cuit_emisor?: string
  es_retencion: boolean
  tipo_retencion?: string
  numero_certificado?: string
  referencia?: string
  observaciones?: string
  anulado: boolean
  created_at: string
}

export interface EstadoCuentaItem {
  fecha: string
  tipo: string
  numero: string
  descripcion: string
  debe: number
  haber: number
  saldo: number
}

export interface EstadoCuenta {
  empresa_id: string
  empresa_nombre: string
  cuit?: string
  saldo_inicial: number
  movimientos: EstadoCuentaItem[]
  saldo_final: number
  fecha_desde: string
  fecha_hasta: string
}

export interface FacturaCreate {
  empresa_id: string
  tipo_comprobante: string
  punto_venta?: number
  fecha_emision: string
  fecha_vencimiento?: string
  subtotal?: number
  descuento?: number
  iva_21?: number
  iva_10_5?: number
  iva_27?: number
  percepciones_iibb?: number
  percepciones_iva?: number
  otros_impuestos?: number
  total?: number
  remito_ids?: string[]
  factura_original_id?: string
  cae?: string
  cae_vencimiento?: string
  observaciones?: string
}

export interface PagoFacturaCreate {
  factura_id: string
  fecha: string
  monto: number
  forma_pago: string
  banco?: string
  numero_cheque?: string
  fecha_cheque?: string
  cuit_emisor?: string
  es_retencion?: boolean
  tipo_retencion?: string
  numero_certificado?: string
  referencia?: string
  observaciones?: string
}

export interface PagoRemitoCreate {
  remito_id: string
  fecha: string
  monto: number
  forma_pago: string
  banco?: string
  numero_cheque?: string
  fecha_cheque?: string
  cuit_emisor?: string
  es_retencion?: boolean
  tipo_retencion?: string
  numero_certificado?: string
  referencia?: string
  observaciones?: string
}

// Constantes
export const TIPOS_COMPROBANTE = [
  { value: 'factura_a', label: 'Factura A' },
  { value: 'factura_b', label: 'Factura B' },
  { value: 'factura_c', label: 'Factura C' },
  { value: 'nota_credito_a', label: 'Nota de Crédito A' },
  { value: 'nota_credito_b', label: 'Nota de Crédito B' },
  { value: 'nota_credito_c', label: 'Nota de Crédito C' },
  { value: 'nota_debito_a', label: 'Nota de Débito A' },
  { value: 'nota_debito_b', label: 'Nota de Débito B' },
  { value: 'nota_debito_c', label: 'Nota de Débito C' },
  { value: 'recibo', label: 'Recibo' },
]

export const FORMAS_PAGO = [
  { value: 'efectivo', label: 'Efectivo' },
  { value: 'transferencia', label: 'Transferencia' },
  { value: 'cheque', label: 'Cheque' },
  { value: 'e_cheque', label: 'E-Cheque' },
  { value: 'tarjeta_debito', label: 'Tarjeta Débito' },
  { value: 'tarjeta_credito', label: 'Tarjeta Crédito' },
  { value: 'retencion_iibb', label: 'Retención IIBB' },
  { value: 'retencion_ganancias', label: 'Retención Ganancias' },
  { value: 'retencion_suss', label: 'Retención SUSS' },
  { value: 'retencion_iva', label: 'Retención IVA' },
  { value: 'otro', label: 'Otro' },
]

export const TIPOS_RETENCION = [
  { value: 'iibb', label: 'IIBB' },
  { value: 'ganancias', label: 'Ganancias' },
  { value: 'iva', label: 'IVA' },
  { value: 'suss', label: 'SUSS' },
]

// Servicio
export const facturacionService = {
  // Facturas
  getFacturas: async (params?: {
    empresa_id?: string
    estado?: string
    tipo_comprobante?: string
    fecha_desde?: string
    fecha_hasta?: string
    skip?: number
    limit?: number
  }): Promise<Factura[]> => {
    const { data } = await api.get('/facturacion/facturas', { params })
    return data
  },

  getFacturasPendientes: async (empresa_id?: string): Promise<Factura[]> => {
    const { data } = await api.get('/facturacion/facturas/pendientes', {
      params: { empresa_id }
    })
    return data
  },

  getFactura: async (id: string): Promise<Factura> => {
    const { data } = await api.get(`/facturacion/facturas/${id}`)
    return data
  },

  crearFactura: async (factura: FacturaCreate): Promise<Factura> => {
    const { data } = await api.post('/facturacion/facturas', factura)
    return data
  },

  actualizarFactura: async (id: string, factura: Partial<FacturaCreate>): Promise<Factura> => {
    const { data } = await api.put(`/facturacion/facturas/${id}`, factura)
    return data
  },

  anularFactura: async (id: string, motivo: string): Promise<void> => {
    await api.delete(`/facturacion/facturas/${id}`, { params: { motivo } })
  },

  // Pagos de Factura
  getPagosFactura: async (facturaId: string): Promise<PagoFactura[]> => {
    const { data } = await api.get(`/facturacion/facturas/${facturaId}/pagos`)
    return data
  },

  registrarPagoFactura: async (
    facturaId: string,
    pago: Omit<PagoFacturaCreate, 'factura_id'>,
    registrarEnCC: boolean = true
  ): Promise<PagoFactura> => {
    const { data } = await api.post(
      `/facturacion/facturas/${facturaId}/pagos`,
      { ...pago, factura_id: facturaId },
      { params: { registrar_en_cc: registrarEnCC } }
    )
    return data
  },

  anularPagoFactura: async (pagoId: string): Promise<void> => {
    await api.delete(`/facturacion/pagos-factura/${pagoId}`)
  },

  // Pagos de Remito (sin factura)
  registrarPagoRemito: async (
    remitoId: string,
    pago: Omit<PagoRemitoCreate, 'remito_id'>,
    registrarEnCC: boolean = true
  ): Promise<any> => {
    const { data } = await api.post(
      `/facturacion/remitos/${remitoId}/pagos`,
      { ...pago, remito_id: remitoId },
      { params: { registrar_en_cc: registrarEnCC } }
    )
    return data
  },

  // Remitos pendientes
  getRemitosPendientesCliente: async (
    empresaId: string,
    soloSinFacturar: boolean = true,
    soloConSaldo: boolean = true
  ): Promise<RemitoParaFactura[]> => {
    const { data } = await api.get(`/facturacion/clientes/${empresaId}/remitos-pendientes`, {
      params: {
        solo_sin_facturar: soloSinFacturar,
        solo_con_saldo: soloConSaldo
      }
    })
    return data
  },

  // Estado de cuenta
  getEstadoCuenta: async (
    empresaId: string,
    fechaDesde?: string,
    fechaHasta?: string
  ): Promise<EstadoCuenta> => {
    const { data } = await api.get(`/facturacion/clientes/${empresaId}/estado-cuenta`, {
      params: { fecha_desde: fechaDesde, fecha_hasta: fechaHasta }
    })
    return data
  },

  descargarEstadoCuentaPDF: async (
    empresaId: string,
    fechaDesde?: string,
    fechaHasta?: string
  ): Promise<Blob> => {
    const { data } = await api.get(`/facturacion/clientes/${empresaId}/estado-cuenta/pdf`, {
      params: { fecha_desde: fechaDesde, fecha_hasta: fechaHasta },
      responseType: 'blob'
    })
    return data
  },
}

export default facturacionService
