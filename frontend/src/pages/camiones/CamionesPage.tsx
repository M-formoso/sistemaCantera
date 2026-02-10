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
import { Truck, Plus, Pencil, Trash2, Wrench, AlertTriangle } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { camionesService } from '@/services/camionesService'
import { Camion } from '@/types'
import { formatDate } from '@/lib/utils'

export default function CamionesPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [sorting, setSorting] = useState<SortingState>([])
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([])

  const { data: camiones = [], isLoading } = useQuery({
    queryKey: ['camiones'],
    queryFn: () => camionesService.getAll(true),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => camionesService.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['camiones'] })
    },
  })

  const handleDelete = async (id: string, patente: string) => {
    if (window.confirm(`¿Está seguro de eliminar el camión ${patente}?`)) {
      try {
        await deleteMutation.mutateAsync(id)
      } catch (error) {
        alert('Error al eliminar el camión')
      }
    }
  }

  const columns: ColumnDef<Camion>[] = [
    {
      accessorKey: 'patente',
      header: 'Patente',
      cell: ({ row }) => (
        <div className="font-medium">{row.getValue('patente')}</div>
      ),
    },
    {
      accessorKey: 'marca',
      header: 'Marca',
    },
    {
      accessorKey: 'modelo',
      header: 'Modelo',
    },
    {
      accessorKey: 'año',
      header: 'Año',
    },
    {
      accessorKey: 'estado',
      header: 'Estado',
      cell: ({ row }) => {
        const estado = row.getValue('estado') as string
        const colorClass =
          estado === 'operativo' ? 'bg-green-100 text-green-700' :
          estado === 'en_servicio' ? 'bg-orange-100 text-orange-700' :
          'bg-red-100 text-red-700'

        return (
          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${colorClass}`}>
            {estado === 'operativo' ? 'Operativo' :
             estado === 'en_servicio' ? 'En servicio' :
             'Fuera de servicio'}
          </span>
        )
      },
    },
    {
      accessorKey: 'kilometraje_actual',
      header: 'Kilometraje',
      cell: ({ row }) => {
        const km = row.getValue('kilometraje_actual') as number | null
        return <div>{km != null ? `${km.toLocaleString('es-AR')} km` : '-'}</div>
      },
    },
    {
      accessorKey: 'ultimo_servicio',
      header: 'Último Servicio',
      cell: ({ row }) => {
        const fecha = row.getValue('ultimo_servicio') as string | null
        return <div className="text-sm text-muted-foreground">
          {fecha ? formatDate(fecha) : 'Sin servicios'}
        </div>
      },
    },
    {
      id: 'proximo_servicio',
      header: 'Próximo Servicio',
      cell: ({ row }) => {
        const camion = row.original
        const requiere = camion.requiere_servicio
        const kmRestantes = camion.km_para_proximo_servicio

        if (!camion.proximo_servicio_km) {
          return <span className="text-sm text-muted-foreground">No definido</span>
        }

        return (
          <div className="flex items-center gap-2">
            {requiere && <AlertTriangle className="h-4 w-4 text-orange-500" />}
            <div>
              <div className={`text-sm font-medium ${requiere ? 'text-orange-600' : ''}`}>
                {camion.proximo_servicio_km?.toLocaleString('es-AR')} km
              </div>
              {kmRestantes != null && (
                <div className={`text-xs ${kmRestantes <= 0 ? 'text-red-600 font-semibold' : kmRestantes <= 500 ? 'text-orange-500' : 'text-muted-foreground'}`}>
                  {kmRestantes <= 0 ? `¡Pasado por ${Math.abs(kmRestantes).toLocaleString('es-AR')} km!` : `Faltan ${kmRestantes.toLocaleString('es-AR')} km`}
                </div>
              )}
            </div>
          </div>
        )
      },
    },
    {
      id: 'actions',
      header: 'Acciones',
      cell: ({ row }) => {
        const camion = row.original
        return (
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => navigate(`/camiones/${camion.id}`)}
              title="Ver servicios"
            >
              <Wrench className="h-4 w-4" />
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => navigate(`/camiones/${camion.id}/editar`)}
              title="Editar"
            >
              <Pencil className="h-4 w-4" />
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleDelete(camion.id, camion.patente)}
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
    data: camiones,
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

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-gray-500">Cargando camiones...</div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
            <Truck className="h-8 w-8" />
            Camiones
          </h1>
          <p className="text-gray-500 mt-1">Gestión de flota de camiones</p>
        </div>
        <Button onClick={() => navigate('/camiones/nuevo')}>
          <Plus className="h-4 w-4 mr-2" />
          Nuevo Camión
        </Button>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Lista de Camiones</CardTitle>
            <div className="flex items-center gap-4">
              <Input
                placeholder="Buscar por patente..."
                value={(table.getColumn('patente')?.getFilterValue() as string) ?? ''}
                onChange={(event) =>
                  table.getColumn('patente')?.setFilterValue(event.target.value)
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
                      No hay camiones registrados
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
          <div className="mt-4 text-sm text-muted-foreground">
            Total: {camiones.length} camiones
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
