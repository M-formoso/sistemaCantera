import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import {
  ColumnDef,
  flexRender,
  getCoreRowModel,
  useReactTable,
  getSortedRowModel,
  SortingState,
  getFilteredRowModel,
  ColumnFiltersState,
} from '@tanstack/react-table'
import { Package, Plus, Pencil, Trash2, AlertTriangle, TrendingUp, TrendingDown } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { repuestosService } from '@/services/repuestosService'
import { Repuesto } from '@/types'
import { formatCurrency } from '@/lib/utils'

export default function RepuestosPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [sorting, setSorting] = useState<SortingState>([])
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([])
  const [showOnlyBajoStock, setShowOnlyBajoStock] = useState(false)

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

  const handleDelete = async (id: string, nombre: string) => {
    if (window.confirm(`¿Está seguro de eliminar el repuesto ${nombre}?`)) {
      try {
        await deleteMutation.mutateAsync(id)
      } catch (error) {
        alert('Error al eliminar el repuesto')
      }
    }
  }

  const handleRegistrarMovimiento = (id: string, tipo: 'entrada' | 'salida') => {
    navigate(`/repuestos/${id}/movimiento?tipo=${tipo}`)
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
              onClick={() => handleRegistrarMovimiento(repuesto.id, 'entrada')}
              title="Registrar entrada"
            >
              <TrendingUp className="h-4 w-4 text-green-600" />
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleRegistrarMovimiento(repuesto.id, 'salida')}
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
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleDelete(repuesto.id, repuesto.nombre)}
              disabled={deleteMutation.isPending}
              title="Eliminar"
            >
              <Trash2 className="h-4 w-4 text-red-600" />
            </Button>
          </div>
        )
      },
    },
  ]

  const table = useReactTable({
    data: repuestos,
    columns,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    state: {
      sorting,
      columnFilters,
    },
  })

  const repuestosBajoStock = repuestos.filter(r => r.stock_actual <= r.stock_minimo).length

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-gray-500">Cargando repuestos...</div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
            <Package className="h-8 w-8" />
            Repuestos
          </h1>
          <p className="text-gray-500 mt-1">Gestión de inventario de repuestos</p>
        </div>
        <Button onClick={() => navigate('/repuestos/nuevo')}>
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
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>
              {showOnlyBajoStock ? 'Repuestos con Stock Bajo' : 'Lista de Repuestos'}
            </CardTitle>
            <div className="flex items-center gap-4">
              {showOnlyBajoStock && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowOnlyBajoStock(false)}
                >
                  Ver todos
                </Button>
              )}
              <Input
                placeholder="Buscar por nombre o código..."
                value={(table.getColumn('nombre')?.getFilterValue() as string) ?? ''}
                onChange={(event) =>
                  table.getColumn('nombre')?.setFilterValue(event.target.value)
                }
                className="max-w-sm"
              />
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="rounded-md border">
            <table className="w-full">
              <thead>
                {table.getHeaderGroups().map((headerGroup) => (
                  <tr key={headerGroup.id} className="border-b bg-gray-50">
                    {headerGroup.headers.map((header) => (
                      <th
                        key={header.id}
                        className="px-4 py-3 text-left text-sm font-medium text-gray-700"
                      >
                        {header.isPlaceholder
                          ? null
                          : flexRender(
                              header.column.columnDef.header,
                              header.getContext()
                            )}
                      </th>
                    ))}
                  </tr>
                ))}
              </thead>
              <tbody>
                {table.getRowModel().rows?.length ? (
                  table.getRowModel().rows.map((row) => (
                    <tr
                      key={row.id}
                      className="border-b hover:bg-gray-50 transition-colors"
                    >
                      {row.getVisibleCells().map((cell) => (
                        <td key={cell.id} className="px-4 py-3 text-sm">
                          {flexRender(
                            cell.column.columnDef.cell,
                            cell.getContext()
                          )}
                        </td>
                      ))}
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td
                      colSpan={columns.length}
                      className="px-4 py-8 text-center text-muted-foreground"
                    >
                      No hay repuestos registrados
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
          <div className="mt-4 text-sm text-muted-foreground">
            Total: {repuestos.length} repuestos
            {repuestosBajoStock > 0 && ` • ${repuestosBajoStock} con stock bajo`}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
