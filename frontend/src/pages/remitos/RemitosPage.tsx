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
import { FileText, Download, Trash2, Plus, ChevronDown, Copy, FileCheck } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { remitosService } from '@/services/remitosService'
import { Remito } from '@/types'
import { formatDate, formatNumber } from '@/lib/utils'

type TipoCopia = 'original' | 'duplicado' | 'triplicado'

export default function RemitosPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [sorting, setSorting] = useState<SortingState>([])
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([])
  const [downloadingId, setDownloadingId] = useState<string | null>(null)
  const [showDropdown, setShowDropdown] = useState<string | null>(null)

  const { data: remitos = [], isLoading } = useQuery({
    queryKey: ['remitos'],
    queryFn: () => remitosService.getAll(0, 500),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => remitosService.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['remitos'] })
    },
  })

  const handleDelete = async (id: string, numero: string) => {
    if (window.confirm(`¿Está seguro de eliminar el remito ${numero}?`)) {
      try {
        await deleteMutation.mutateAsync(id)
      } catch (error) {
        alert('Error al eliminar el remito')
      }
    }
  }

  const handleDownloadPDF = async (id: string, numeroRemito: string, tipo: TipoCopia) => {
    setDownloadingId(id)
    setShowDropdown(null)
    try {
      const blob = await remitosService.downloadPDF(id, tipo)
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `remito-${numeroRemito}-${tipo}.pdf`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (error) {
      alert('Error al descargar el PDF')
    } finally {
      setDownloadingId(null)
    }
  }

  const columns: ColumnDef<Remito>[] = [
    {
      accessorKey: 'numero_remito',
      header: 'N° Remito',
      cell: ({ row }) => (
        <div className="font-medium">{row.getValue('numero_remito')}</div>
      ),
    },
    {
      accessorKey: 'fecha_emision',
      header: 'Fecha Emisión',
      cell: ({ row }) => {
        const fecha = row.getValue('fecha_emision') as string
        return <div className="text-sm">{formatDate(fecha)}</div>
      },
    },
    {
      id: 'pesaje',
      header: 'Pesaje',
      cell: ({ row }) => {
        const remito = row.original
        return (
          <div className="text-sm">
            #{remito.pesaje_numero || '-'}
          </div>
        )
      },
    },
    {
      id: 'camion',
      header: 'Camión',
      cell: ({ row }) => {
        const remito = row.original
        return <div className="font-medium">{remito.camion_patente || '-'}</div>
      },
    },
    {
      id: 'material',
      header: 'Material',
      cell: ({ row }) => {
        const remito = row.original
        return (
          <span className="inline-flex px-2 py-1 bg-blue-100 text-blue-700 text-xs font-semibold rounded">
            {remito.material || '-'}
          </span>
        )
      },
    },
    {
      id: 'cliente',
      header: 'Cliente/Destino',
      cell: ({ row }) => {
        const remito = row.original
        return <div className="text-sm">{remito.cliente_destino || '-'}</div>
      },
    },
    {
      id: 'peso_neto',
      header: 'Peso Neto',
      cell: ({ row }) => {
        const remito = row.original
        return (
          <div className="text-sm font-semibold text-green-700">
            {formatNumber((remito.peso_neto || 0) / 1000, 2)} t
          </div>
        )
      },
    },
    {
      id: 'actions',
      header: 'Acciones',
      cell: ({ row }) => {
        const remito = row.original
        const isDownloading = downloadingId === remito.id
        const isDropdownOpen = showDropdown === remito.id

        return (
          <div className="flex items-center gap-2">
            {/* Dropdown de descarga */}
            <div className="relative">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowDropdown(isDropdownOpen ? null : remito.id)}
                disabled={isDownloading}
                className="flex items-center gap-1"
                title="Descargar PDF"
              >
                <Download className={`h-4 w-4 text-blue-600 ${isDownloading ? 'animate-pulse' : ''}`} />
                <ChevronDown className="h-3 w-3" />
              </Button>

              {isDropdownOpen && (
                <>
                  {/* Overlay para cerrar al hacer clic afuera */}
                  <div
                    className="fixed inset-0 z-10"
                    onClick={() => setShowDropdown(null)}
                  />

                  {/* Menú dropdown */}
                  <div className="absolute right-0 mt-1 w-40 bg-white border rounded-md shadow-lg z-20">
                    <button
                      onClick={() => handleDownloadPDF(remito.id, remito.numero_remito, 'original')}
                      className="w-full flex items-center gap-2 px-3 py-2 text-sm hover:bg-gray-100 text-left"
                    >
                      <FileCheck className="h-4 w-4 text-green-600" />
                      Original
                    </button>
                    <button
                      onClick={() => handleDownloadPDF(remito.id, remito.numero_remito, 'duplicado')}
                      className="w-full flex items-center gap-2 px-3 py-2 text-sm hover:bg-gray-100 text-left"
                    >
                      <Copy className="h-4 w-4 text-blue-600" />
                      Duplicado
                    </button>
                    <button
                      onClick={() => handleDownloadPDF(remito.id, remito.numero_remito, 'triplicado')}
                      className="w-full flex items-center gap-2 px-3 py-2 text-sm hover:bg-gray-100 text-left"
                    >
                      <Copy className="h-4 w-4 text-orange-600" />
                      Triplicado
                    </button>
                  </div>
                </>
              )}
            </div>

            <Button
              variant="outline"
              size="sm"
              onClick={() => handleDelete(remito.id, remito.numero_remito)}
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
    data: remitos,
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
        <div className="text-gray-500">Cargando remitos...</div>
      </div>
    )
  }

  const totalToneladas = remitos.reduce((sum, r) => sum + (r.peso_neto || 0) / 1000, 0)

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 flex items-center gap-2">
            <FileText className="h-6 w-6 sm:h-8 sm:w-8" />
            Remitos
          </h1>
          <p className="text-gray-500 mt-1 text-sm sm:text-base">Gestión de remitos de transporte</p>
        </div>
        <Button onClick={() => navigate('/pesajes')} className="w-full sm:w-auto">
          <Plus className="h-4 w-4 mr-2" />
          Generar desde Pesaje
        </Button>
      </div>

      {/* Estadísticas */}
      <div className="grid grid-cols-2 gap-3 sm:gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Total Remitos</div>
            <div className="text-2xl font-bold">{remitos.length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Total Toneladas</div>
            <div className="text-2xl font-bold text-green-600">
              {formatNumber(totalToneladas, 2)} t
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader className="px-3 sm:px-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <CardTitle className="text-lg sm:text-xl">Lista de Remitos</CardTitle>
            <Input
              placeholder="Buscar por número..."
              value={(table.getColumn('numero_remito')?.getFilterValue() as string) ?? ''}
              onChange={(event) =>
                table.getColumn('numero_remito')?.setFilterValue(event.target.value)
              }
              className="w-full sm:max-w-sm"
            />
          </div>
        </CardHeader>
        <CardContent className="px-3 sm:px-6">
          <div className="rounded-md border overflow-x-auto">
            <table className="w-full min-w-[700px]">
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
                      No hay remitos registrados
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
          <div className="mt-4 text-sm text-muted-foreground">
            Total: {remitos.length} remitos • {formatNumber(totalToneladas, 2)} toneladas
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
