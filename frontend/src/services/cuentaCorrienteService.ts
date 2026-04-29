import api from './api'

export interface MovimientoCC {
  id: string
  empresa_id: string
  tipo: 'cargo' | 'pago' | 'ajuste'
  monto: number
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
  monto: number
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

// Actualizar monto de un cargo
export const actualizarMontoCargo = async (
  movimientoId: string,
  monto: number,
  precioUnitario?: number
): Promise<MovimientoCC> => {
  const { data } = await api.put<MovimientoCC>(`/cuenta-corriente/${movimientoId}/monto`, {
    monto,
    precio_unitario: precioUnitario
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
}

export default cuentaCorrienteService
