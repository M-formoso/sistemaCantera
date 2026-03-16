import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  FileText, Download, TrendingUp, TrendingDown, Truck, Users,
  Package, Calendar, Filter, BarChart3, PieChart,
  DollarSign, Fuel, Wrench, Loader2
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { reportesService } from '@/services/reportesService'
import { formatNumber } from '@/lib/utils'

type TipoReporte = 'resumen' | 'ventas-material' | 'ventas-semanal' | 'gastos' | 'maquinaria' | 'top-clientes'

// Función para obtener fecha hace N días
const getFechaHace = (dias: number) => {
  const fecha = new Date()
  fecha.setDate(fecha.getDate() - dias)
  return fecha.toISOString().split('T')[0]
}

export default function ReportesPage() {
  // Estado de filtros
  const [fechaDesde, setFechaDesde] = useState(getFechaHace(30))
  const [fechaHasta, setFechaHasta] = useState(new Date().toISOString().split('T')[0])
  const [materialFiltro, setMaterialFiltro] = useState<string>('')
  const [tipoReporteActivo, setTipoReporteActivo] = useState<TipoReporte>('resumen')
  const [exportando, setExportando] = useState(false)

  // Queries
  const { data: materiales = [] } = useQuery({
    queryKey: ['reportes-materiales'],
    queryFn: () => reportesService.getMateriales(),
  })

  const { data: resumen, isLoading: loadingResumen } = useQuery({
    queryKey: ['reporte-resumen', fechaDesde, fechaHasta],
    queryFn: () => reportesService.getResumen(fechaDesde, fechaHasta),
    enabled: tipoReporteActivo === 'resumen',
  })

  const { data: ventasMaterial, isLoading: loadingVentasMaterial } = useQuery({
    queryKey: ['reporte-ventas-material', fechaDesde, fechaHasta],
    queryFn: () => reportesService.getVentasPorMaterial(fechaDesde, fechaHasta),
    enabled: tipoReporteActivo === 'ventas-material',
  })

  const { data: ventasSemanal, isLoading: loadingVentasSemanal } = useQuery({
    queryKey: ['reporte-ventas-semanal', fechaDesde, fechaHasta, materialFiltro],
    queryFn: () => reportesService.getVentasSemanales(fechaDesde, fechaHasta, materialFiltro || undefined),
    enabled: tipoReporteActivo === 'ventas-semanal',
  })

  const { data: gastos, isLoading: loadingGastos } = useQuery({
    queryKey: ['reporte-gastos', fechaDesde, fechaHasta],
    queryFn: () => reportesService.getGastos(fechaDesde, fechaHasta),
    enabled: tipoReporteActivo === 'gastos',
  })

  const { data: maquinaria, isLoading: loadingMaquinaria } = useQuery({
    queryKey: ['reporte-maquinaria', fechaDesde, fechaHasta],
    queryFn: () => reportesService.getMaquinaria(fechaDesde, fechaHasta),
    enabled: tipoReporteActivo === 'maquinaria',
  })

  const { data: topClientes, isLoading: loadingTopClientes } = useQuery({
    queryKey: ['reporte-top-clientes', fechaDesde, fechaHasta],
    queryFn: () => reportesService.getTopClientes(fechaDesde, fechaHasta, 10),
    enabled: tipoReporteActivo === 'top-clientes',
  })

  const isLoading = loadingResumen || loadingVentasMaterial || loadingVentasSemanal || loadingGastos || loadingMaquinaria || loadingTopClientes

  // Exportar PDF
  const handleExportarPDF = async () => {
    setExportando(true)
    try {
      await reportesService.exportarPDF(
        tipoReporteActivo,
        fechaDesde,
        fechaHasta,
        tipoReporteActivo === 'ventas-semanal' ? materialFiltro || undefined : undefined
      )
    } catch (error) {
      console.error('Error exportando PDF:', error)
      alert('Error al exportar el PDF')
    } finally {
      setExportando(false)
    }
  }

  // Presets de fechas
  const aplicarPreset = (dias: number) => {
    setFechaDesde(getFechaHace(dias))
    setFechaHasta(new Date().toISOString().split('T')[0])
  }

  const tabs = [
    { id: 'resumen', label: 'Resumen', icon: BarChart3 },
    { id: 'ventas-material', label: 'Por Material', icon: Package },
    { id: 'ventas-semanal', label: 'Por Semana', icon: Calendar },
    { id: 'gastos', label: 'Gastos', icon: TrendingDown },
    { id: 'maquinaria', label: 'Maquinaria', icon: Truck },
    { id: 'top-clientes', label: 'Top Clientes', icon: Users },
  ] as const

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <FileText className="h-6 w-6" />
            Reportes
          </h1>
          <p className="text-gray-500 text-sm mt-1">
            Análisis y estadísticas del período seleccionado
          </p>
        </div>
        <Button
          onClick={handleExportarPDF}
          disabled={exportando || isLoading}
          className="bg-red-600 hover:bg-red-700"
        >
          {exportando ? (
            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
          ) : (
            <Download className="h-4 w-4 mr-2" />
          )}
          Exportar PDF
        </Button>
      </div>

      {/* Filtros */}
      <Card>
        <CardContent className="pt-4">
          <div className="flex flex-wrap items-end gap-4">
            <div className="flex items-center gap-2">
              <Filter className="h-4 w-4 text-gray-500" />
              <span className="text-sm font-medium">Período:</span>
            </div>

            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => aplicarPreset(7)}
                className={fechaDesde === getFechaHace(7) ? 'bg-blue-50 border-blue-300' : ''}
              >
                7 días
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => aplicarPreset(30)}
                className={fechaDesde === getFechaHace(30) ? 'bg-blue-50 border-blue-300' : ''}
              >
                30 días
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => aplicarPreset(90)}
                className={fechaDesde === getFechaHace(90) ? 'bg-blue-50 border-blue-300' : ''}
              >
                90 días
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => aplicarPreset(365)}
                className={fechaDesde === getFechaHace(365) ? 'bg-blue-50 border-blue-300' : ''}
              >
                1 año
              </Button>
            </div>

            <div className="flex items-center gap-2">
              <Input
                type="date"
                value={fechaDesde}
                onChange={(e) => setFechaDesde(e.target.value)}
                className="w-40"
              />
              <span className="text-gray-500">a</span>
              <Input
                type="date"
                value={fechaHasta}
                onChange={(e) => setFechaHasta(e.target.value)}
                className="w-40"
              />
            </div>

            {tipoReporteActivo === 'ventas-semanal' && (
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-500">Material:</span>
                <select
                  value={materialFiltro}
                  onChange={(e) => setMaterialFiltro(e.target.value)}
                  className="border rounded-md px-3 py-1.5 text-sm"
                >
                  <option value="">Todos</option>
                  {materiales.map((m) => (
                    <option key={m} value={m}>{m}</option>
                  ))}
                </select>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Tabs */}
      <div className="flex gap-2 border-b pb-2 overflow-x-auto">
        {tabs.map((tab) => (
          <Button
            key={tab.id}
            variant={tipoReporteActivo === tab.id ? 'default' : 'ghost'}
            size="sm"
            onClick={() => setTipoReporteActivo(tab.id)}
            className="flex items-center gap-2 whitespace-nowrap"
          >
            <tab.icon className="h-4 w-4" />
            {tab.label}
          </Button>
        ))}
      </div>

      {/* Contenido según tab activo */}
      {isLoading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
          <span className="ml-2 text-gray-500">Cargando reporte...</span>
        </div>
      ) : (
        <>
          {/* RESUMEN */}
          {tipoReporteActivo === 'resumen' && resumen && (
            <div className="space-y-6">
              {/* Cards de resumen */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <Card>
                  <CardContent className="pt-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-gray-500">Pesajes</p>
                        <p className="text-2xl font-bold">{resumen.cantidad_pesajes}</p>
                      </div>
                      <Package className="h-8 w-8 text-blue-500 opacity-50" />
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardContent className="pt-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-gray-500">Toneladas</p>
                        <p className="text-2xl font-bold">{formatNumber(resumen.total_toneladas, 1)}</p>
                      </div>
                      <TrendingUp className="h-8 w-8 text-green-500 opacity-50" />
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardContent className="pt-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-gray-500">Ventas</p>
                        <p className="text-2xl font-bold">${formatNumber(resumen.importe_total_ventas, 0)}</p>
                      </div>
                      <DollarSign className="h-8 w-8 text-green-500 opacity-50" />
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardContent className="pt-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-gray-500">Gastos</p>
                        <p className="text-2xl font-bold text-red-600">${formatNumber(resumen.total_gastos, 0)}</p>
                      </div>
                      <TrendingDown className="h-8 w-8 text-red-500 opacity-50" />
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Detalle */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg">Desglose de Gastos</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      <div className="flex justify-between items-center">
                        <div className="flex items-center gap-2">
                          <Fuel className="h-4 w-4 text-yellow-500" />
                          <span>Combustible</span>
                        </div>
                        <span className="font-medium">${formatNumber(resumen.gasto_combustible, 0)}</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <div className="flex items-center gap-2">
                          <Wrench className="h-4 w-4 text-blue-500" />
                          <span>Servicios</span>
                        </div>
                        <span className="font-medium">${formatNumber(resumen.gasto_servicios, 0)}</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <div className="flex items-center gap-2">
                          <Package className="h-4 w-4 text-purple-500" />
                          <span>Repuestos</span>
                        </div>
                        <span className="font-medium">${formatNumber(resumen.gasto_repuestos, 0)}</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg">Destacados</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      <div className="flex justify-between items-center">
                        <div className="flex items-center gap-2">
                          <Truck className="h-4 w-4 text-gray-500" />
                          <span>Máquinas Activas</span>
                        </div>
                        <span className="font-bold text-lg">{resumen.maquinas_activas}</span>
                      </div>
                      {resumen.cliente_top_nombre && (
                        <div className="flex justify-between items-center">
                          <div className="flex items-center gap-2">
                            <Users className="h-4 w-4 text-green-500" />
                            <span>Cliente Top</span>
                          </div>
                          <span className="font-medium">{resumen.cliente_top_nombre}</span>
                        </div>
                      )}
                      {resumen.material_top_nombre && (
                        <div className="flex justify-between items-center">
                          <div className="flex items-center gap-2">
                            <Package className="h-4 w-4 text-blue-500" />
                            <span>Material Top</span>
                          </div>
                          <span className="font-medium">{resumen.material_top_nombre}</span>
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              </div>
            </div>
          )}

          {/* VENTAS POR MATERIAL */}
          {tipoReporteActivo === 'ventas-material' && ventasMaterial && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <PieChart className="h-5 w-5" />
                  Ventas por Tipo de Material
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b bg-gray-50">
                        <th className="text-left py-3 px-4">Material</th>
                        <th className="text-right py-3 px-4">Pesajes</th>
                        <th className="text-right py-3 px-4">Kg</th>
                        <th className="text-right py-3 px-4">Toneladas</th>
                        <th className="text-right py-3 px-4">Importe</th>
                        <th className="text-right py-3 px-4">$/kg</th>
                      </tr>
                    </thead>
                    <tbody>
                      {ventasMaterial.materiales.map((m, i) => (
                        <tr key={i} className="border-b hover:bg-gray-50">
                          <td className="py-3 px-4 font-medium">{m.material}</td>
                          <td className="text-right py-3 px-4">{m.cantidad_pesajes}</td>
                          <td className="text-right py-3 px-4">{formatNumber(m.total_kg, 0)}</td>
                          <td className="text-right py-3 px-4">{formatNumber(m.total_toneladas, 2)}</td>
                          <td className="text-right py-3 px-4">${formatNumber(m.importe_total, 0)}</td>
                          <td className="text-right py-3 px-4">${formatNumber(m.precio_promedio, 2)}</td>
                        </tr>
                      ))}
                    </tbody>
                    <tfoot>
                      <tr className="bg-gray-100 font-bold">
                        <td className="py-3 px-4">TOTAL</td>
                        <td className="text-right py-3 px-4">{ventasMaterial.cantidad_pesajes}</td>
                        <td className="text-right py-3 px-4">{formatNumber(ventasMaterial.total_kg, 0)}</td>
                        <td className="text-right py-3 px-4">{formatNumber(ventasMaterial.total_toneladas, 2)}</td>
                        <td className="text-right py-3 px-4">${formatNumber(ventasMaterial.total_importe, 0)}</td>
                        <td className="text-right py-3 px-4">-</td>
                      </tr>
                    </tfoot>
                  </table>
                </div>
              </CardContent>
            </Card>
          )}

          {/* VENTAS SEMANALES */}
          {tipoReporteActivo === 'ventas-semanal' && ventasSemanal && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Calendar className="h-5 w-5" />
                  Ventas por Semana
                  {materialFiltro && <span className="text-sm font-normal text-gray-500">- {materialFiltro}</span>}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b bg-gray-50">
                        <th className="text-left py-3 px-4">Semana</th>
                        <th className="text-left py-3 px-4">Período</th>
                        <th className="text-right py-3 px-4">Pesajes</th>
                        <th className="text-right py-3 px-4">Kg</th>
                        <th className="text-right py-3 px-4">Toneladas</th>
                        <th className="text-right py-3 px-4">Importe</th>
                      </tr>
                    </thead>
                    <tbody>
                      {ventasSemanal.semanas.map((s, i) => (
                        <tr key={i} className="border-b hover:bg-gray-50">
                          <td className="py-3 px-4 font-medium">S{s.semana}/{s.anio}</td>
                          <td className="py-3 px-4 text-gray-500">
                            {new Date(s.fecha_inicio).toLocaleDateString('es-AR', { day: '2-digit', month: 'short' })} -
                            {new Date(s.fecha_fin).toLocaleDateString('es-AR', { day: '2-digit', month: 'short' })}
                          </td>
                          <td className="text-right py-3 px-4">{s.cantidad_pesajes}</td>
                          <td className="text-right py-3 px-4">{formatNumber(s.total_kg, 0)}</td>
                          <td className="text-right py-3 px-4">{formatNumber(s.total_toneladas, 2)}</td>
                          <td className="text-right py-3 px-4">${formatNumber(s.importe_total, 0)}</td>
                        </tr>
                      ))}
                    </tbody>
                    <tfoot>
                      <tr className="bg-gray-100 font-bold">
                        <td className="py-3 px-4">TOTAL</td>
                        <td className="py-3 px-4"></td>
                        <td className="text-right py-3 px-4">{ventasSemanal.semanas.reduce((a, s) => a + s.cantidad_pesajes, 0)}</td>
                        <td className="text-right py-3 px-4">{formatNumber(ventasSemanal.total_kg, 0)}</td>
                        <td className="text-right py-3 px-4">{formatNumber(ventasSemanal.total_toneladas, 2)}</td>
                        <td className="text-right py-3 px-4">${formatNumber(ventasSemanal.total_importe, 0)}</td>
                      </tr>
                    </tfoot>
                  </table>
                </div>
              </CardContent>
            </Card>
          )}

          {/* GASTOS */}
          {tipoReporteActivo === 'gastos' && gastos && (
            <div className="space-y-6">
              {/* Cards resumen */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <Card className="bg-red-50 border-red-200">
                  <CardContent className="pt-4">
                    <p className="text-sm text-red-600">Total Gastos</p>
                    <p className="text-2xl font-bold text-red-700">${formatNumber(gastos.total_gastos, 0)}</p>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="pt-4">
                    <p className="text-sm text-gray-500">Combustible</p>
                    <p className="text-xl font-bold">${formatNumber(gastos.total_combustible, 0)}</p>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="pt-4">
                    <p className="text-sm text-gray-500">Servicios</p>
                    <p className="text-xl font-bold">${formatNumber(gastos.total_servicios, 0)}</p>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="pt-4">
                    <p className="text-sm text-gray-500">Repuestos</p>
                    <p className="text-xl font-bold">${formatNumber(gastos.total_repuestos, 0)}</p>
                  </CardContent>
                </Card>
              </div>

              {/* Tabla de categorías */}
              <Card>
                <CardHeader>
                  <CardTitle>Desglose por Categoría</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b bg-gray-50">
                          <th className="text-left py-3 px-4">Categoría</th>
                          <th className="text-right py-3 px-4">Cantidad</th>
                          <th className="text-right py-3 px-4">Total</th>
                          <th className="text-right py-3 px-4">% del Total</th>
                        </tr>
                      </thead>
                      <tbody>
                        {gastos.categorias.map((c, i) => (
                          <tr key={i} className="border-b hover:bg-gray-50">
                            <td className="py-3 px-4 font-medium">{c.categoria}</td>
                            <td className="text-right py-3 px-4">{c.cantidad}</td>
                            <td className="text-right py-3 px-4">${formatNumber(c.total, 0)}</td>
                            <td className="text-right py-3 px-4">
                              <div className="flex items-center justify-end gap-2">
                                <div className="w-20 bg-gray-200 rounded-full h-2">
                                  <div
                                    className="bg-red-500 h-2 rounded-full"
                                    style={{ width: `${c.porcentaje}%` }}
                                  />
                                </div>
                                <span>{formatNumber(c.porcentaje, 1)}%</span>
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* MAQUINARIA */}
          {tipoReporteActivo === 'maquinaria' && maquinaria && (
            <div className="space-y-6">
              {/* Resumen */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Card className="bg-blue-50 border-blue-200">
                  <CardContent className="pt-4">
                    <p className="text-sm text-blue-600">Máquinas Activas</p>
                    <p className="text-3xl font-bold text-blue-700">{maquinaria.total_maquinas_activas}</p>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="pt-4">
                    <p className="text-sm text-gray-500">Combustible Total</p>
                    <p className="text-xl font-bold">{formatNumber(maquinaria.total_combustible, 0)} L</p>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="pt-4">
                    <p className="text-sm text-gray-500">Costo Servicios</p>
                    <p className="text-xl font-bold">${formatNumber(maquinaria.total_costo_servicios, 0)}</p>
                  </CardContent>
                </Card>
              </div>

              {/* Tabla de máquinas */}
              <Card>
                <CardHeader>
                  <CardTitle>Actividad por Máquina</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b bg-gray-50">
                          <th className="text-left py-3 px-4">Identificador</th>
                          <th className="text-right py-3 px-4">Pesajes</th>
                          <th className="text-right py-3 px-4">Kg Transp.</th>
                          <th className="text-right py-3 px-4">Días Activa</th>
                          <th className="text-right py-3 px-4">Combustible</th>
                          <th className="text-right py-3 px-4">Servicios</th>
                          <th className="text-right py-3 px-4">Costo Serv.</th>
                        </tr>
                      </thead>
                      <tbody>
                        {maquinaria.maquinas.map((m, i) => (
                          <tr key={i} className="border-b hover:bg-gray-50">
                            <td className="py-3 px-4 font-medium">{m.identificador}</td>
                            <td className="text-right py-3 px-4">{m.cantidad_pesajes}</td>
                            <td className="text-right py-3 px-4">{formatNumber(m.total_kg, 0)}</td>
                            <td className="text-right py-3 px-4">{m.dias_activa}</td>
                            <td className="text-right py-3 px-4">{formatNumber(m.total_combustible, 0)} L</td>
                            <td className="text-right py-3 px-4">{m.cantidad_servicios}</td>
                            <td className="text-right py-3 px-4">${formatNumber(m.costo_servicios, 0)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* TOP CLIENTES */}
          {tipoReporteActivo === 'top-clientes' && topClientes && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Users className="h-5 w-5" />
                  Ranking de Clientes
                  <span className="text-sm font-normal text-gray-500">
                    ({topClientes.total_clientes} clientes en el período)
                  </span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b bg-gray-50">
                        <th className="text-center py-3 px-4 w-12">#</th>
                        <th className="text-left py-3 px-4">Cliente</th>
                        <th className="text-right py-3 px-4">Pesajes</th>
                        <th className="text-right py-3 px-4">Kg</th>
                        <th className="text-right py-3 px-4">Toneladas</th>
                        <th className="text-right py-3 px-4">Importe</th>
                        <th className="text-right py-3 px-4">% Total</th>
                      </tr>
                    </thead>
                    <tbody>
                      {topClientes.clientes.map((c, i) => (
                        <tr
                          key={i}
                          className={`border-b hover:bg-gray-50 ${i < 3 ? 'font-semibold' : ''}`}
                        >
                          <td className="text-center py-3 px-4">
                            {i === 0 && <span className="text-yellow-500 text-lg">🥇</span>}
                            {i === 1 && <span className="text-gray-400 text-lg">🥈</span>}
                            {i === 2 && <span className="text-amber-600 text-lg">🥉</span>}
                            {i > 2 && i + 1}
                          </td>
                          <td className="py-3 px-4">{c.nombre}</td>
                          <td className="text-right py-3 px-4">{c.cantidad_pesajes}</td>
                          <td className="text-right py-3 px-4">{formatNumber(c.total_kg, 0)}</td>
                          <td className="text-right py-3 px-4">{formatNumber(c.total_toneladas, 2)}</td>
                          <td className="text-right py-3 px-4">${formatNumber(c.importe_total, 0)}</td>
                          <td className="text-right py-3 px-4">
                            <div className="flex items-center justify-end gap-2">
                              <div className="w-16 bg-gray-200 rounded-full h-2">
                                <div
                                  className="bg-green-500 h-2 rounded-full"
                                  style={{ width: `${Math.min(c.porcentaje_total, 100)}%` }}
                                />
                              </div>
                              <span>{formatNumber(c.porcentaje_total, 1)}%</span>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                <div className="mt-4 pt-4 border-t text-right">
                  <span className="text-gray-500">Total General:</span>
                  <span className="ml-2 font-bold text-lg">${formatNumber(topClientes.total_general, 0)}</span>
                </div>
              </CardContent>
            </Card>
          )}
        </>
      )}
    </div>
  )
}
