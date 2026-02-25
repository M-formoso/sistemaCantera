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

export const getCategorias = async (tipo?: TipoMovimiento) => {
  const params = new URLSearchParams()
  if (tipo) params.append('tipo', tipo)
  const { data } = await api.get<CategoriaFinanzas[]>(`/finanzas/categorias?${params.toString()}`)
  return data
}

export const createCategoria = async (categoria: CategoriaFinanzasCreate) => {
  const { data } = await api.post<CategoriaFinanzas>('/finanzas/categorias', categoria)
  return data
}

export const updateCategoria = async (id: string, categoria: Partial<CategoriaFinanzasCreate>) => {
  const { data } = await api.put<CategoriaFinanzas>(`/finanzas/categorias/${id}`, categoria)
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

export const getMovimientos = async (filters: MovimientosFilters = {}) => {
  const params = new URLSearchParams()
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      params.append(key, String(value))
    }
  })
  const { data } = await api.get<MovimientoFinanciero[]>(`/finanzas/movimientos?${params.toString()}`)
  return data
}

export const getMovimiento = async (id: string) => {
  const { data } = await api.get<MovimientoFinanciero>(`/finanzas/movimientos/${id}`)
  return data
}

export const createMovimiento = async (movimiento: MovimientoFinancieroCreate) => {
  const { data } = await api.post<MovimientoFinanciero>('/finanzas/movimientos', movimiento)
  return data
}

export const updateMovimiento = async (id: string, movimiento: Partial<MovimientoFinancieroCreate>) => {
  const { data } = await api.put<MovimientoFinanciero>(`/finanzas/movimientos/${id}`, movimiento)
  return data
}

export const deleteMovimiento = async (id: string) => {
  const { data } = await api.delete<MovimientoFinanciero>(`/finanzas/movimientos/${id}`)
  return data
}

// ==================== RESÚMENES ====================

export const getResumen = async (fechaDesde?: string, fechaHasta?: string) => {
  const params = new URLSearchParams()
  if (fechaDesde) params.append('fecha_desde', fechaDesde)
  if (fechaHasta) params.append('fecha_hasta', fechaHasta)
  const { data } = await api.get<ResumenFinanciero>(`/finanzas/resumen?${params.toString()}`)
  return data
}

export const getResumenPorCategoria = async (
  tipo?: TipoMovimiento,
  fechaDesde?: string,
  fechaHasta?: string
) => {
  const params = new URLSearchParams()
  if (tipo) params.append('tipo', tipo)
  if (fechaDesde) params.append('fecha_desde', fechaDesde)
  if (fechaHasta) params.append('fecha_hasta', fechaHasta)
  const { data } = await api.get<ResumenPorCategoria[]>(`/finanzas/resumen/categorias?${params.toString()}`)
  return data
}

export const getResumenDiario = async (dias: number = 30) => {
  const { data } = await api.get<{ fecha: string; ingresos: number; egresos: number }[]>(`/finanzas/resumen/diario?dias=${dias}`)
  return data
}

// ==================== CUENTAS BANCARIAS ====================

export const getCuentas = async () => {
  const { data } = await api.get<CuentaBancaria[]>('/finanzas/cuentas')
  return data
}

export const getCuenta = async (id: string) => {
  const { data } = await api.get<CuentaBancaria>(`/finanzas/cuentas/${id}`)
  return data
}

export const createCuenta = async (cuenta: Partial<CuentaBancaria>) => {
  const { data } = await api.post<CuentaBancaria>('/finanzas/cuentas', cuenta)
  return data
}

export const updateCuenta = async (id: string, cuenta: Partial<CuentaBancaria>) => {
  const { data } = await api.put<CuentaBancaria>(`/finanzas/cuentas/${id}`, cuenta)
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
