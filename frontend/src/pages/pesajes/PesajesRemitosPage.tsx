import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { ColumnDef } from '@tanstack/react-table'
import { Scale, Plus, Pencil, Trash2, FileText, Printer, Download } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { DataTable } from '@/components/ui/data-table'
import { pesajesService } from '@/services/pesajesService'
import { remitosService } from '@/services/remitosService'
import { Pesaje, Remito } from '@/types'
import { formatDate, formatNumber } from '@/lib/utils'

type TabType = 'pesajes' | 'remitos'

export default function PesajesRemitosPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState<TabType>('pesajes')

  // Query para pesajes
  const { data: pesajes = [], isLoading: isLoadingPesajes } = useQuery({
    queryKey: ['pesajes'],
    queryFn: () => pesajesService.getAll(0, 500),
  })

  // Query para remitos
  const { data: remitos = [], isLoading: isLoadingRemitos } = useQuery({
    queryKey: ['remitos'],
    queryFn: () => remitosService.getAll(0, 500),
  })

  // Mutations
  const deletePesajeMutation = useMutation({
    mutationFn: (id: string) => pesajesService.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pesajes'] })
    },
  })

  const deleteRemitoMutation = useMutation({
    mutationFn: (id: string) => remitosService.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['remitos'] })
    },
  })

  // Handlers
  const handleDeletePesaje = async (id: string, numero: number) => {
    if (window.confirm(`¿Está seguro de eliminar el pesaje #${numero}?`)) {
      try {
        await deletePesajeMutation.mutateAsync(id)
      } catch (error) {
        alert('Error al eliminar el pesaje')
      }
    }
  }

  const handleDeleteRemito = async (id: string, numero: string) => {
    if (window.confirm(`¿Está seguro de eliminar el remito ${numero}?`)) {
      try {
        await deleteRemitoMutation.mutateAsync(id)
      } catch (error) {
        alert('Error al eliminar el remito')
      }
    }
  }

  const handleDownloadTicketPDF = async (id: string, numeroPesaje: number) => {
    try {
      await pesajesService.downloadTicketPDF(id, numeroPesaje)
    } catch (error) {
      alert('Error al descargar el ticket PDF')
    }
  }

  const handleDownloadRemitoPDF = async (id: string, numeroRemito: string) => {
    try {
      const blob = await remitosService.downloadPDF(id)
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `remito-${numeroRemito}.pdf`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (error) {
      alert('Error al descargar el PDF')
    }
  }

  const handleGenerarRemito = (pesajeId: string) => {
    navigate(`/pesajes-remitos/generar-remito?pesaje=${pesajeId}`)
  }

  // Columnas para pesajes
  const pesajesColumns: ColumnDef<Pesaje>[] = [
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
            {material || '-'}
          </span>
        )
      },
    },
    {
      accessorKey: 'cliente_destino',
      header: 'Cliente/Destino',
      cell: ({ row }) => (
        <div className="text-sm">{row.getValue('cliente_destino') || '-'}</div>
      ),
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
      accessorKey: 'remito_generado',
      header: 'Remito',
      cell: ({ row }) => {
        const remitoGenerado = row.getValue('remito_generado') as boolean
        return (
          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded ${
            remitoGenerado
              ? 'bg-green-100 text-green-700'
              : 'bg-gray-100 text-gray-500'
          }`}>
            {remitoGenerado ? 'Generado' : 'Pendiente'}
          </span>
        )
      },
    },
    {
      id: 'actions',
      header: 'Acciones',
      cell: ({ row }) => {
        const pesaje = row.original
        return (
          <div className="flex items-center gap-1">
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleDownloadTicketPDF(pesaje.id, pesaje.numero_pesaje)}
              title="Descargar Ticket PDF"
            >
              <Printer className="h-4 w-4 text-green-600" />
            </Button>
            {!pesaje.remito_generado && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleGenerarRemito(pesaje.id)}
                title="Generar remito"
              >
                <FileText className="h-4 w-4 text-blue-600" />
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
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleDeletePesaje(pesaje.id, pesaje.numero_pesaje)}
              disabled={deletePesajeMutation.isPending}
              title="Eliminar"
            >
              <Trash2 className="h-4 w-4 text-red-600" />
            </Button>
          </div>
        )
      },
    },
  ]

  // Columnas para remitos
  const remitosColumns: ColumnDef<Remito>[] = [
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
        return (
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleDownloadRemitoPDF(remito.id, remito.numero_remito)}
              title="Descargar PDF"
            >
              <Download className="h-4 w-4 text-blue-600" />
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleDeleteRemito(remito.id, remito.numero_remito)}
              disabled={deleteRemitoMutation.isPending}
              title="Eliminar"
            >
              <Trash2 className="h-4 w-4 text-red-600" />
            </Button>
          </div>
        )
      },
    },
  ]

  const isLoading = activeTab === 'pesajes' ? isLoadingPesajes : isLoadingRemitos

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-gray-500">
          Cargando {activeTab === 'pesajes' ? 'pesajes' : 'remitos'}...
        </div>
      </div>
    )
  }

  const totalToneladasPesajes = pesajes.reduce((sum, p) => sum + p.peso_neto / 1000, 0)
  const pesajesSinRemito = pesajes.filter(p => !p.remito_generado).length

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 flex items-center gap-2">
            <Scale className="h-6 w-6 sm:h-8 sm:w-8" />
            Pesajes y Remitos
          </h1>
          <p className="text-gray-500 mt-1 text-sm sm:text-base">
            Gestión de pesajes de camiones y generación de remitos
          </p>
        </div>
        <Button onClick={() => navigate('/pesajes-remitos/nuevo')} className="w-full sm:w-auto">
          <Plus className="h-4 w-4 mr-2" />
          Nuevo Pesaje
        </Button>
      </div>

      {/* Estadísticas rápidas */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Total Pesajes</div>
            <div className="text-2xl font-bold">{pesajes.length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Toneladas Pesadas</div>
            <div className="text-2xl font-bold text-green-600">
              {formatNumber(totalToneladasPesajes, 2)} t
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Remitos Generados</div>
            <div className="text-2xl font-bold">{remitos.length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Pesajes sin Remito</div>
            <div className={`text-2xl font-bold ${pesajesSinRemito > 0 ? 'text-orange-600' : 'text-green-600'}`}>
              {pesajesSinRemito}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('pesajes')}
            className={`py-4 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'pesajes'
                ? 'border-brand-600 text-brand-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <Scale className="h-4 w-4 inline mr-2" />
            Pesajes ({pesajes.length})
          </button>
          <button
            onClick={() => setActiveTab('remitos')}
            className={`py-4 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'remitos'
                ? 'border-brand-600 text-brand-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <FileText className="h-4 w-4 inline mr-2" />
            Remitos ({remitos.length})
          </button>
        </nav>
      </div>

      {/* Content based on active tab */}
      {activeTab === 'pesajes' ? (
        <Card>
          <CardHeader className="px-3 sm:px-6">
            <CardTitle className="text-lg sm:text-xl">Lista de Pesajes</CardTitle>
          </CardHeader>
          <CardContent className="px-3 sm:px-6">
            <DataTable
              columns={pesajesColumns}
              data={pesajes}
              searchPlaceholder="Buscar por patente, material, cliente..."
              defaultPageSize={10}
            />
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardHeader className="px-3 sm:px-6">
            <CardTitle className="text-lg sm:text-xl">Lista de Remitos</CardTitle>
          </CardHeader>
          <CardContent className="px-3 sm:px-6">
            <DataTable
              columns={remitosColumns}
              data={remitos}
              searchPlaceholder="Buscar por número de remito, camión..."
              defaultPageSize={10}
            />
          </CardContent>
        </Card>
      )}
    </div>
  )
}
