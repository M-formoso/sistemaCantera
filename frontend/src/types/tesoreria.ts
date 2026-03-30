/**
 * Tipos TypeScript para el módulo de Tesorería
 */

// ==================== CONSTANTES ====================

export const TIPOS_CHEQUE = [
  { value: 'fisico', label: 'Cheque Físico' },
  { value: 'echeq', label: 'E-Cheq' },
] as const

export const ORIGENES_CHEQUE = [
  { value: 'recibido_cliente', label: 'Recibido de Cliente' },
  { value: 'recibido_proveedor', label: 'Recibido de Proveedor' },
  { value: 'emitido', label: 'Emitido (Propio)' },
] as const

export const ESTADOS_CHEQUE = [
  { value: 'en_cartera', label: 'En Cartera', color: 'blue' },
  { value: 'depositado', label: 'Depositado', color: 'yellow' },
  { value: 'cobrado', label: 'Cobrado', color: 'green' },
  { value: 'entregado', label: 'Entregado', color: 'purple' },
  { value: 'rechazado', label: 'Rechazado', color: 'red' },
  { value: 'anulado', label: 'Anulado', color: 'gray' },
] as const

export const METODOS_PAGO = [
  { value: 'efectivo', label: 'Efectivo' },
  { value: 'transferencia', label: 'Transferencia' },
  { value: 'cheque', label: 'Cheque' },
] as const

export const BANCOS_ARGENTINA = [
  { value: 'banco_nacion', label: 'Banco Nación' },
  { value: 'banco_provincia', label: 'Banco Provincia' },
  { value: 'banco_ciudad', label: 'Banco Ciudad' },
  { value: 'banco_santander', label: 'Banco Santander' },
  { value: 'banco_galicia', label: 'Banco Galicia' },
  { value: 'banco_bbva', label: 'Banco BBVA' },
  { value: 'banco_macro', label: 'Banco Macro' },
  { value: 'banco_hsbc', label: 'Banco HSBC' },
  { value: 'banco_credicoop', label: 'Banco Credicoop' },
  { value: 'banco_patagonia', label: 'Banco Patagonia' },
  { value: 'banco_supervielle', label: 'Banco Supervielle' },
  { value: 'banco_icbc', label: 'Banco ICBC' },
  { value: 'banco_hipotecario', label: 'Banco Hipotecario' },
  { value: 'otro', label: 'Otro' },
] as const

export const CATEGORIAS_GASTO = [
  { value: 'combustible', label: 'Combustible' },
  { value: 'repuestos', label: 'Repuestos' },
  { value: 'mantenimiento', label: 'Mantenimiento' },
  { value: 'sueldos', label: 'Sueldos' },
  { value: 'servicios', label: 'Servicios' },
  { value: 'impuestos', label: 'Impuestos' },
  { value: 'alquileres', label: 'Alquileres' },
  { value: 'seguros', label: 'Seguros' },
  { value: 'administrativos', label: 'Gastos Administrativos' },
  { value: 'otros', label: 'Otros' },
] as const

// ==================== TIPOS DE ENUM ====================

export type TipoCheque = typeof TIPOS_CHEQUE[number]['value']
export type OrigenCheque = typeof ORIGENES_CHEQUE[number]['value']
export type EstadoCheque = typeof ESTADOS_CHEQUE[number]['value']
export type MetodoPago = typeof METODOS_PAGO[number]['value']
export type CategoriaGasto = typeof CATEGORIAS_GASTO[number]['value']

// ==================== CHEQUE ====================

export interface Cheque {
  id: string
  numero: string
  tipo: TipoCheque
  origen: OrigenCheque
  estado: EstadoCheque
  monto: number
  fecha_emision?: string
  fecha_vencimiento: string
  fecha_cobro?: string
  fecha_deposito?: string
  fecha_entrega?: string
  banco_origen?: string
  cuenta_destino_id?: string
  banco_destino?: string
  empresa_id?: string
  librador?: string
  cuit_librador?: string
  notas?: string
  motivo_rechazo?: string
  concepto_entrega?: string
  registrado_por_id: string
  cobrado_por_id?: string
  fecha_registro: string
  activo: boolean
  created_at: string
  updated_at: string
  // Campos enriquecidos
  empresa_nombre?: string
  registrado_por_nombre?: string
  cobrado_por_nombre?: string
  cuenta_destino_nombre?: string
  dias_para_vencimiento?: number
}

export interface ChequeCreate {
  numero: string
  tipo?: TipoCheque
  origen?: OrigenCheque
  monto: number
  fecha_emision?: string
  fecha_vencimiento: string
  banco_origen?: string
  cuenta_destino_id?: string
  banco_destino?: string
  empresa_id?: string
  librador?: string
  cuit_librador?: string
  notas?: string
}

export interface ChequeUpdate {
  numero?: string
  tipo?: TipoCheque
  origen?: OrigenCheque
  estado?: EstadoCheque
  monto?: number
  fecha_emision?: string
  fecha_vencimiento?: string
  banco_origen?: string
  cuenta_destino_id?: string
  banco_destino?: string
  empresa_id?: string
  librador?: string
  cuit_librador?: string
  notas?: string
}

export interface ChequeList {
  id: string
  numero: string
  tipo: TipoCheque
  origen: OrigenCheque
  estado: EstadoCheque
  monto: number
  fecha_vencimiento: string
  fecha_cobro?: string
  banco_origen?: string
  empresa_id?: string
  empresa_nombre?: string
  librador?: string
  dias_para_vencimiento?: number
  created_at: string
}

// Acciones de cheque
export interface DepositarChequeRequest {
  cuenta_destino_id: string
  fecha_deposito?: string
  notas?: string
}

export interface CobrarChequeRequest {
  fecha_cobro?: string
  notas?: string
}

export interface RechazarChequeRequest {
  motivo_rechazo: string
  fecha_rechazo?: string
}

export interface EntregarChequeRequest {
  empresa_destino_id?: string
  concepto: string
  fecha_entrega?: string
  notas?: string
}

// ==================== MOVIMIENTO TESORERÍA ====================

export interface MovimientoTesoreria {
  id: string
  tipo: string
  concepto: string
  descripcion?: string
  monto: number
  es_ingreso: boolean
  fecha_movimiento: string
  fecha_valor?: string
  metodo_pago: MetodoPago
  banco_origen?: string
  banco_destino?: string
  cuenta_destino_id?: string
  numero_transferencia?: string
  cheque_id?: string
  empresa_id?: string
  pesaje_id?: string
  cobro_id?: string
  notas?: string
  comprobante?: string
  registrado_por_id: string
  anulado: boolean
  motivo_anulacion?: string
  anulado_por_id?: string
  fecha_anulacion?: string
  activo: boolean
  created_at: string
  updated_at: string
  // Campos enriquecidos
  empresa_nombre?: string
  registrado_por_nombre?: string
  cheque_numero?: string
  pesaje_numero?: number
}

export interface MovimientoTesoreriaCreate {
  tipo: string
  concepto: string
  descripcion?: string
  monto: number
  es_ingreso: boolean
  fecha_movimiento: string
  fecha_valor?: string
  metodo_pago: MetodoPago
  banco_origen?: string
  banco_destino?: string
  cuenta_destino_id?: string
  numero_transferencia?: string
  cheque_id?: string
  empresa_id?: string
  pesaje_id?: string
  cobro_id?: string
  notas?: string
  comprobante?: string
}

export interface MovimientoTesoreriaList {
  id: string
  tipo: string
  concepto: string
  monto: number
  es_ingreso: boolean
  fecha_movimiento: string
  metodo_pago: MetodoPago
  empresa_id?: string
  empresa_nombre?: string
  anulado: boolean
  created_at: string
}

export interface AnularMovimientoRequest {
  motivo: string
}

// ==================== CAJA EFECTIVO ====================

export interface CajaEfectivo {
  id: string
  nombre: string
  descripcion?: string
  saldo_actual: number
  saldo_inicial: number
  moneda: string
  activo: boolean
  es_principal: boolean
  notas?: string
  created_at: string
  updated_at: string
}

export interface CajaEfectivoCreate {
  nombre: string
  descripcion?: string
  saldo_inicial?: number
  moneda?: string
  es_principal?: boolean
  notas?: string
}

export interface CajaEfectivoUpdate {
  nombre?: string
  descripcion?: string
  es_principal?: boolean
  notas?: string
  activo?: boolean
}

// ==================== MOVIMIENTO CAJA ====================

export interface MovimientoCaja {
  id: string
  caja_id: string
  tipo: 'ingreso' | 'egreso'
  concepto: string
  descripcion?: string
  monto: number
  saldo_anterior: number
  saldo_posterior: number
  fecha: string
  movimiento_tesoreria_id?: string
  empresa_id?: string
  registrado_por_id: string
  anulado: boolean
  notas?: string
  created_at: string
  updated_at: string
  // Campos enriquecidos
  caja_nombre?: string
  empresa_nombre?: string
  registrado_por_nombre?: string
}

export interface MovimientoCajaCreate {
  caja_id: string
  tipo: 'ingreso' | 'egreso'
  concepto: string
  descripcion?: string
  monto: number
  fecha: string
  empresa_id?: string
  notas?: string
}

// ==================== CUENTA BANCARIA (extendido) ====================

export interface CuentaBancariaTesoreria {
  id: string
  nombre: string
  banco: string
  tipo_cuenta?: string
  numero_cuenta?: string
  cbu?: string
  alias?: string
  titular?: string
  cuit_titular?: string
  saldo_inicial: number
  saldo_actual: number
  moneda: string
  activo: boolean
  notas?: string
  created_at: string
  updated_at: string
}

export interface CuentaBancariaCreate {
  nombre: string
  banco: string
  tipo_cuenta?: string
  numero_cuenta?: string
  cbu?: string
  alias?: string
  titular?: string
  cuit_titular?: string
  saldo_inicial?: number
  moneda?: string
  notas?: string
}

export interface CuentaBancariaUpdate {
  nombre?: string
  banco?: string
  tipo_cuenta?: string
  numero_cuenta?: string
  cbu?: string
  alias?: string
  titular?: string
  cuit_titular?: string
  notas?: string
  activo?: boolean
}

// ==================== MOVIMIENTO BANCARIO ====================

export interface MovimientoBancario {
  id: string
  cuenta_id: string
  tipo: 'ingreso' | 'egreso'
  concepto: string
  descripcion?: string
  monto: number
  saldo_anterior: number
  saldo_posterior: number
  fecha: string
  fecha_valor?: string
  numero_operacion?: string
  movimiento_tesoreria_id?: string
  cheque_id?: string
  empresa_id?: string
  registrado_por_id: string
  anulado: boolean
  notas?: string
  created_at: string
  updated_at: string
  // Campos enriquecidos
  cuenta_nombre?: string
  cuenta_banco?: string
  empresa_nombre?: string
  registrado_por_nombre?: string
}

export interface MovimientoBancarioCreate {
  cuenta_id: string
  tipo: 'ingreso' | 'egreso'
  concepto: string
  descripcion?: string
  monto: number
  fecha: string
  fecha_valor?: string
  numero_operacion?: string
  empresa_id?: string
  notas?: string
}

// ==================== GASTO ====================

export interface Gasto {
  id: string
  fecha: string
  concepto: string
  descripcion?: string
  categoria?: CategoriaGasto
  monto: number
  empresa_id?: string
  proveedor_nombre?: string
  tipo_comprobante?: string
  numero_comprobante?: string
  comprobante_url?: string
  metodo_pago: MetodoPago
  cuenta_bancaria_id?: string
  caja_id?: string
  cheque_id?: string
  camion_id?: string
  servicio_id?: string
  movimiento_tesoreria_id?: string
  registrado_por_id: string
  notas?: string
  estado: string
  anulado: boolean
  activo: boolean
  created_at: string
  updated_at: string
  // Campos enriquecidos
  empresa_nombre?: string
  cuenta_bancaria_nombre?: string
  caja_nombre?: string
  camion_identificador?: string
  registrado_por_nombre?: string
}

export interface GastoCreate {
  fecha: string
  concepto: string
  descripcion?: string
  categoria?: CategoriaGasto
  monto: number
  empresa_id?: string
  proveedor_nombre?: string
  tipo_comprobante?: string
  numero_comprobante?: string
  comprobante_url?: string
  metodo_pago: MetodoPago
  cuenta_bancaria_id?: string
  caja_id?: string
  cheque_id?: string
  camion_id?: string
  servicio_id?: string
  notas?: string
}

export interface GastoUpdate {
  fecha?: string
  concepto?: string
  descripcion?: string
  categoria?: CategoriaGasto
  monto?: number
  empresa_id?: string
  proveedor_nombre?: string
  tipo_comprobante?: string
  numero_comprobante?: string
  comprobante_url?: string
  notas?: string
}

export interface GastoList {
  id: string
  fecha: string
  concepto: string
  categoria?: CategoriaGasto
  monto: number
  metodo_pago: MetodoPago
  empresa_nombre?: string
  proveedor_nombre?: string
  estado: string
  anulado: boolean
  created_at: string
}

// ==================== RECIBO ====================

export interface Recibo {
  id: string
  numero_recibo: string
  fecha: string
  empresa_id: string
  monto: number
  concepto: string
  metodo_pago: MetodoPago
  cheque_id?: string
  movimiento_tesoreria_id?: string
  cobro_id?: string
  pdf_url?: string
  registrado_por_id: string
  notas?: string
  anulado: boolean
  activo: boolean
  created_at: string
  updated_at: string
  // Campos enriquecidos
  empresa_nombre?: string
  registrado_por_nombre?: string
}

export interface ReciboCreate {
  fecha: string
  empresa_id: string
  monto: number
  concepto: string
  metodo_pago: MetodoPago
  cheque_id?: string
  cobro_id?: string
  notas?: string
}

// ==================== RESUMEN ====================

export interface ResumenTesoreria {
  cheques_en_cartera: number
  total_cheques_cartera: number
  cheques_proximos_vencer: number
  total_proximos_vencer: number
  cheques_vencidos: number
  total_vencidos: number
  total_ingresos_efectivo: number
  total_ingresos_transferencia: number
  total_ingresos_cheque: number
  total_ingresos: number
  total_egresos_efectivo: number
  total_egresos_transferencia: number
  total_egresos_cheque: number
  total_egresos: number
  saldo_periodo: number
  saldo_cajas: number
  saldo_bancos: number
  total_disponible: number
}

// ==================== MOVIMIENTOS CONSOLIDADOS ====================

export interface MovimientoConsolidado {
  id: string
  fecha: string
  tipo: string
  origen: 'cheque' | 'movimiento_tesoreria' | 'movimiento_caja' | 'movimiento_bancario'
  concepto: string
  monto: number
  es_ingreso: boolean
  metodo_pago: MetodoPago
  empresa_nombre?: string
  numero_referencia?: string
  banco?: string
  estado?: EstadoCheque
  created_at: string
}

export interface MovimientosConsolidadosResponse {
  items: MovimientoConsolidado[]
  total: number
  total_ingresos: number
  total_egresos: number
  skip: number
  limit: number
}

// ==================== PAGINACIÓN ====================

export interface PaginatedCheques {
  items: ChequeList[]
  total: number
  skip: number
  limit: number
}

export interface PaginatedMovimientos {
  items: MovimientoTesoreriaList[]
  total: number
  skip: number
  limit: number
}

export interface PaginatedGastos {
  items: GastoList[]
  total: number
  skip: number
  limit: number
}

// ==================== FILTROS ====================

export interface FiltrosCheques {
  skip?: number
  limit?: number
  estado?: EstadoCheque | string
  tipo?: TipoCheque | string
  origen?: OrigenCheque | string
  empresa_id?: string
  fecha_desde?: string
  fecha_hasta?: string
  buscar?: string
  solo_en_cartera?: boolean
  vencidos?: boolean
  proximos_vencer?: boolean
  dias_vencimiento?: number
}

export interface FiltrosMovimientos {
  skip?: number
  limit?: number
  tipo?: string
  es_ingreso?: boolean
  metodo_pago?: MetodoPago | string
  empresa_id?: string
  fecha_desde?: string
  fecha_hasta?: string
  buscar?: string
  incluir_anulados?: boolean
}

export interface FiltrosGastos {
  skip?: number
  limit?: number
  categoria?: CategoriaGasto | string
  metodo_pago?: MetodoPago | string
  empresa_id?: string
  fecha_desde?: string
  fecha_hasta?: string
  buscar?: string
  incluir_anulados?: boolean
}

// ==================== UTILIDADES ====================

export function getEstadoChequeColor(estado: EstadoCheque): string {
  const estadoInfo = ESTADOS_CHEQUE.find(e => e.value === estado)
  return estadoInfo?.color || 'gray'
}

export function getEstadoChequeLabel(estado: EstadoCheque): string {
  const estadoInfo = ESTADOS_CHEQUE.find(e => e.value === estado)
  return estadoInfo?.label || estado
}

export function formatMonto(monto: number): string {
  return new Intl.NumberFormat('es-AR', {
    style: 'currency',
    currency: 'ARS',
  }).format(monto)
}

export function getDiasVencimiento(fechaVencimiento: string): number {
  const hoy = new Date()
  const vencimiento = new Date(fechaVencimiento)
  const diffTime = vencimiento.getTime() - hoy.getTime()
  return Math.ceil(diffTime / (1000 * 60 * 60 * 24))
}

export function getChequeVencimientoStatus(diasParaVencer?: number): {
  label: string
  color: string
} {
  if (diasParaVencer === undefined) {
    return { label: 'Sin fecha', color: 'gray' }
  }
  if (diasParaVencer < 0) {
    return { label: 'Vencido', color: 'red' }
  }
  if (diasParaVencer <= 7) {
    return { label: `${diasParaVencer} días`, color: 'yellow' }
  }
  return { label: `${diasParaVencer} días`, color: 'green' }
}
