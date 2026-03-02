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
import { Truck, Plus, Pencil, Trash2, Wrench, AlertTriangle, Cog } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { camionesService } from '@/services/camionesService'
import { Camion, CategoriaEquipo } from '@/types'
import { formatDate } from '@/lib/utils'
import { useIsAdmin } from '@/hooks/useIsAdmin'

export default function CamionesPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const isAdmin = useIsAdmin()
  const [sorting, setSorting] = useState<SortingState>([])
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([])
  const [activeTab, setActiveTab] = useState<CategoriaEquipo>('camion')

  const { data: todosEquipos = [], isLoading } = useQuery({
    queryKey: ['camiones'],
    queryFn: () => camionesService.getAll(true),
  })

  // Filtrar por categoría según el tab activo
  const equiposFiltrados = todosEquipos.filter(
    (equipo) => equipo.categoria === activeTab
  )

  const deleteMutation = useMutation({
    mutationFn: (id: string) => camionesService.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['camiones'] })
    },
  })

  const handleDelete = async (id: string, identificador: string) => {
    const tipo = activeTab === 'camion' ? 'camión' : 'máquina'
    if (window.confirm(`¿Está seguro de eliminar ${tipo} ${identificador}?`)) {
      try {
        await deleteMutation.mutateAsync(id)
      } catch (error) {
        alert(`Error al eliminar ${tipo}`)
      }
    }
  }

  // Columnas para camiones
  const columnsCamiones: ColumnDef<Camion>[] = [
    {
      accessorKey: 'patente',
      header: 'Patente',
      cell: ({ row }) => (
        <div className="font-medium">{row.getValue('patente') || '-'}</div>
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
            {isAdmin && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleDelete(camion.id, camion.patente || camion.nombre || 'este equipo')}
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

  // Columnas para máquinas (usa horómetro en lugar de kilometraje)
  const columnsMaquinas: ColumnDef<Camion>[] = [
    {
      accessorKey: 'nombre',
      header: 'Nombre',
      cell: ({ row }) => (
        <div className="font-medium">{row.getValue('nombre') || row.original.codigo_interno || '-'}</div>
      ),
    },
    {
      accessorKey: 'tipo_maquina',
      header: 'Tipo',
      cell: ({ row }) => {
        const tipo = row.getValue('tipo_maquina') as string | null
        const tipoLabels: Record<string, string> = {
          'pala_cargadora': 'Pala Cargadora',
          'retroexcavadora': 'Retroexcavadora',
          'excavadora': 'Excavadora',
          'motoniveladora': 'Motoniveladora',
          'compactadora': 'Compactadora',
          'trituradora': 'Trituradora',
          'generador': 'Generador',
          'bomba': 'Bomba',
          'otro': 'Otro',
        }
        return <div>{tipo ? tipoLabels[tipo] || tipo : '-'}</div>
      },
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
      accessorKey: 'horometro_actual',
      header: 'Horómetro',
      cell: ({ row }) => {
        const horas = row.getValue('horometro_actual') as number | null
        return <div>{horas != null ? `${Number(horas).toLocaleString('es-AR')} hs` : '-'}</div>
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
        const maquina = row.original
        const requiere = maquina.requiere_servicio

        // Para máquinas, usamos horas
        if (!maquina.proximo_servicio_horas) {
          return <span className="text-sm text-muted-foreground">No definido</span>
        }

        const horasActuales = Number(maquina.horometro_actual) || 0
        const proximoServicio = Number(maquina.proximo_servicio_horas) || 0
        const horasRestantes = proximoServicio - horasActuales

        return (
          <div className="flex items-center gap-2">
            {requiere && <AlertTriangle className="h-4 w-4 text-orange-500" />}
            <div>
              <div className={`text-sm font-medium ${requiere ? 'text-orange-600' : ''}`}>
                {proximoServicio.toLocaleString('es-AR')} hs
              </div>
              <div className={`text-xs ${horasRestantes <= 0 ? 'text-red-600 font-semibold' : horasRestantes <= 50 ? 'text-orange-500' : 'text-muted-foreground'}`}>
                {horasRestantes <= 0 ? `¡Pasado por ${Math.abs(horasRestantes).toLocaleString('es-AR')} hs!` : `Faltan ${horasRestantes.toLocaleString('es-AR')} hs`}
              </div>
            </div>
          </div>
        )
      },
    },
    {
      id: 'actions',
      header: 'Acciones',
      cell: ({ row }) => {
        const maquina = row.original
        return (
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => navigate(`/camiones/${maquina.id}`)}
              title="Ver servicios y mantenimientos"
            >
              <Wrench className="h-4 w-4" />
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => navigate(`/camiones/${maquina.id}/editar`)}
              title="Editar"
            >
              <Pencil className="h-4 w-4" />
            </Button>
            {isAdmin && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleDelete(maquina.id, maquina.nombre || maquina.codigo_interno || 'esta máquina')}
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

  const columns = activeTab === 'camion' ? columnsCamiones : columnsMaquinas

  const table = useReactTable({
    data: equiposFiltrados,
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
    // Reset sorting when tab changes to avoid column mismatch
    autoResetAll: false,
  })

  // Contadores
  const totalCamiones = todosEquipos.filter(e => e.categoria === 'camion').length
  const totalMaquinas = todosEquipos.filter(e => e.categoria === 'maquina').length

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-gray-500">Cargando equipos...</div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 flex items-center gap-2">
            {activeTab === 'camion' ? (
              <Truck className="h-6 w-6 sm:h-8 sm:w-8" />
            ) : (
              <Cog className="h-6 w-6 sm:h-8 sm:w-8" />
            )}
            {activeTab === 'camion' ? 'Camiones' : 'Máquinas'}
          </h1>
          <p className="text-gray-500 mt-1 text-sm sm:text-base">
            {activeTab === 'camion'
              ? 'Gestión de flota de camiones'
              : 'Gestión de maquinaria y equipos'}
          </p>
        </div>
        <Button
          onClick={() => navigate(`/camiones/nuevo?categoria=${activeTab}`)}
          className="w-full sm:w-auto"
        >
          <Plus className="h-4 w-4 mr-2" />
          {activeTab === 'camion' ? 'Nuevo Camión' : 'Nueva Máquina'}
        </Button>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b">
        <button
          type="button"
          onClick={() => {
            setActiveTab('camion')
            setSorting([])
            setColumnFilters([])
          }}
          className={`flex items-center gap-2 px-4 py-2 border-b-2 transition-colors cursor-pointer ${
            activeTab === 'camion'
              ? 'border-brand-600 text-brand-600 font-medium'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          <Truck className="h-4 w-4" />
          Camiones
          <span className={`text-xs px-2 py-0.5 rounded-full ${
            activeTab === 'camion' ? 'bg-brand-100 text-brand-700' : 'bg-gray-100'
          }`}>
            {totalCamiones}
          </span>
        </button>
        <button
          type="button"
          onClick={() => {
            setActiveTab('maquina')
            setSorting([])
            setColumnFilters([])
          }}
          className={`flex items-center gap-2 px-4 py-2 border-b-2 transition-colors cursor-pointer ${
            activeTab === 'maquina'
              ? 'border-brand-600 text-brand-600 font-medium'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          <Cog className="h-4 w-4" />
          Máquinas
          <span className={`text-xs px-2 py-0.5 rounded-full ${
            activeTab === 'maquina' ? 'bg-brand-100 text-brand-700' : 'bg-gray-100'
          }`}>
            {totalMaquinas}
          </span>
        </button>
      </div>

      <Card>
        <CardHeader className="px-3 sm:px-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <CardTitle className="text-lg sm:text-xl">
              Lista de {activeTab === 'camion' ? 'Camiones' : 'Máquinas'}
            </CardTitle>
            <Input
              placeholder={activeTab === 'camion' ? 'Buscar por patente...' : 'Buscar por nombre...'}
              value={(table.getColumn(activeTab === 'camion' ? 'patente' : 'nombre')?.getFilterValue() as string) ?? ''}
              onChange={(event) =>
                table.getColumn(activeTab === 'camion' ? 'patente' : 'nombre')?.setFilterValue(event.target.value)
              }
              className="w-full sm:max-w-sm"
            />
          </div>
        </CardHeader>
        <CardContent className="px-3 sm:px-6">
          <div className="rounded-md border overflow-x-auto">
            <table className="w-full min-w-[800px]">
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
                      No hay {activeTab === 'camion' ? 'camiones' : 'máquinas'} registrados
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
          <div className="mt-4 text-sm text-muted-foreground">
            Total: {equiposFiltrados.length} {activeTab === 'camion' ? 'camiones' : 'máquinas'}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
