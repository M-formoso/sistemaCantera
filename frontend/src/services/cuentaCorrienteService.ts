import api from './api'

export interface MovimientoCC {
  id: string
  empresa_id: string
  tipo: 'cargo' | 'pago' | 'ajuste'
  monto: number  // TOTAL c/IVA
  monto_neto?: number
  monto_iva?: number
  alicuota_iva?: number
  saldo_anterior: number
  saldo_posterior: number
  fecha: string
  descripcion: string
  detalle?: string
  pesaje_id?: string
  movimiento_financiero_id?: string
  numero_comprobante?: string
  tipo_comprobante?: string
  metodo_pago?: string
  referencia_pago?: string
  banco?: string
  anulado: boolean
  created_at: string
  notas?: string
  empresa_nombre?: string
  material?: string
  toneladas?: number
  metros_cubicos?: number
  factor_conversion_m3?: number
}

export interface ResumenCuentaCorriente {
  empresa_id: string
  empresa_nombre: string
  saldo_actual: number
  total_cargos: number
  total_pagos: number
  cantidad_movimientos: number
}

export interface ClienteConDeuda {
  id: string
  nombre: string
  cuit?: string
  saldo: number
}

export interface PagoCreate {
  empresa_id: string
  monto: number  // TOTAL c/IVA
  alicuota_iva?: number
  fecha: string
  descripcion: string
  metodo_pago?: string
  numero_comprobante?: string
  referencia_pago?: string
  banco?: string
  notas?: string
  registrar_ingreso?: boolean
}

export interface AjusteCreate {
  empresa_id: string
  monto: number
  es_credito: boolean
  fecha: string
  descripcion: string
  notas?: string
  alicuota_iva?: number
}

export interface ActualizarMontoCargo {
  monto: number  // NETO
  precio_unitario?: number
  alicuota_iva?: number
}

// Obtener clientes con deuda
export const getClientesConDeuda = async (): Promise<ClienteConDeuda[]> => {
  const { data } = await api.get<ClienteConDeuda[]>('/cuenta-corriente/clientes-con-deuda')
  return data
}

// Obtener resumen de un cliente
export const getResumenCliente = async (empresaId: string): Promise<ResumenCuentaCorriente> => {
  const { data } = await api.get<ResumenCuentaCorriente>(`/cuenta-corriente/cliente/${empresaId}/resumen`)
  return data
}

// Obtener movimientos de un cliente
export const getMovimientosCliente = async (
  empresaId: string,
  fechaDesde?: string,
  fechaHasta?: string
): Promise<MovimientoCC[]> => {
  const params: Record<string, string> = {}
  if (fechaDesde) params.fecha_desde = fechaDesde
  if (fechaHasta) params.fecha_hasta = fechaHasta

  const { data } = await api.get<MovimientoCC[]>(`/cuenta-corriente/cliente/${empresaId}/movimientos`, { params })
  return data
}

// Obtener saldo de un cliente
export const getSaldoCliente = async (empresaId: string): Promise<number> => {
  const { data } = await api.get<{ saldo: number }>(`/cuenta-corriente/cliente/${empresaId}/saldo`)
  return data.saldo
}

// Registrar pago
export const registrarPago = async (pago: PagoCreate): Promise<MovimientoCC> => {
  const { data } = await api.post<MovimientoCC>('/cuenta-corriente/pago', pago)
  return data
}

// Registrar ajuste
export const registrarAjuste = async (ajuste: AjusteCreate): Promise<MovimientoCC> => {
  const { data } = await api.post<MovimientoCC>('/cuenta-corriente/ajuste', ajuste)
  return data
}

// Anular movimiento
export const anularMovimiento = async (movimientoId: string, motivo: string): Promise<MovimientoCC> => {
  const { data } = await api.post<MovimientoCC>(`/cuenta-corriente/${movimientoId}/anular`, { motivo })
  return data
}

// Actualizar monto de un cargo (monto = neto)
export const actualizarMontoCargo = async (
  movimientoId: string,
  monto: number,
  precioUnitario?: number,
  alicuotaIva?: number,
): Promise<MovimientoCC> => {
  const { data } = await api.put<MovimientoCC>(`/cuenta-corriente/${movimientoId}/monto`, {
    monto,
    precio_unitario: precioUnitario,
    alicuota_iva: alicuotaIva,
  })
  return data
}

export interface HistorialMovimientoItem {
  id: string | null
  fecha: string
  usuario_nombre: string
  accion: string
  detalle?: string | null
}

// Obtener historial de un movimiento
export const getHistorialMovimiento = async (movimientoId: string): Promise<HistorialMovimientoItem[]> => {
  const { data } = await api.get<HistorialMovimientoItem[]>(
    `/cuenta-corriente/movimientos/${movimientoId}/historial`
  )
  return data
}

export interface RecalcularResultado {
  empresa_id: string
  movimientos_procesados: number
  movimientos_actualizados: number
  saldo_anterior_empresa: number
  saldo_recalculado: number
}

// Recalcular saldos acumulados de un cliente
export const recalcularSaldosCliente = async (empresaId: string): Promise<RecalcularResultado> => {
  const { data } = await api.post<RecalcularResultado>(
    `/cuenta-corriente/cliente/${empresaId}/recalcular`
  )
  return data
}

// Descargar comprobante PDF de un movimiento
export const descargarComprobantePDF = async (movimientoId: string, filename?: string): Promise<void> => {
  const response = await api.get<Blob>(`/cuenta-corriente/movimientos/${movimientoId}/comprobante-pdf`, {
    responseType: 'blob',
  })
  const blob = new Blob([response.data], { type: 'application/pdf' })
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename || `comprobante_${movimientoId}.pdf`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  window.URL.revokeObjectURL(url)
}

export const cuentaCorrienteService = {
  getClientesConDeuda,
  getResumenCliente,
  getMovimientosCliente,
  getSaldoCliente,
  registrarPago,
  registrarAjuste,
  anularMovimiento,
  actualizarMontoCargo,
  getHistorialMovimiento,
  descargarComprobantePDF,
  recalcularSaldosCliente,
}

export default cuentaCorrienteService
