import api from './api'

// ============== TIPOS ==============

export interface VentaPorMaterial {
  material: string
  cantidad_pesajes: number
  total_kg: number
  total_toneladas: number
  importe_total: number
  precio_promedio: number
}

export interface ReporteVentasMaterial {
  fecha_desde: string
  fecha_hasta: string
  materiales: VentaPorMaterial[]
  total_kg: number
  total_toneladas: number
  total_importe: number
  cantidad_pesajes: number
}

export interface VentaPorSemana {
  semana: number
  anio: number
  fecha_inicio: string
  fecha_fin: string
  cantidad_pesajes: number
  total_kg: number
  total_toneladas: number
  importe_total: number
}

export interface ReporteVentasSemanal {
  fecha_desde: string
  fecha_hasta: string
  material?: string
  semanas: VentaPorSemana[]
  total_kg: number
  total_toneladas: number
  total_importe: number
}

export interface GastoPorCategoria {
  categoria: string
  cantidad: number
  total: number
  porcentaje: number
}

export interface ReporteGastos {
  fecha_desde: string
  fecha_hasta: string
  categorias: GastoPorCategoria[]
  total_gastos: number
  total_combustible: number
  total_servicios: number
  total_repuestos: number
}

export interface MaquinaActividad {
  id: string
  identificador: string
  tipo: string
  cantidad_pesajes: number
  total_kg: number
  total_combustible: number
  cantidad_servicios: number
  costo_servicios: number
  dias_activa: number
}

export interface ReporteMaquinaria {
  fecha_desde: string
  fecha_hasta: string
  maquinas: MaquinaActividad[]
  total_maquinas_activas: number
  total_combustible: number
  total_costo_servicios: number
}

export interface ClienteTop {
  id: string
  nombre: string
  cantidad_pesajes: number
  total_kg: number
  total_toneladas: number
  importe_total: number
  porcentaje_total: number
}

export interface ReporteTopClientes {
  fecha_desde: string
  fecha_hasta: string
  clientes: ClienteTop[]
  total_clientes: number
  total_general: number
}

export interface ResumenGeneral {
  fecha_desde: string
  fecha_hasta: string
  cantidad_pesajes: number
  total_kg: number
  total_toneladas: number
  importe_total_ventas: number
  total_gastos: number
  gasto_combustible: number
  gasto_servicios: number
  gasto_repuestos: number
  maquinas_activas: number
  cliente_top_nombre?: string
  cliente_top_kg?: number
  material_top_nombre?: string
  material_top_kg?: number
}

// ============== SERVICIO ==============

export const reportesService = {
  // Obtener lista de materiales disponibles
  async getMateriales(): Promise<string[]> {
    const response = await api.get<string[]>('/reportes/materiales')
    return response.data
  },

  // Obtener resumen general
  async getResumen(fechaDesde?: string, fechaHasta?: string): Promise<ResumenGeneral> {
    const params: Record<string, string> = {}
    if (fechaDesde) params.fecha_desde = fechaDesde
    if (fechaHasta) params.fecha_hasta = fechaHasta

    const response = await api.get<ResumenGeneral>('/reportes/resumen', { params })
    return response.data
  },

  // Obtener ventas por material
  async getVentasPorMaterial(fechaDesde?: string, fechaHasta?: string): Promise<ReporteVentasMaterial> {
    const params: Record<string, string> = {}
    if (fechaDesde) params.fecha_desde = fechaDesde
    if (fechaHasta) params.fecha_hasta = fechaHasta

    const response = await api.get<ReporteVentasMaterial>('/reportes/ventas-material', { params })
    return response.data
  },

  // Obtener ventas semanales
  async getVentasSemanales(fechaDesde?: string, fechaHasta?: string, material?: string): Promise<ReporteVentasSemanal> {
    const params: Record<string, string> = {}
    if (fechaDesde) params.fecha_desde = fechaDesde
    if (fechaHasta) params.fecha_hasta = fechaHasta
    if (material) params.material = material

    const response = await api.get<ReporteVentasSemanal>('/reportes/ventas-semanal', { params })
    return response.data
  },

  // Obtener reporte de gastos
  async getGastos(fechaDesde?: string, fechaHasta?: string): Promise<ReporteGastos> {
    const params: Record<string, string> = {}
    if (fechaDesde) params.fecha_desde = fechaDesde
    if (fechaHasta) params.fecha_hasta = fechaHasta

    const response = await api.get<ReporteGastos>('/reportes/gastos', { params })
    return response.data
  },

  // Obtener reporte de maquinaria
  async getMaquinaria(fechaDesde?: string, fechaHasta?: string): Promise<ReporteMaquinaria> {
    const params: Record<string, string> = {}
    if (fechaDesde) params.fecha_desde = fechaDesde
    if (fechaHasta) params.fecha_hasta = fechaHasta

    const response = await api.get<ReporteMaquinaria>('/reportes/maquinaria', { params })
    return response.data
  },

  // Obtener top clientes
  async getTopClientes(fechaDesde?: string, fechaHasta?: string, limite?: number): Promise<ReporteTopClientes> {
    const params: Record<string, string | number> = {}
    if (fechaDesde) params.fecha_desde = fechaDesde
    if (fechaHasta) params.fecha_hasta = fechaHasta
    if (limite) params.limite = limite

    const response = await api.get<ReporteTopClientes>('/reportes/top-clientes', { params })
    return response.data
  },

  // Exportar a PDF
  async exportarPDF(
    tipo: 'resumen' | 'ventas-material' | 'ventas-semanal' | 'gastos' | 'maquinaria' | 'top-clientes',
    fechaDesde?: string,
    fechaHasta?: string,
    material?: string
  ): Promise<void> {
    const params: Record<string, string> = { tipo }
    if (fechaDesde) params.fecha_desde = fechaDesde
    if (fechaHasta) params.fecha_hasta = fechaHasta
    if (material) params.material = material

    const response = await api.get('/reportes/exportar-pdf', {
      params,
      responseType: 'blob'
    })

    // Descargar el archivo
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `reporte_${tipo}_${new Date().toISOString().split('T')[0]}.pdf`)
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
  }
}

export default reportesService
