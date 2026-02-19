import api from './api'
import {
  CategoriaFinanzas,
  CategoriaFinanzasCreate,
  MovimientoFinanciero,
  MovimientoFinancieroCreate,
  CuentaBancaria,
  ResumenFinanciero,
  ResumenPorCategoria,
  TipoMovimiento
} from '@/types'

// ==================== CATEGORÍAS ====================

export const getCategorias = async (tipo?: TipoMovimiento): Promise<CategoriaFinanzas[]> => {
  const params = new URLSearchParams()
  if (tipo) params.append('tipo', tipo)
  const { data } = await api.get(`/finanzas/categorias/?${params.toString()}`)
  return data
}

export const createCategoria = async (categoria: CategoriaFinanzasCreate): Promise<CategoriaFinanzas> => {
  const { data } = await api.post('/finanzas/categorias/', categoria)
  return data
}

export const updateCategoria = async (id: string, categoria: Partial<CategoriaFinanzasCreate>): Promise<CategoriaFinanzas> => {
  const { data } = await api.put(`/finanzas/categorias/${id}`, categoria)
  return data
}

// ==================== MOVIMIENTOS ====================

export interface MovimientosFilters {
  tipo?: TipoMovimiento
  categoria_id?: string
  camion_id?: string
  empresa_id?: string
  fecha_desde?: string
  fecha_hasta?: string
  estado?: string
  skip?: number
  limit?: number
}

export const getMovimientos = async (filters: MovimientosFilters = {}): Promise<MovimientoFinanciero[]> => {
  const params = new URLSearchParams()
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      params.append(key, String(value))
    }
  })
  const { data } = await api.get(`/finanzas/movimientos/?${params.toString()}`)
  return data
}

export const getMovimiento = async (id: string): Promise<MovimientoFinanciero> => {
  const { data } = await api.get(`/finanzas/movimientos/${id}`)
  return data
}

export const createMovimiento = async (movimiento: MovimientoFinancieroCreate): Promise<MovimientoFinanciero> => {
  const { data } = await api.post('/finanzas/movimientos/', movimiento)
  return data
}

export const updateMovimiento = async (id: string, movimiento: Partial<MovimientoFinancieroCreate>): Promise<MovimientoFinanciero> => {
  const { data } = await api.put(`/finanzas/movimientos/${id}`, movimiento)
  return data
}

export const deleteMovimiento = async (id: string): Promise<MovimientoFinanciero> => {
  const { data } = await api.delete(`/finanzas/movimientos/${id}`)
  return data
}

// ==================== RESÚMENES ====================

export const getResumen = async (fechaDesde?: string, fechaHasta?: string): Promise<ResumenFinanciero> => {
  const params = new URLSearchParams()
  if (fechaDesde) params.append('fecha_desde', fechaDesde)
  if (fechaHasta) params.append('fecha_hasta', fechaHasta)
  const { data } = await api.get(`/finanzas/resumen/?${params.toString()}`)
  return data
}

export const getResumenPorCategoria = async (
  tipo?: TipoMovimiento,
  fechaDesde?: string,
  fechaHasta?: string
): Promise<ResumenPorCategoria[]> => {
  const params = new URLSearchParams()
  if (tipo) params.append('tipo', tipo)
  if (fechaDesde) params.append('fecha_desde', fechaDesde)
  if (fechaHasta) params.append('fecha_hasta', fechaHasta)
  const { data } = await api.get(`/finanzas/resumen/categorias/?${params.toString()}`)
  return data
}

export const getResumenDiario = async (dias: number = 30): Promise<{ fecha: string; ingresos: number; egresos: number }[]> => {
  const { data } = await api.get(`/finanzas/resumen/diario/?dias=${dias}`)
  return data
}

// ==================== CUENTAS BANCARIAS ====================

export const getCuentas = async (): Promise<CuentaBancaria[]> => {
  const { data } = await api.get('/finanzas/cuentas/')
  return data
}

export const getCuenta = async (id: string): Promise<CuentaBancaria> => {
  const { data } = await api.get(`/finanzas/cuentas/${id}`)
  return data
}

export const createCuenta = async (cuenta: Partial<CuentaBancaria>): Promise<CuentaBancaria> => {
  const { data } = await api.post('/finanzas/cuentas/', cuenta)
  return data
}

export const updateCuenta = async (id: string, cuenta: Partial<CuentaBancaria>): Promise<CuentaBancaria> => {
  const { data } = await api.put(`/finanzas/cuentas/${id}`, cuenta)
  return data
}

export const finanzasService = {
  getCategorias,
  createCategoria,
  updateCategoria,
  getMovimientos,
  getMovimiento,
  createMovimiento,
  updateMovimiento,
  deleteMovimiento,
  getResumen,
  getResumenPorCategoria,
  getResumenDiario,
  getCuentas,
  getCuenta,
  createCuenta,
  updateCuenta
}

export default finanzasService
