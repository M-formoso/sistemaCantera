import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { ColumnDef } from '@tanstack/react-table'
import { Fuel, TrendingUp, TrendingDown, Truck, AlertTriangle, Pencil, Trash2, Plus, ArrowRightLeft, History } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { DataTable } from '@/components/ui/data-table'
import { combustibleService } from '@/services/combustibleService'
import { CargaCisterna, SuministroCombustible } from '@/types'
import { formatNumber, formatDate, formatCurrency } from '@/lib/utils'
import { useIsAdmin } from '@/hooks/useIsAdmin'

export default function CombustiblePage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const isAdmin = useIsAdmin()
  const [selectedTab, setSelectedTab] = useState<'cisternas' | 'cargas' | 'suministros' | 'movimientos'>('cisternas')
  const [selectedCisternaId, setSelectedCisternaId] = useState<string | null>(null)

  // Mutation para eliminar suministro
  const deleteSuministroMutation = useMutation({
    mutationFn: (id: string) => combustibleService.deleteSuministro(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['suministros'] })
      queryClient.invalidateQueries({ queryKey: ['cisternas'] })
    },
    onError: () => {
      alert('Error al eliminar el suministro')
    },
  })

  const handleDeleteSuministro = (suministro: SuministroCombustible) => {
    const identificador = suministro.camion_patente || suministro.camion_nombre || 'el camión'
    const confirmed = window.confirm(
      `¿Eliminar el suministro de ${suministro.litros} litros a ${identificador}?\n\nLos litros serán devueltos a la cisterna.`
    )
    if (confirmed) {
      deleteSuministroMutation.mutate(suministro.id)
    }
  }

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

  // Query para movimientos de cisterna seleccionada
  const { data: movimientos = [], isLoading: isLoadingMovimientos } = useQuery({
    queryKey: ['movimientos-cisterna', selectedCisternaId],
    queryFn: () => combustibleService.getMovimientosCisterna(selectedCisternaId!, 0, 200),
    enabled: !!selectedCisternaId && selectedTab === 'movimientos',
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

  // Columnas para tabla de cargas
  const cargasColumns: ColumnDef<CargaCisterna>[] = [
    {
      accessorKey: 'fecha',
      header: 'Fecha',
      cell: ({ row }) => <div className="text-sm">{formatDate(row.getValue('fecha'))}</div>,
    },
    {
      accessorKey: 'cisterna_nombre',
      header: 'Cisterna',
      cell: ({ row }) => (
        <div className="flex items-center gap-2">
          <TrendingUp className="h-4 w-4 text-green-600" />
          <span className="font-medium">{row.getValue('cisterna_nombre') || 'Cisterna'}</span>
        </div>
      ),
    },
    {
      accessorKey: 'proveedor',
      header: 'Proveedor',
      cell: ({ row }) => <div className="text-sm">{row.getValue('proveedor')}</div>,
    },
    {
      accessorKey: 'numero_remito',
      header: 'Remito',
      cell: ({ row }) => (
        <div className="text-sm text-muted-foreground">{row.getValue('numero_remito') || '-'}</div>
      ),
    },
    {
      accessorKey: 'litros',
      header: 'Litros',
      cell: ({ row }) => (
        <div className="text-lg font-bold text-green-600 text-right">
          +{formatNumber(row.getValue('litros'), 0)} L
        </div>
      ),
    },
    {
      id: 'costo',
      header: 'Costo',
      cell: ({ row }) => {
        const carga = row.original
        return carga.precio_por_litro ? (
          <div className="text-sm text-right text-muted-foreground">
            {formatCurrency(carga.litros * carga.precio_por_litro)}
          </div>
        ) : (
          <div className="text-sm text-right text-muted-foreground">-</div>
        )
      },
    },
  ]

  // Columnas para tabla de suministros
  const suministrosColumns: ColumnDef<SuministroCombustible>[] = [
    {
      accessorKey: 'fecha',
      header: 'Fecha',
      cell: ({ row }) => <div className="text-sm">{formatDate(row.getValue('fecha'))}</div>,
    },
    {
      id: 'camion',
      header: 'Camión/Máquina',
      cell: ({ row }) => {
        const suministro = row.original
        // Mostrar patente, o nombre, o código interno (lo que esté disponible)
        const identificador = suministro.camion_patente || suministro.camion_nombre || suministro.camion_codigo_interno || '-'
        return (
          <div className="flex items-center gap-2">
            <Truck className="h-4 w-4 text-blue-600" />
            <span className="font-medium">{identificador}</span>
          </div>
        )
      },
    },
    {
      accessorKey: 'usuario_nombre',
      header: 'Realizado por',
      cell: ({ row }) => (
        <div className="text-sm">{row.getValue('usuario_nombre') || '-'}</div>
      ),
    },
    {
      accessorKey: 'litros',
      header: 'Litros',
      cell: ({ row }) => (
        <div className="text-lg font-bold text-orange-600 text-right">
          -{formatNumber(row.getValue('litros'), 0)} L
        </div>
      ),
    },
    {
      id: 'acciones',
      header: 'Acciones',
      cell: ({ row }) => {
        const suministro = row.original
        return (
          <div className="flex items-center gap-1">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => navigate(`/combustible/suministro/${suministro.id}/editar`)}
              title="Editar suministro"
            >
              <Pencil className="h-4 w-4 text-blue-600" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => handleDeleteSuministro(suministro)}
              title="Eliminar suministro"
            >
              <Trash2 className="h-4 w-4 text-red-600" />
            </Button>
          </div>
        )
      },
    },
  ]

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 flex items-center gap-2">
            <Fuel className="h-6 w-6 sm:h-8 sm:w-8" />
            Combustible
          </h1>
          <p className="text-gray-500 mt-1 text-sm sm:text-base">Gestión de cisternas y suministros</p>
        </div>
        <div className="flex gap-2 w-full sm:w-auto">
          <Button onClick={() => navigate('/combustible/carga-nueva')} className="flex-1 sm:flex-none" size="sm">
            <TrendingUp className="h-4 w-4 sm:mr-2" />
            <span className="hidden sm:inline">Nueva</span> Carga
          </Button>
          <Button onClick={() => navigate('/combustible/suministro-nuevo')} className="flex-1 sm:flex-none" size="sm">
            <TrendingDown className="h-4 w-4 sm:mr-2" />
            <span className="hidden sm:inline">Nuevo</span> Suministro
          </Button>
        </div>
      </div>

      {/* Estadísticas globales */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 sm:gap-4">
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
      <div className="border-b overflow-x-auto">
        <div className="flex gap-2 sm:gap-4 min-w-max">
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
          <button
            onClick={() => setSelectedTab('movimientos')}
            className={`pb-3 px-1 border-b-2 transition-colors flex items-center gap-1 ${
              selectedTab === 'movimientos'
                ? 'border-blue-600 text-blue-600 font-medium'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            <History className="h-4 w-4" />
            Movimientos
          </button>
        </div>
      </div>

      {/* Contenido de tabs */}
      {selectedTab === 'cisternas' && (
        <div className="space-y-4">
          {/* Botón Nueva Cisterna - Solo Admin */}
          {isAdmin && (
            <div className="flex justify-end">
              <Button onClick={() => navigate('/combustible/cisterna-nueva')}>
                <Plus className="h-4 w-4 mr-2" />
                Nueva Cisterna
              </Button>
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-6">
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
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => navigate(`/combustible/transferencia?origen=${cisterna.id}`)}
                      className="flex-1"
                      title="Transferir a otra cisterna"
                    >
                      <ArrowRightLeft className="h-4 w-4 mr-1" />
                      Transferir
                    </Button>
                  </div>
                </CardContent>
              </Card>
            )
          })}
          </div>
        </div>
      )}

      {selectedTab === 'cargas' && (
        <Card>
          <CardHeader>
            <CardTitle>Historial de Cargas</CardTitle>
            <CardDescription>Registros de carga de combustible a cisternas</CardDescription>
          </CardHeader>
          <CardContent>
            <DataTable
              columns={cargasColumns}
              data={cargas}
              searchPlaceholder="Buscar por proveedor, cisterna..."
              defaultPageSize={10}
            />
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
            <DataTable
              columns={suministrosColumns}
              data={suministros}
              searchPlaceholder="Buscar por patente, cisterna..."
              defaultPageSize={10}
            />
          </CardContent>
        </Card>
      )}

      {selectedTab === 'movimientos' && (
        <div className="space-y-4">
          {/* Selector de cisterna */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <History className="h-5 w-5" />
                Historial de Movimientos
              </CardTitle>
              <CardDescription>
                Seleccione una cisterna para ver todos sus movimientos
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2">
                {cisternas.map((cisterna) => (
                  <button
                    key={cisterna.id}
                    onClick={() => setSelectedCisternaId(cisterna.id)}
                    className={`p-3 rounded-lg text-left transition-all ${
                      selectedCisternaId === cisterna.id
                        ? 'bg-blue-100 border-2 border-blue-500 shadow-md'
                        : 'bg-gray-50 hover:bg-gray-100 border-2 border-transparent hover:border-gray-300'
                    }`}
                  >
                    <p className="font-medium text-sm">{cisterna.nombre}</p>
                    <p className="text-xs text-gray-500 mt-1">
                      {formatNumber(cisterna.nivel_actual, 0)} L
                    </p>
                  </button>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Lista de movimientos */}
          {selectedCisternaId && (
            <Card>
              <CardHeader>
                <CardTitle>
                  Movimientos de {cisternas.find(c => c.id === selectedCisternaId)?.nombre}
                </CardTitle>
              </CardHeader>
              <CardContent>
                {isLoadingMovimientos ? (
                  <div className="py-8 text-center text-gray-500">
                    Cargando movimientos...
                  </div>
                ) : movimientos.length === 0 ? (
                  <div className="py-8 text-center text-gray-500">
                    No hay movimientos registrados
                  </div>
                ) : (
                  <div className="space-y-2">
                    {movimientos.map((mov) => {
                      const fecha = new Date(mov.fecha)
                      const fechaStr = fecha.toLocaleDateString('es-AR', {
                        day: '2-digit',
                        month: '2-digit',
                        year: 'numeric'
                      })
                      const horaStr = fecha.toLocaleTimeString('es-AR', {
                        hour: '2-digit',
                        minute: '2-digit'
                      })

                      const tipoConfig: Record<string, { color: string; icon: string; label: string }> = {
                        CARGA: { color: 'bg-green-100 text-green-700', icon: '↑', label: 'Carga' },
                        SUMINISTRO: { color: 'bg-orange-100 text-orange-700', icon: '↓', label: 'Suministro' },
                        TRANSFERENCIA_SALIDA: { color: 'bg-red-100 text-red-700', icon: '→', label: 'Transf. Salida' },
                        TRANSFERENCIA_ENTRADA: { color: 'bg-blue-100 text-blue-700', icon: '←', label: 'Transf. Entrada' },
                      }

                      const config = tipoConfig[mov.tipo] || { color: 'bg-gray-100', icon: '•', label: mov.tipo }

                      return (
                        <div
                          key={mov.id}
                          className="flex items-center justify-between py-3 px-4 bg-gray-50 rounded-lg hover:bg-gray-100"
                        >
                          <div className="flex items-center gap-4">
                            <div className="text-center min-w-[80px]">
                              <p className="text-sm font-medium">{fechaStr}</p>
                              <p className="text-xs text-gray-500">{horaStr}</p>
                            </div>
                            <span className={`text-xs font-semibold px-2 py-1 rounded ${config.color}`}>
                              {config.icon} {config.label}
                            </span>
                            <div>
                              <p className="text-sm font-medium">{mov.descripcion}</p>
                              <p className="text-xs text-gray-500">{mov.usuario_nombre}</p>
                            </div>
                          </div>
                          <div className={`text-lg font-bold ${mov.signo === '+' ? 'text-green-600' : 'text-orange-600'}`}>
                            {mov.signo}{formatNumber(mov.litros, 0)} L
                          </div>
                        </div>
                      )
                    })}
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </div>
      )}

    </div>
  )
}
