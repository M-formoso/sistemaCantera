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
import { Wrench, Plus, Pencil, Trash2, Calendar, Package } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { serviciosService } from '@/services/serviciosService'
import { Servicio } from '@/types'
import { formatDate, formatCurrency } from '@/lib/utils'
import { useIsAdmin } from '@/hooks/useIsAdmin'

export default function ServiciosPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const isAdmin = useIsAdmin()
  const [sorting, setSorting] = useState<SortingState>([])
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([])
  const [showOnlyProgramados, setShowOnlyProgramados] = useState(false)

  const { data: servicios = [], isLoading } = useQuery({
    queryKey: ['servicios', showOnlyProgramados],
    queryFn: () => showOnlyProgramados ? serviciosService.getProgramados() : serviciosService.getAll(0, 500),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => serviciosService.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['servicios'] })
    },
  })

  const handleDelete = async (id: string, camionPatente: string) => {
    if (window.confirm(`¿Está seguro de eliminar el servicio del camión ${camionPatente}?`)) {
      try {
        await deleteMutation.mutateAsync(id)
      } catch (error) {
        alert('Error al eliminar el servicio')
      }
    }
  }

  const columns: ColumnDef<Servicio>[] = [
    {
      accessorKey: 'fecha',
      header: 'Fecha',
      cell: ({ row }) => {
        const fecha = row.getValue('fecha') as string
        return <div className="text-sm">{formatDate(fecha)}</div>
      },
    },
    {
      accessorKey: 'camion_patente',
      header: 'Camión',
      cell: ({ row }) => (
        <div className="font-medium">{row.getValue('camion_patente')}</div>
      ),
    },
    {
      accessorKey: 'tipo',
      header: 'Tipo',
      cell: ({ row }) => {
        const tipo = row.getValue('tipo') as string
        const colorClass =
          tipo === 'preventivo' ? 'bg-blue-100 text-blue-700' :
          tipo === 'correctivo' ? 'bg-orange-100 text-orange-700' :
          'bg-purple-100 text-purple-700'

        return (
          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded ${colorClass}`}>
            {tipo === 'preventivo' ? 'Preventivo' :
             tipo === 'correctivo' ? 'Correctivo' :
             'Reparación'}
          </span>
        )
      },
    },
    {
      accessorKey: 'descripcion',
      header: 'Descripción',
      cell: ({ row }) => (
        <div className="text-sm max-w-xs truncate">{row.getValue('descripcion')}</div>
      ),
    },
    {
      accessorKey: 'kilometraje_actual',
      header: 'Kilometraje',
      cell: ({ row }) => {
        const km = row.getValue('kilometraje_actual') as number | null
        return <div className="text-sm">{km ? km.toLocaleString('es-AR') : '-'} km</div>
      },
    },
    {
      id: 'repuestos',
      header: 'Repuestos',
      cell: ({ row }) => {
        const servicio = row.original
        const cantidadRepuestos = servicio.repuestos_utilizados?.length || 0
        return (
          <div className="flex items-center gap-1 text-sm text-muted-foreground">
            <Package className="h-3 w-3" />
            {cantidadRepuestos}
          </div>
        )
      },
    },
    {
      accessorKey: 'costo_total',
      header: 'Costo Total',
      cell: ({ row }) => {
        const costo = row.getValue('costo_total') as number
        return <div className="font-semibold">{formatCurrency(costo)}</div>
      },
    },
    {
      id: 'actions',
      header: 'Acciones',
      cell: ({ row }) => {
        const servicio = row.original
        return (
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => navigate(`/servicios/${servicio.id}/editar`)}
              title="Editar"
            >
              <Pencil className="h-4 w-4" />
            </Button>
            {isAdmin && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleDelete(servicio.id, servicio.camion_patente || 'N/A')}
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

  const table = useReactTable({
    data: servicios,
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

  const totalCosto = servicios.reduce((sum, s) => sum + (s.costo_total || 0), 0)
  const serviciosProgramados = servicios.filter(s => new Date(s.fecha) > new Date()).length

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-gray-500">Cargando servicios...</div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
            <Wrench className="h-8 w-8" />
            Servicios
          </h1>
          <p className="text-gray-500 mt-1">Gestión de servicios y mantenimiento</p>
        </div>
        <Button onClick={() => navigate('/servicios/nuevo')}>
          <Plus className="h-4 w-4 mr-2" />
          Nuevo Servicio
        </Button>
      </div>

      {/* Estadísticas rápidas */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Total Servicios</div>
            <div className="text-2xl font-bold">{servicios.length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground flex items-center gap-1">
              <Calendar className="h-4 w-4" />
              Servicios Programados
            </div>
            <div className="text-2xl font-bold text-blue-600">{serviciosProgramados}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Costo Total</div>
            <div className="text-2xl font-bold text-green-600">
              {formatCurrency(totalCosto)}
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>
              {showOnlyProgramados ? 'Servicios Programados' : 'Lista de Servicios'}
            </CardTitle>
            <div className="flex items-center gap-4">
              {!showOnlyProgramados && serviciosProgramados > 0 && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowOnlyProgramados(true)}
                >
                  <Calendar className="h-4 w-4 mr-2" />
                  Ver programados ({serviciosProgramados})
                </Button>
              )}
              {showOnlyProgramados && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowOnlyProgramados(false)}
                >
                  Ver todos
                </Button>
              )}
              <Input
                placeholder="Buscar por patente..."
                value={(table.getColumn('camion_patente')?.getFilterValue() as string) ?? ''}
                onChange={(event) =>
                  table.getColumn('camion_patente')?.setFilterValue(event.target.value)
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
                      No hay servicios registrados
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
          <div className="mt-4 text-sm text-muted-foreground">
            Total: {servicios.length} servicios • {formatCurrency(totalCosto)} en costos
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
