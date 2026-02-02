import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { Fuel, Plus, TrendingUp, TrendingDown, Truck, AlertTriangle } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { combustibleService } from '@/services/combustibleService'
import { formatNumber, formatDate, formatCurrency } from '@/lib/utils'

export default function CombustiblePage() {
  const navigate = useNavigate()
  const [selectedTab, setSelectedTab] = useState<'cisternas' | 'cargas' | 'suministros'>('cisternas')

  const { data: cisternas = [], isLoading: isLoadingCisternas } = useQuery({
    queryKey: ['cisternas'],
    queryFn: () => combustibleService.getCisternas(),
  })

  const { data: cargas = [], isLoading: isLoadingCargas } = useQuery({
    queryKey: ['cargas'],
    queryFn: () => combustibleService.getCargas(),
  })

  const { data: suministros = [], isLoading: isLoadingSuministros } = useQuery({
    queryKey: ['suministros'],
    queryFn: () => combustibleService.getSuministros(0, 100),
  })

  const isLoading = isLoadingCisternas || isLoadingCargas || isLoadingSuministros

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-gray-500">Cargando combustible...</div>
      </div>
    )
  }

  const totalCargado = cargas.reduce((sum, c) => sum + c.litros, 0)
  const totalSuministrado = suministros.reduce((sum, s) => sum + s.litros, 0)
  const nivelActualTotal = cisternas.reduce((sum, c) => sum + c.nivel_actual, 0)

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
            <Fuel className="h-8 w-8" />
            Combustible
          </h1>
          <p className="text-gray-500 mt-1">Gestión de cisternas y suministros</p>
        </div>
        <div className="flex gap-2">
          <Button onClick={() => navigate('/combustible/carga-nueva')}>
            <TrendingUp className="h-4 w-4 mr-2" />
            Nueva Carga
          </Button>
          <Button onClick={() => navigate('/combustible/suministro-nuevo')}>
            <TrendingDown className="h-4 w-4 mr-2" />
            Nuevo Suministro
          </Button>
        </div>
      </div>

      {/* Estadísticas globales */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Nivel Actual</div>
            <div className="text-2xl font-bold text-blue-600">
              {formatNumber(nivelActualTotal, 0)} L
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Total Cargado</div>
            <div className="text-2xl font-bold text-green-600">
              {formatNumber(totalCargado, 0)} L
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Total Suministrado</div>
            <div className="text-2xl font-bold text-orange-600">
              {formatNumber(totalSuministrado, 0)} L
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Cisternas</div>
            <div className="text-2xl font-bold">{cisternas.length}</div>
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <div className="border-b">
        <div className="flex gap-4">
          <button
            onClick={() => setSelectedTab('cisternas')}
            className={`pb-3 px-1 border-b-2 transition-colors ${
              selectedTab === 'cisternas'
                ? 'border-blue-600 text-blue-600 font-medium'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            Cisternas
          </button>
          <button
            onClick={() => setSelectedTab('cargas')}
            className={`pb-3 px-1 border-b-2 transition-colors ${
              selectedTab === 'cargas'
                ? 'border-blue-600 text-blue-600 font-medium'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            Cargas ({cargas.length})
          </button>
          <button
            onClick={() => setSelectedTab('suministros')}
            className={`pb-3 px-1 border-b-2 transition-colors ${
              selectedTab === 'suministros'
                ? 'border-blue-600 text-blue-600 font-medium'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            Suministros ({suministros.length})
          </button>
        </div>
      </div>

      {/* Contenido de tabs */}
      {selectedTab === 'cisternas' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {cisternas.map((cisterna) => {
            const porcentaje = (cisterna.nivel_actual / cisterna.capacidad_total) * 100
            const isLow = porcentaje <= 30
            const colorClass = isLow ? 'bg-red-500' : 'bg-green-500'

            return (
              <Card key={cisterna.id}>
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div>
                      <CardTitle>{cisterna.nombre}</CardTitle>
                      <CardDescription>
                        Capacidad: {formatNumber(cisterna.capacidad_total, 0)} L
                      </CardDescription>
                    </div>
                    {isLow && (
                      <AlertTriangle className="h-5 w-5 text-red-600" />
                    )}
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  {/* Medidor visual */}
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Nivel Actual</span>
                      <span className={`font-semibold ${isLow ? 'text-red-600' : 'text-green-600'}`}>
                        {formatNumber(porcentaje, 1)}%
                      </span>
                    </div>
                    <div className="h-8 bg-gray-200 rounded-full overflow-hidden">
                      <div
                        className={`h-full ${colorClass} transition-all duration-500`}
                        style={{ width: `${Math.min(porcentaje, 100)}%` }}
                      />
                    </div>
                    <div className="flex justify-between text-sm text-muted-foreground">
                      <span>{formatNumber(cisterna.nivel_actual, 0)} L</span>
                      <span>{formatNumber(cisterna.capacidad_total, 0)} L</span>
                    </div>
                  </div>

                  {/* Info adicional */}
                  <div className="pt-3 border-t space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Nivel Mínimo:</span>
                      <span className="font-medium">{formatNumber(cisterna.nivel_minimo, 0)} L</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Última Actualización:</span>
                      <span className="font-medium">{formatDate(cisterna.updated_at)}</span>
                    </div>
                  </div>

                  {/* Botones */}
                  <div className="pt-3 border-t flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => navigate(`/combustible/carga-nueva?cisterna=${cisterna.id}`)}
                      className="flex-1"
                    >
                      <TrendingUp className="h-4 w-4 mr-1" />
                      Cargar
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => navigate(`/combustible/suministro-nuevo?cisterna=${cisterna.id}`)}
                      className="flex-1"
                    >
                      <TrendingDown className="h-4 w-4 mr-1" />
                      Suministrar
                    </Button>
                  </div>
                </CardContent>
              </Card>
            )
          })}
        </div>
      )}

      {selectedTab === 'cargas' && (
        <Card>
          <CardHeader>
            <CardTitle>Historial de Cargas</CardTitle>
            <CardDescription>Registros de carga de combustible a cisternas</CardDescription>
          </CardHeader>
          <CardContent>
            {cargas.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                No hay cargas registradas
              </div>
            ) : (
              <div className="space-y-3">
                {cargas.map((carga) => (
                  <div
                    key={carga.id}
                    className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50 transition-colors"
                  >
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <TrendingUp className="h-4 w-4 text-green-600" />
                        <span className="font-medium">{carga.cisterna_nombre || 'Cisterna'}</span>
                      </div>
                      <p className="text-sm text-muted-foreground">
                        {carga.proveedor}
                        {carga.numero_remito && ` • Remito: ${carga.numero_remito}`}
                      </p>
                      <p className="text-xs text-muted-foreground mt-1">{formatDate(carga.fecha)}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-lg font-bold text-green-600">
                        +{formatNumber(carga.litros, 0)} L
                      </p>
                      {carga.precio_por_litro && (
                        <p className="text-sm text-muted-foreground">
                          {formatCurrency(carga.litros * carga.precio_por_litro)}
                        </p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {selectedTab === 'suministros' && (
        <Card>
          <CardHeader>
            <CardTitle>Historial de Suministros</CardTitle>
            <CardDescription>Registros de suministro de combustible a camiones</CardDescription>
          </CardHeader>
          <CardContent>
            {suministros.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                No hay suministros registrados
              </div>
            ) : (
              <div className="space-y-3">
                {suministros.map((suministro) => (
                  <div
                    key={suministro.id}
                    className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50 transition-colors"
                  >
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <Truck className="h-4 w-4 text-blue-600" />
                        <span className="font-medium">{suministro.camion_patente}</span>
                        <TrendingDown className="h-4 w-4 text-orange-600" />
                      </div>
                      <p className="text-sm text-muted-foreground">
                        {suministro.cisterna_nombre || 'Cisterna'}
                      </p>
                      <div className="flex items-center gap-3 mt-1">
                        <p className="text-xs text-muted-foreground">{formatDate(suministro.fecha)}</p>
                        {suministro.kilometraje_actual && (
                          <p className="text-xs text-muted-foreground">
                            {formatNumber(suministro.kilometraje_actual)} km
                          </p>
                        )}
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-lg font-bold text-orange-600">
                        -{formatNumber(suministro.litros, 0)} L
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  )
}
