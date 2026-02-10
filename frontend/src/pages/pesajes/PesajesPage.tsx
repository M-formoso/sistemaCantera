import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { ColumnDef } from '@tanstack/react-table'
import { Scale, Plus, Pencil, Trash2, FileText, Printer } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { DataTable } from '@/components/ui/data-table'
import { pesajesService } from '@/services/pesajesService'
import { Pesaje } from '@/types'
import { formatDate, formatNumber } from '@/lib/utils'

export default function PesajesPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const { data: pesajes = [], isLoading } = useQuery({
    queryKey: ['pesajes'],
    queryFn: () => pesajesService.getAll(0, 1000),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => pesajesService.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pesajes'] })
    },
  })

  const handleDelete = async (id: string, numero: number) => {
    if (window.confirm(`¿Está seguro de eliminar el pesaje #${numero}?`)) {
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
      alert('Error al descargar el ticket PDF')
    }
  }

  const columns: ColumnDef<Pesaje>[] = [
    {
      accessorKey: 'numero_pesaje',
      header: '#',
      cell: ({ row }) => (
        <div className="font-medium">#{row.getValue('numero_pesaje')}</div>
      ),
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
      accessorKey: 'camion_patente',
      header: 'Camión',
      cell: ({ row }) => (
        <div className="font-medium">{row.getValue('camion_patente')}</div>
      ),
    },
    {
      accessorKey: 'material',
      header: 'Material',
      cell: ({ row }) => {
        const material = row.getValue('material') as string
        return (
          <span className="inline-flex px-2 py-1 bg-blue-100 text-blue-700 text-xs font-semibold rounded">
            {material}
          </span>
        )
      },
    },
    {
      accessorKey: 'cliente_destino',
      header: 'Cliente/Destino',
      cell: ({ row }) => (
        <div className="text-sm">{row.getValue('cliente_destino')}</div>
      ),
    },
    {
      accessorKey: 'peso_bruto',
      header: 'Peso Bruto',
      cell: ({ row }) => {
        const pesoBruto = row.getValue('peso_bruto') as number
        return <div className="text-sm text-right">{formatNumber(pesoBruto)} kg</div>
      },
    },
    {
      accessorKey: 'peso_tara',
      header: 'Tara',
      cell: ({ row }) => {
        const pesoTara = row.getValue('peso_tara') as number
        return <div className="text-sm text-right">{formatNumber(pesoTara)} kg</div>
      },
    },
    {
      accessorKey: 'peso_neto',
      header: 'Peso Neto',
      cell: ({ row }) => {
        const pesoNeto = row.getValue('peso_neto') as number
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
        return (
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleDownloadPDF(pesaje.id, pesaje.numero_pesaje)}
              title="Descargar Ticket PDF"
            >
              <Printer className="h-4 w-4 text-green-600" />
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => navigate(`/remitos/generar?pesaje=${pesaje.id}`)}
              title="Generar remito"
            >
              <FileText className="h-4 w-4 text-blue-600" />
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => navigate(`/pesajes/${pesaje.id}/editar`)}
              title="Editar"
            >
              <Pencil className="h-4 w-4" />
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleDelete(pesaje.id, pesaje.numero_pesaje)}
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

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-gray-500">Cargando pesajes...</div>
      </div>
    )
  }

  const totalToneladas = pesajes.reduce((sum, p) => sum + p.peso_neto / 1000, 0)

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 flex items-center gap-2">
            <Scale className="h-6 w-6 sm:h-8 sm:w-8" />
            Pesajes
          </h1>
          <p className="text-gray-500 mt-1 text-sm sm:text-base">Registro de pesajes de camiones</p>
        </div>
        <Button onClick={() => navigate('/pesajes/nuevo')} className="w-full sm:w-auto">
          <Plus className="h-4 w-4 mr-2" />
          Nuevo Pesaje
        </Button>
      </div>

      {/* Estadísticas rápidas */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 sm:gap-4">
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
              {pesajes.length > 0 ? formatNumber(totalToneladas / pesajes.length, 2) : 0} t
            </div>
          </CardContent>
        </Card>
      </div>

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
