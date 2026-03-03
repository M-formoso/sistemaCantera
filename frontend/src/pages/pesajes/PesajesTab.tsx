import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { ColumnDef } from '@tanstack/react-table'
import { Plus, Pencil, Trash2, Download, DollarSign, Scale, Clock } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { DataTable } from '@/components/ui/data-table'
import { pesajesService } from '@/services/pesajesService'
import { Pesaje } from '@/types'
import { formatDate, formatNumber } from '@/lib/utils'
import { useIsAdmin } from '@/hooks/useIsAdmin'

export default function PesajesTab() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const isAdmin = useIsAdmin()

  // Query para pesajes
  const { data: pesajes = [], isLoading } = useQuery({
    queryKey: ['pesajes'],
    queryFn: () => pesajesService.getAll(0, 500),
  })

  // Mutation para eliminar
  const deleteMutation = useMutation({
    mutationFn: (id: string) => pesajesService.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pesajes'] })
      queryClient.invalidateQueries({ queryKey: ['remitos'] })
    },
  })

  // Handlers
  const handleDelete = async (id: string, numero: number) => {
    if (window.confirm(`¿Está seguro de eliminar el pesaje #${numero}? También se eliminará el remito asociado.`)) {
      try {
        await deleteMutation.mutateAsync(id)
      } catch (error) {
        alert('Error al eliminar el pesaje')
      }
    }
  }

  const handleDownloadPDF = async (id: string, numeroPesaje: number) => {
    try {
      await pesajesService.downloadTicketPDF(id, numeroPesaje)
    } catch (error) {
      alert('Error al descargar el comprobante')
    }
  }

  // Columnas para pesajes
  const columns: ColumnDef<Pesaje>[] = [
    {
      accessorKey: 'numero_pesaje',
      header: '#',
      cell: ({ row }) => (
        <div className="font-medium">#{row.getValue('numero_pesaje')}</div>
      ),
    },
    {
      accessorKey: 'estado',
      header: 'Estado',
      cell: ({ row }) => {
        const estado = row.original.estado
        const esPendiente = estado === 'pendiente'
        return (
          <span className={`inline-flex items-center gap-1 px-2 py-1 text-xs font-semibold rounded ${
            esPendiente
              ? 'bg-yellow-100 text-yellow-700'
              : 'bg-green-100 text-green-700'
          }`}>
            {esPendiente ? <Clock className="h-3 w-3" /> : null}
            {esPendiente ? 'Pendiente' : 'Completado'}
          </span>
        )
      },
    },
    {
      accessorKey: 'fecha',
      header: 'Fecha',
      cell: ({ row }) => {
        const fecha = row.getValue('fecha') as string
        return <div className="text-sm">{formatDate(fecha)}</div>
      },
    },
    {
      id: 'patente',
      header: 'Patente',
      cell: ({ row }) => {
        const pesaje = row.original
        const patente = pesaje.camion_patente || pesaje.patente_externa || '-'
        return <div className="font-medium">{patente}</div>
      },
    },
    {
      accessorKey: 'material',
      header: 'Material',
      cell: ({ row }) => {
        const material = row.getValue('material') as string
        return (
          <span className="inline-flex px-2 py-1 bg-blue-100 text-blue-700 text-xs font-semibold rounded">
            {material || '-'}
          </span>
        )
      },
    },
    {
      id: 'cliente',
      header: 'Cliente',
      cell: ({ row }) => {
        const pesaje = row.original
        const cliente = pesaje.cliente_nombre || '-'
        return <div className="text-sm">{cliente}</div>
      },
    },
    {
      accessorKey: 'peso_tara',
      header: 'Tara',
      cell: ({ row }) => {
        const pesoTara = row.original.peso_tara as number
        return (
          <div className="text-sm text-right">
            {pesoTara ? `${formatNumber(pesoTara)} kg` : '-'}
          </div>
        )
      },
    },
    {
      accessorKey: 'peso_neto',
      header: 'Neto',
      cell: ({ row }) => {
        const pesoNeto = row.getValue('peso_neto') as number
        if (!pesoNeto) {
          return <div className="text-sm text-gray-400 text-right">-</div>
        }
        return (
          <div className="text-sm font-semibold text-right text-green-700">
            {formatNumber(pesoNeto / 1000, 2)} t
          </div>
        )
      },
    },
    {
      id: 'actions',
      header: 'Acciones',
      cell: ({ row }) => {
        const pesaje = row.original
        const esPendiente = pesaje.estado === 'pendiente'

        return (
          <div className="flex items-center gap-1">
            {/* Botón para completar pesaje pendiente */}
            {esPendiente && (
              <Button
                size="sm"
                className="bg-yellow-500 hover:bg-yellow-600 text-white"
                onClick={() => navigate(`/pesajes-remitos/nuevo?completar=${pesaje.id}`)}
                title="Registrar peso bruto"
              >
                <Scale className="h-4 w-4 mr-1" />
                Completar
              </Button>
            )}

            {/* Botón descargar PDF solo para completados */}
            {!esPendiente && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleDownloadPDF(pesaje.id, pesaje.numero_pesaje)}
                title="Descargar Comprobante"
              >
                <Download className="h-4 w-4 text-green-600" />
              </Button>
            )}

            <Button
              variant="outline"
              size="sm"
              onClick={() => navigate(`/pesajes-remitos/${pesaje.id}/editar`)}
              title="Editar"
            >
              <Pencil className="h-4 w-4" />
            </Button>

            {isAdmin && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleDelete(pesaje.id, pesaje.numero_pesaje)}
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

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-gray-500">Cargando pesajes...</div>
      </div>
    )
  }

  const totalToneladas = pesajes.reduce((sum, p) => sum + (p.peso_neto || 0) / 1000, 0)
  const promedioToneladas = pesajes.length > 0 ? totalToneladas / pesajes.length : 0
  const totalIngresos = pesajes.reduce((sum, p) => sum + (p.importe_total || 0), 0)

  return (
    <div className="space-y-6">
      {/* Header con botón */}
      <div className="flex justify-end">
        <Button onClick={() => navigate('/pesajes-remitos/nuevo')}>
          <Plus className="h-4 w-4 mr-2" />
          Nuevo Pesaje
        </Button>
      </div>

      {/* Estadísticas */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-3 sm:gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Total Pesajes</div>
            <div className="text-2xl font-bold">{pesajes.length}</div>
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
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Promedio por Pesaje</div>
            <div className="text-2xl font-bold">
              {formatNumber(promedioToneladas, 2)} t
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground flex items-center gap-1">
              <DollarSign className="h-3 w-3" />
              Ingresos por Pesajes
            </div>
            <div className="text-2xl font-bold text-blue-600">
              ${formatNumber(totalIngresos, 2)}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Tabla */}
      <Card>
        <CardHeader className="px-3 sm:px-6">
          <CardTitle className="text-lg sm:text-xl">Lista de Pesajes</CardTitle>
        </CardHeader>
        <CardContent className="px-3 sm:px-6">
          <DataTable
            columns={columns}
            data={pesajes}
            searchPlaceholder="Buscar por patente, material, cliente..."
            defaultPageSize={10}
          />
        </CardContent>
      </Card>
    </div>
  )
}
