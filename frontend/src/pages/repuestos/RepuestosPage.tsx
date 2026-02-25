import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { ColumnDef } from '@tanstack/react-table'
import { Package, Plus, Pencil, Trash2, AlertTriangle, TrendingUp, TrendingDown, X, History } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { DataTable } from '@/components/ui/data-table'
import { repuestosService } from '@/services/repuestosService'
import { Repuesto, MovimientoStock } from '@/types'
import { formatCurrency } from '@/lib/utils'
import { useIsAdmin } from '@/hooks/useIsAdmin'

interface MovimientoModal {
  repuesto: Repuesto | null
  tipo: 'ingreso' | 'egreso' | null
}

export default function RepuestosPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const isAdmin = useIsAdmin()
  const [showOnlyBajoStock, setShowOnlyBajoStock] = useState(false)
  const [movimientoModal, setMovimientoModal] = useState<MovimientoModal>({ repuesto: null, tipo: null })
  const [cantidad, setCantidad] = useState('')
  const [observaciones, setObservaciones] = useState('')
  const [historialRepuesto, setHistorialRepuesto] = useState<Repuesto | null>(null)
  const [movimientos, setMovimientos] = useState<MovimientoStock[]>([])
  const [loadingHistorial, setLoadingHistorial] = useState(false)

  const { data: repuestos = [], isLoading } = useQuery({
    queryKey: ['repuestos', showOnlyBajoStock],
    queryFn: () => showOnlyBajoStock ? repuestosService.getStockBajo() : repuestosService.getAll(true),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => repuestosService.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['repuestos'] })
    },
  })

  const ajustarStockMutation = useMutation({
    mutationFn: ({ id, cantidad, tipo, observaciones }: { id: string; cantidad: number; tipo: 'ingreso' | 'egreso'; observaciones?: string }) =>
      tipo === 'ingreso'
        ? repuestosService.registrarEntrada(id, cantidad, observaciones)
        : repuestosService.registrarSalida(id, cantidad, observaciones),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['repuestos'] })
      cerrarModal()
    },
  })

  const handleDelete = async (id: string, nombre: string) => {
    if (window.confirm(`¿Está seguro de eliminar el repuesto ${nombre}?`)) {
      try {
        await deleteMutation.mutateAsync(id)
      } catch (error) {
        alert('Error al eliminar el repuesto')
      }
    }
  }

  const abrirModal = (repuesto: Repuesto, tipo: 'ingreso' | 'egreso') => {
    setMovimientoModal({ repuesto, tipo })
    setCantidad('')
    setObservaciones('')
  }

  const cerrarModal = () => {
    setMovimientoModal({ repuesto: null, tipo: null })
    setCantidad('')
    setObservaciones('')
  }

  const abrirHistorial = async (repuesto: Repuesto) => {
    setHistorialRepuesto(repuesto)
    setLoadingHistorial(true)
    try {
      const data = await repuestosService.getMovimientos(repuesto.id)
      setMovimientos(data)
    } catch (error) {
      console.error('Error al cargar historial:', error)
      setMovimientos([])
    } finally {
      setLoadingHistorial(false)
    }
  }

  const cerrarHistorial = () => {
    setHistorialRepuesto(null)
    setMovimientos([])
  }

  const handleAjustarStock = async () => {
    if (!movimientoModal.repuesto || !movimientoModal.tipo || !cantidad) return

    const cantidadNum = parseFloat(cantidad)
    if (isNaN(cantidadNum) || cantidadNum <= 0) {
      alert('La cantidad debe ser mayor a 0')
      return
    }

    if (movimientoModal.tipo === 'egreso' && cantidadNum > movimientoModal.repuesto.stock_actual) {
      alert('No hay suficiente stock disponible')
      return
    }

    try {
      await ajustarStockMutation.mutateAsync({
        id: movimientoModal.repuesto.id,
        cantidad: cantidadNum,
        tipo: movimientoModal.tipo,
        observaciones: observaciones || undefined,
      })
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Error al ajustar el stock')
    }
  }

  const columns: ColumnDef<Repuesto>[] = [
    {
      accessorKey: 'codigo',
      header: 'Código',
      cell: ({ row }) => (
        <div className="font-medium">{row.getValue('codigo')}</div>
      ),
    },
    {
      accessorKey: 'nombre',
      header: 'Nombre',
      cell: ({ row }) => (
        <div className="font-medium">{row.getValue('nombre')}</div>
      ),
    },
    {
      accessorKey: 'categoria',
      header: 'Categoría',
      cell: ({ row }) => {
        const categoria = row.getValue('categoria') as string
        return (
          <span className="inline-flex px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded">
            {categoria}
          </span>
        )
      },
    },
    {
      accessorKey: 'stock_actual',
      header: 'Stock',
      cell: ({ row }) => {
        const stockActual = row.getValue('stock_actual') as number
        const stockMinimo = row.original.stock_minimo
        const isLow = stockActual <= stockMinimo

        return (
          <div className="flex items-center gap-2">
            <span className={`font-semibold ${isLow ? 'text-red-600' : 'text-green-600'}`}>
              {stockActual}
            </span>
            {isLow && <AlertTriangle className="h-4 w-4 text-red-600" />}
          </div>
        )
      },
    },
    {
      accessorKey: 'stock_minimo',
      header: 'Stock Mín.',
      cell: ({ row }) => (
        <div className="text-sm text-muted-foreground">{row.getValue('stock_minimo')}</div>
      ),
    },
    {
      accessorKey: 'precio_unitario',
      header: 'Precio Unit.',
      cell: ({ row }) => {
        const precio = row.getValue('precio_unitario') as number
        return <div className="text-sm">{formatCurrency(precio)}</div>
      },
    },
    {
      accessorKey: 'ubicacion',
      header: 'Ubicación',
      cell: ({ row }) => {
        const ubicacion = row.getValue('ubicacion') as string | null
        return <div className="text-sm text-muted-foreground">{ubicacion || '-'}</div>
      },
    },
    {
      id: 'actions',
      header: 'Acciones',
      cell: ({ row }) => {
        const repuesto = row.original
        return (
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => abrirHistorial(repuesto)}
              title="Ver historial"
            >
              <History className="h-4 w-4 text-blue-600" />
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => abrirModal(repuesto, 'ingreso')}
              title="Registrar entrada"
            >
              <TrendingUp className="h-4 w-4 text-green-600" />
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => abrirModal(repuesto, 'egreso')}
              title="Registrar salida"
            >
              <TrendingDown className="h-4 w-4 text-orange-600" />
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => navigate(`/repuestos/${repuesto.id}/editar`)}
              title="Editar"
            >
              <Pencil className="h-4 w-4" />
            </Button>
            {isAdmin && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleDelete(repuesto.id, repuesto.nombre)}
                disabled={deleteMutation.isPending}
                title="Eliminar"
              >
                <Trash2 className="h-4 w-4 text-red-600" />
              </Button>
            )}
          </div>
        )
      },
    },
  ]

  const repuestosBajoStock = repuestos.filter(r => r.stock_actual <= r.stock_minimo).length

  // Columnas para el historial de movimientos
  const movimientosColumns: ColumnDef<MovimientoStock>[] = [
    {
      accessorKey: 'created_at',
      header: 'Fecha',
      cell: ({ row }) => (
        <div className="text-sm">
          {new Date(row.getValue('created_at')).toLocaleDateString('es-AR', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
          })}
        </div>
      ),
    },
    {
      accessorKey: 'tipo',
      header: 'Tipo',
      cell: ({ row }) => {
        const tipo = row.getValue('tipo') as string
        return (
          <div className="flex items-center gap-2">
            {tipo === 'ingreso' ? (
              <TrendingUp className="h-4 w-4 text-green-600" />
            ) : (
              <TrendingDown className="h-4 w-4 text-orange-600" />
            )}
            <span className={tipo === 'ingreso' ? 'text-green-700' : 'text-orange-700'}>
              {tipo === 'ingreso' ? 'Ingreso' : 'Egreso'}
            </span>
          </div>
        )
      },
    },
    {
      accessorKey: 'cantidad',
      header: 'Cantidad',
      cell: ({ row }) => {
        const mov = row.original
        return (
          <span className={`font-semibold ${mov.tipo === 'ingreso' ? 'text-green-700' : 'text-orange-700'}`}>
            {mov.tipo === 'ingreso' ? '+' : '-'}{mov.cantidad}
          </span>
        )
      },
    },
    {
      accessorKey: 'usuario_nombre',
      header: 'Usuario',
      cell: ({ row }) => <div className="text-sm font-medium">{row.getValue('usuario_nombre')}</div>,
    },
    {
      accessorKey: 'observaciones',
      header: 'Observaciones',
      cell: ({ row }) => (
        <div className="text-sm text-muted-foreground">{row.getValue('observaciones') || '-'}</div>
      ),
    },
  ]

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-gray-500">Cargando repuestos...</div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 flex items-center gap-2">
            <Package className="h-6 w-6 sm:h-8 sm:w-8" />
            Repuestos
          </h1>
          <p className="text-gray-500 mt-1 text-sm sm:text-base">Gestión de inventario de repuestos</p>
        </div>
        <Button onClick={() => navigate('/repuestos/nuevo')} className="w-full sm:w-auto">
          <Plus className="h-4 w-4 mr-2" />
          Nuevo Repuesto
        </Button>
      </div>

      {/* Alertas de stock bajo */}
      {repuestosBajoStock > 0 && !showOnlyBajoStock && (
        <Card className="border-orange-200 bg-orange-50">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <AlertTriangle className="h-5 w-5 text-orange-600" />
                <p className="text-orange-700 font-medium">
                  {repuestosBajoStock} repuesto(s) con stock bajo
                </p>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowOnlyBajoStock(true)}
              >
                Ver repuestos con stock bajo
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader className="px-3 sm:px-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <CardTitle className="text-lg sm:text-xl">
              {showOnlyBajoStock ? 'Repuestos con Stock Bajo' : 'Lista de Repuestos'}
            </CardTitle>
            {showOnlyBajoStock && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowOnlyBajoStock(false)}
              >
                Ver todos
              </Button>
            )}
          </div>
        </CardHeader>
        <CardContent className="px-3 sm:px-6">
          <DataTable
            columns={columns}
            data={repuestos}
            searchPlaceholder="Buscar por código, nombre, categoría..."
            defaultPageSize={10}
          />
        </CardContent>
      </Card>

      {/* Modal de ajuste de stock */}
      {movimientoModal.repuesto && movimientoModal.tipo && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-md">
            <div className="flex items-center justify-between p-4 border-b">
              <h3 className="text-lg font-semibold">
                {movimientoModal.tipo === 'ingreso' ? 'Registrar Entrada' : 'Registrar Salida'}
              </h3>
              <Button variant="ghost" size="sm" onClick={cerrarModal}>
                <X className="h-4 w-4" />
              </Button>
            </div>
            <div className="p-4 space-y-4">
              <div className="bg-gray-50 rounded-lg p-3">
                <p className="text-sm text-muted-foreground">Repuesto</p>
                <p className="font-semibold">{movimientoModal.repuesto.nombre}</p>
                <p className="text-sm text-muted-foreground">
                  Stock actual: <span className="font-medium">{movimientoModal.repuesto.stock_actual}</span>
                </p>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">
                  Cantidad a {movimientoModal.tipo === 'ingreso' ? 'ingresar' : 'egresar'}
                </label>
                <Input
                  type="number"
                  min="1"
                  max={movimientoModal.tipo === 'egreso' ? movimientoModal.repuesto.stock_actual : undefined}
                  value={cantidad}
                  onChange={(e) => setCantidad(e.target.value)}
                  placeholder="Ingrese la cantidad"
                  autoFocus
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">Observaciones (opcional)</label>
                <Input
                  type="text"
                  value={observaciones}
                  onChange={(e) => setObservaciones(e.target.value)}
                  placeholder="Motivo del ajuste..."
                />
              </div>

              {cantidad && (
                <div className="bg-blue-50 rounded-lg p-3">
                  <p className="text-sm text-blue-700">
                    Nuevo stock: <span className="font-bold">
                      {movimientoModal.tipo === 'ingreso'
                        ? movimientoModal.repuesto.stock_actual + parseFloat(cantidad || '0')
                        : movimientoModal.repuesto.stock_actual - parseFloat(cantidad || '0')
                      }
                    </span>
                  </p>
                </div>
              )}
            </div>
            <div className="flex justify-end gap-2 p-4 border-t">
              <Button variant="outline" onClick={cerrarModal}>
                Cancelar
              </Button>
              <Button
                onClick={handleAjustarStock}
                disabled={ajustarStockMutation.isPending || !cantidad}
                className={movimientoModal.tipo === 'ingreso' ? 'bg-green-600 hover:bg-green-700' : 'bg-orange-600 hover:bg-orange-700'}
              >
                {ajustarStockMutation.isPending ? 'Guardando...' : movimientoModal.tipo === 'ingreso' ? 'Registrar Entrada' : 'Registrar Salida'}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Modal de historial de movimientos */}
      {historialRepuesto && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[85vh] flex flex-col">
            <div className="flex items-center justify-between p-4 border-b">
              <div>
                <h3 className="text-lg font-semibold flex items-center gap-2">
                  <History className="h-5 w-5 text-blue-600" />
                  Historial de Movimientos
                </h3>
                <p className="text-sm text-muted-foreground">{historialRepuesto.nombre} • Stock actual: {historialRepuesto.stock_actual}</p>
              </div>
              <Button variant="ghost" size="sm" onClick={cerrarHistorial}>
                <X className="h-4 w-4" />
              </Button>
            </div>

            <div className="p-4 overflow-y-auto flex-1">
              {loadingHistorial ? (
                <div className="flex items-center justify-center py-8">
                  <div className="text-muted-foreground">Cargando historial...</div>
                </div>
              ) : (
                <DataTable
                  columns={movimientosColumns}
                  data={movimientos}
                  searchPlaceholder="Buscar por usuario, observaciones..."
                  defaultPageSize={10}
                  pageSizeOptions={[5, 10, 25, 50]}
                />
              )}
            </div>

            <div className="flex justify-end p-4 border-t">
              <Button variant="outline" onClick={cerrarHistorial}>
                Cerrar
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
