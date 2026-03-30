/**
 * Servicio de Tesorería para comunicación con la API
 */
import api from './api'
import type {
  // Cheques
  Cheque, ChequeCreate, ChequeUpdate, PaginatedCheques,
  DepositarChequeRequest, CobrarChequeRequest, RechazarChequeRequest, EntregarChequeRequest,
  FiltrosCheques,
  // Movimientos
  MovimientoTesoreria, MovimientoTesoreriaCreate, PaginatedMovimientos,
  AnularMovimientoRequest, FiltrosMovimientos,
  // Consolidados
  MovimientosConsolidadosResponse,
  // Cajas
  CajaEfectivo, CajaEfectivoCreate, CajaEfectivoUpdate,
  MovimientoCaja, MovimientoCajaCreate,
  // Cuentas bancarias
  CuentaBancariaTesoreria, CuentaBancariaCreate, CuentaBancariaUpdate,
  MovimientoBancario,
  // Gastos
  Gasto, GastoCreate, GastoUpdate, PaginatedGastos, FiltrosGastos,
  // Recibos
  Recibo,
  // Resumen
  ResumenTesoreria
} from '@/types/tesoreria'


// ==================== CONSTANTES ====================

export const constantesService = {
  async getTiposCheque() {
    const { data } = await api.get<Array<{ value: string; label: string }>>('/tesoreria/constantes/tipos-cheque')
    return data
  },

  async getOrigenesCheque() {
    const { data } = await api.get<Array<{ value: string; label: string }>>('/tesoreria/constantes/origenes-cheque')
    return data
  },

  async getEstadosCheque() {
    const { data } = await api.get<Array<{ value: string; label: string; color: string }>>('/tesoreria/constantes/estados-cheque')
    return data
  },

  async getMetodosPago() {
    const { data } = await api.get<Array<{ value: string; label: string }>>('/tesoreria/constantes/metodos-pago')
    return data
  },

  async getBancos() {
    const { data } = await api.get<Array<{ value: string; label: string }>>('/tesoreria/constantes/bancos')
    return data
  },

  async getCategoriasGasto() {
    const { data } = await api.get<Array<{ value: string; label: string }>>('/tesoreria/constantes/categorias-gasto')
    return data
  },
}


// ==================== RESUMEN ====================

export const resumenService = {
  async getResumen(fechaDesde?: string, fechaHasta?: string): Promise<ResumenTesoreria> {
    const { data } = await api.get<ResumenTesoreria>('/tesoreria/resumen', {
      params: { fecha_desde: fechaDesde, fecha_hasta: fechaHasta }
    })
    return data
  },
}


// ==================== CHEQUES ====================

export const chequesService = {
  async getCheques(filtros?: FiltrosCheques): Promise<PaginatedCheques> {
    const { data } = await api.get<PaginatedCheques>('/tesoreria/cheques', { params: filtros })
    return data
  },

  async getCheque(chequeId: string): Promise<Cheque> {
    const { data } = await api.get<Cheque>(`/tesoreria/cheques/${chequeId}`)
    return data
  },

  async crearCheque(cheque: ChequeCreate): Promise<Cheque> {
    const { data } = await api.post<Cheque>('/tesoreria/cheques', cheque)
    return data
  },

  async actualizarCheque(chequeId: string, cheque: ChequeUpdate): Promise<Cheque> {
    const { data } = await api.put<Cheque>(`/tesoreria/cheques/${chequeId}`, cheque)
    return data
  },

  async depositarCheque(chequeId: string, request: DepositarChequeRequest): Promise<Cheque> {
    const { data } = await api.post<Cheque>(`/tesoreria/cheques/${chequeId}/depositar`, request)
    return data
  },

  async cobrarCheque(chequeId: string, request: CobrarChequeRequest): Promise<Cheque> {
    const { data } = await api.post<Cheque>(`/tesoreria/cheques/${chequeId}/cobrar`, request)
    return data
  },

  async rechazarCheque(chequeId: string, request: RechazarChequeRequest): Promise<Cheque> {
    const { data } = await api.post<Cheque>(`/tesoreria/cheques/${chequeId}/rechazar`, request)
    return data
  },

  async entregarCheque(chequeId: string, request: EntregarChequeRequest): Promise<Cheque> {
    const { data } = await api.post<Cheque>(`/tesoreria/cheques/${chequeId}/entregar`, request)
    return data
  },

  async eliminarCheque(chequeId: string): Promise<void> {
    await api.delete(`/tesoreria/cheques/${chequeId}`)
  },
}


// ==================== MOVIMIENTOS TESORERÍA ====================

export const movimientosService = {
  async getMovimientos(filtros?: FiltrosMovimientos): Promise<PaginatedMovimientos> {
    const { data } = await api.get<PaginatedMovimientos>('/tesoreria/movimientos', { params: filtros })
    return data
  },

  async getMovimiento(movimientoId: string): Promise<MovimientoTesoreria> {
    const { data } = await api.get<MovimientoTesoreria>(`/tesoreria/movimientos/${movimientoId}`)
    return data
  },

  async crearMovimiento(movimiento: MovimientoTesoreriaCreate): Promise<MovimientoTesoreria> {
    const { data } = await api.post<MovimientoTesoreria>('/tesoreria/movimientos', movimiento)
    return data
  },

  async anularMovimiento(movimientoId: string, request: AnularMovimientoRequest): Promise<MovimientoTesoreria> {
    const { data } = await api.post<MovimientoTesoreria>(`/tesoreria/movimientos/${movimientoId}/anular`, request)
    return data
  },
}


// ==================== MOVIMIENTOS CONSOLIDADOS ====================

export const consolidadosService = {
  async getMovimientosConsolidados(params?: {
    skip?: number
    limit?: number
    tipo?: string
    es_ingreso?: boolean
    fecha_desde?: string
    fecha_hasta?: string
    buscar?: string
  }): Promise<MovimientosConsolidadosResponse> {
    const { data } = await api.get<MovimientosConsolidadosResponse>('/tesoreria/movimientos-consolidados', { params })
    return data
  },
}


// ==================== CAJAS DE EFECTIVO ====================

export const cajasService = {
  async getCajas(soloActivas = true): Promise<CajaEfectivo[]> {
    const { data } = await api.get<CajaEfectivo[]>('/tesoreria/cajas', {
      params: { solo_activas: soloActivas }
    })
    return data
  },

  async getCaja(cajaId: string): Promise<CajaEfectivo> {
    const { data } = await api.get<CajaEfectivo>(`/tesoreria/cajas/${cajaId}`)
    return data
  },

  async crearCaja(caja: CajaEfectivoCreate): Promise<CajaEfectivo> {
    const { data } = await api.post<CajaEfectivo>('/tesoreria/cajas', caja)
    return data
  },

  async actualizarCaja(cajaId: string, caja: CajaEfectivoUpdate): Promise<CajaEfectivo> {
    const { data } = await api.put<CajaEfectivo>(`/tesoreria/cajas/${cajaId}`, caja)
    return data
  },

  async crearMovimientoCaja(movimiento: MovimientoCajaCreate): Promise<MovimientoCaja> {
    const { data } = await api.post<MovimientoCaja>('/tesoreria/cajas/movimientos', movimiento)
    return data
  },

  async getMovimientosCaja(
    cajaId: string,
    params?: { fecha_desde?: string; fecha_hasta?: string; skip?: number; limit?: number }
  ): Promise<{ items: MovimientoCaja[]; total: number; skip: number; limit: number }> {
    const { data } = await api.get<{ items: MovimientoCaja[]; total: number; skip: number; limit: number }>(
      `/tesoreria/cajas/${cajaId}/movimientos`,
      { params }
    )
    return data
  },
}


// ==================== CUENTAS BANCARIAS ====================

export const cuentasBancariasService = {
  async getCuentas(soloActivas = true): Promise<CuentaBancariaTesoreria[]> {
    const { data } = await api.get<CuentaBancariaTesoreria[]>('/tesoreria/cuentas-bancarias', {
      params: { solo_activas: soloActivas }
    })
    return data
  },

  async getCuenta(cuentaId: string): Promise<CuentaBancariaTesoreria> {
    const { data } = await api.get<CuentaBancariaTesoreria>(`/tesoreria/cuentas-bancarias/${cuentaId}`)
    return data
  },

  async crearCuenta(cuenta: CuentaBancariaCreate): Promise<CuentaBancariaTesoreria> {
    const { data } = await api.post<CuentaBancariaTesoreria>('/tesoreria/cuentas-bancarias', cuenta)
    return data
  },

  async actualizarCuenta(cuentaId: string, cuenta: CuentaBancariaUpdate): Promise<CuentaBancariaTesoreria> {
    const { data } = await api.put<CuentaBancariaTesoreria>(`/tesoreria/cuentas-bancarias/${cuentaId}`, cuenta)
    return data
  },

  async getMovimientosBancarios(
    cuentaId: string,
    params?: { fecha_desde?: string; fecha_hasta?: string; skip?: number; limit?: number }
  ): Promise<{ items: MovimientoBancario[]; total: number; skip: number; limit: number }> {
    const { data } = await api.get<{ items: MovimientoBancario[]; total: number; skip: number; limit: number }>(
      `/tesoreria/cuentas-bancarias/${cuentaId}/movimientos`,
      { params }
    )
    return data
  },
}


// ==================== GASTOS ====================

export const gastosService = {
  async getGastos(filtros?: FiltrosGastos): Promise<PaginatedGastos> {
    const { data } = await api.get<PaginatedGastos>('/tesoreria/gastos', { params: filtros })
    return data
  },

  async getGasto(gastoId: string): Promise<Gasto> {
    const { data } = await api.get<Gasto>(`/tesoreria/gastos/${gastoId}`)
    return data
  },

  async crearGasto(gasto: GastoCreate): Promise<Gasto> {
    const { data } = await api.post<Gasto>('/tesoreria/gastos', gasto)
    return data
  },

  async actualizarGasto(gastoId: string, gasto: GastoUpdate): Promise<Gasto> {
    const { data } = await api.put<Gasto>(`/tesoreria/gastos/${gastoId}`, gasto)
    return data
  },

  async anularGasto(gastoId: string, motivo: string): Promise<Gasto> {
    const { data } = await api.post<Gasto>(`/tesoreria/gastos/${gastoId}/anular`, { motivo })
    return data
  },
}


// ==================== RECIBOS ====================

export const recibosService = {
  async getRecibos(params?: {
    empresa_id?: string
    fecha_desde?: string
    fecha_hasta?: string
    skip?: number
    limit?: number
  }): Promise<{ items: Recibo[]; total: number; skip: number; limit: number }> {
    const { data } = await api.get<{ items: Recibo[]; total: number; skip: number; limit: number }>(
      '/tesoreria/recibos',
      { params }
    )
    return data
  },
}


// ==================== SERVICIO PRINCIPAL ====================

const tesoreriaService = {
  constantes: constantesService,
  resumen: resumenService,
  cheques: chequesService,
  movimientos: movimientosService,
  consolidados: consolidadosService,
  cajas: cajasService,
  cuentasBancarias: cuentasBancariasService,
  gastos: gastosService,
  recibos: recibosService,
}

export default tesoreriaService
