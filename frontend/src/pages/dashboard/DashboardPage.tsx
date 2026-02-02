import { useQuery } from '@tanstack/react-query'
import {
  Scale,
  Fuel,
  Truck,
  AlertTriangle,
  TrendingUp,
  Calendar
} from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { dashboardService } from '@/services/dashboardService'
import { formatNumber, formatDate } from '@/lib/utils'

export default function DashboardPage() {
  const { data: resumen, isLoading } = useQuery({
    queryKey: ['dashboard-resumen'],
    queryFn: () => dashboardService.getResumenDia(),
    refetchInterval: 60000, // Refrescar cada minuto
  })

  const { data: estadisticasMes } = useQuery({
    queryKey: ['dashboard-estadisticas-mes'],
    queryFn: () => dashboardService.getEstadisticasMes(),
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-gray-500">Cargando dashboard...</div>
      </div>
    )
  }

  if (!resumen) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-gray-500">No se pudo cargar el dashboard</div>
      </div>
    )
  }

  const porcentajeCombustible = resumen.combustible.porcentaje
  const colorCombustible = porcentajeCombustible > 30 ? 'text-green-600' : 'text-red-600'

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-500 mt-1">Resumen de operaciones del día</p>
      </div>

      {/* Alertas */}
      {(resumen.alertas.repuestos_bajo_stock > 0 ||
        resumen.alertas.servicios_proximos > 0 ||
        resumen.alertas.nivel_combustible_bajo) && (
        <Card className="border-orange-200 bg-orange-50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-orange-800">
              <AlertTriangle className="h-5 w-5" />
              Alertas
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            {resumen.alertas.repuestos_bajo_stock > 0 && (
              <p className="text-orange-700">
                • {resumen.alertas.repuestos_bajo_stock} repuesto(s) con stock bajo
              </p>
            )}
            {resumen.alertas.servicios_proximos > 0 && (
              <p className="text-orange-700">
                • {resumen.alertas.servicios_proximos} servicio(s) programado(s) próximamente
              </p>
            )}
            {resumen.alertas.nivel_combustible_bajo && (
              <p className="text-orange-700">
                • Nivel de combustible en cisterna bajo
              </p>
            )}
          </CardContent>
        </Card>
      )}

      {/* Métricas principales */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Pesajes del día */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pesajes Hoy</CardTitle>
            <Scale className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{resumen.pesajes.cantidad}</div>
            <p className="text-xs text-muted-foreground">
              {formatNumber(resumen.pesajes.toneladas)} toneladas
            </p>
          </CardContent>
        </Card>

        {/* Combustible */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Combustible</CardTitle>
            <Fuel className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${colorCombustible}`}>
              {formatNumber(porcentajeCombustible, 1)}%
            </div>
            <p className="text-xs text-muted-foreground">
              {formatNumber(resumen.combustible.nivel_actual, 0)} / {formatNumber(resumen.combustible.capacidad_total, 0)} L
            </p>
          </CardContent>
        </Card>

        {/* Camiones operativos */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Camiones Operativos</CardTitle>
            <Truck className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {resumen.camiones.operativos}
            </div>
            <p className="text-xs text-muted-foreground">
              de {resumen.camiones.total} camiones
            </p>
          </CardContent>
        </Card>

        {/* Servicios en proceso */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">En Servicio</CardTitle>
            <Calendar className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-orange-600">
              {resumen.camiones.en_servicio}
            </div>
            <p className="text-xs text-muted-foreground">
              {resumen.alertas.servicios_proximos} próximos
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Estadísticas del mes (si están disponibles) */}
      {estadisticasMes && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5" />
              Resumen del Mes
            </CardTitle>
            <CardDescription>Estadísticas acumuladas</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <p className="text-sm text-muted-foreground">Total Pesajes</p>
                <p className="text-2xl font-bold">{estadisticasMes.total_pesajes_mes}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Total Toneladas</p>
                <p className="text-2xl font-bold">{formatNumber(estadisticasMes.total_toneladas_mes)}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Combustible (L)</p>
                <p className="text-2xl font-bold">{formatNumber(estadisticasMes.total_combustible_mes, 0)}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Servicios</p>
                <p className="text-2xl font-bold">{estadisticasMes.total_servicios_mes}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Últimos pesajes y servicios próximos */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Servicios próximos */}
        <Card>
          <CardHeader>
            <CardTitle>Servicios Programados</CardTitle>
            <CardDescription>Próximos 7 días</CardDescription>
          </CardHeader>
          <CardContent>
            {resumen.servicios_proximos.length === 0 ? (
              <p className="text-sm text-muted-foreground">No hay servicios programados</p>
            ) : (
              <div className="space-y-3">
                {resumen.servicios_proximos.map((servicio) => (
                  <div key={servicio.id} className="flex items-start justify-between border-b pb-3 last:border-0">
                    <div className="flex-1">
                      <p className="font-medium text-sm">{servicio.camion_patente}</p>
                      <p className="text-xs text-muted-foreground">{servicio.descripcion}</p>
                      <span className="inline-block mt-1 px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded">
                        {servicio.tipo}
                      </span>
                    </div>
                    <div className="text-right text-sm text-muted-foreground">
                      {formatDate(servicio.fecha)}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Últimos pesajes */}
        <Card>
          <CardHeader>
            <CardTitle>Últimos Pesajes</CardTitle>
            <CardDescription>Registros recientes</CardDescription>
          </CardHeader>
          <CardContent>
            {resumen.ultimos_pesajes.length === 0 ? (
              <p className="text-sm text-muted-foreground">No hay pesajes registrados</p>
            ) : (
              <div className="space-y-3">
                {resumen.ultimos_pesajes.slice(0, 5).map((pesaje) => (
                  <div key={pesaje.id} className="flex items-start justify-between border-b pb-3 last:border-0">
                    <div className="flex-1">
                      <p className="font-medium text-sm">#{pesaje.numero_pesaje} - {pesaje.camion_patente}</p>
                      <p className="text-xs text-muted-foreground">{pesaje.material} → {pesaje.cliente_destino}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-semibold">{formatNumber(pesaje.peso_neto / 1000)} t</p>
                      <p className="text-xs text-muted-foreground">{formatDate(pesaje.fecha)}</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
