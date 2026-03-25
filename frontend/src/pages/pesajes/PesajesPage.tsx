import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { ColumnDef } from '@tanstack/react-table'
import { Scale, Plus, Pencil, FileText, Printer, X, AlertTriangle, Ban, FileDown, RefreshCw } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { DataTable } from '@/components/ui/data-table'
import { pesajesService } from '@/services/pesajesService'
import { reportesService } from '@/services/reportesService'
import { Pesaje } from '@/types'
import { formatDate, formatNumber } from '@/lib/utils'
import { useIsAdmin } from '@/hooks/useIsAdmin'

type FiltroEstado = 'activos' | 'cancelados' | 'todos'

export default function PesajesPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const isAdmin = useIsAdmin()

  // Estado para filtro
  const [filtroEstado, setFiltroEstado] = useState<FiltroEstado>('activos')

  // Estado para modal de cancelación
  const [showCancelarModal, setShowCancelarModal] = useState(false)
  const [pesajeCancelar, setPesajeCancelar] = useState<Pesaje | null>(null)
  const [motivoCancelacion, setMotivoCancelacion] = useState('')
  const [errorMotivo, setErrorMotivo] = useState('')
  const [descargandoPDF, setDescargandoPDF] = useState(false)

  const { data: pesajes = [], isLoading } = useQuery({
    queryKey: ['pesajes', filtroEstado],
    queryFn: () => {
      if (filtroEstado === 'cancelados') {
        return pesajesService.getCancelados(0, 500)
      }
      // 'activos' o 'todos' van al endpoint normal
      return pesajesService.getAll(0, 500)
    },
  })

  // Filtrar en frontend si es 'activos' (excluir cancelados)
  const pesajesFiltrados = filtroEstado === 'activos'
    ? pesajes.filter(p => p.estado !== 'cancelado')
    : pesajes

  const cancelarMutation = useMutation({
    mutationFn: ({ id, motivo }: { id: string; motivo: string }) =>
      pesajesService.cancelarPesaje(id, motivo),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pesajes'] })
      cerrarModalCancelar()
    },
  })

  const sincronizarMutation = useMutation({
    mutationFn: (id: string) => pesajesService.sincronizarCuentaCorriente(id),
    onSuccess: (data) => {
      if (data.status === 'creado') {
        alert(`Sincronizado exitosamente. ${data.message}`)
      } else if (data.status === 'ya_existe') {
        alert(`El pesaje ya estaba en cuenta corriente. ${data.message}`)
      } else {
        alert(data.message || 'No se pudo sincronizar')
      }
    },
    onError: (error: any) => {
      alert(error.response?.data?.detail || 'Error al sincronizar')
    },
  })

  const abrirModalCancelar = (pesaje: Pesaje) => {
    setPesajeCancelar(pesaje)
    setMotivoCancelacion('')
    setErrorMotivo('')
    setShowCancelarModal(true)
  }

  const cerrarModalCancelar = () => {
    setShowCancelarModal(false)
    setPesajeCancelar(null)
    setMotivoCancelacion('')
    setErrorMotivo('')
  }

  const handleCancelar = async () => {
    if (!pesajeCancelar) return

    // Validar motivo
    if (motivoCancelacion.length < 10) {
      setErrorMotivo('El motivo debe tener al menos 10 caracteres')
      return
    }

    try {
      await cancelarMutation.mutateAsync({
        id: pesajeCancelar.id,
        motivo: motivoCancelacion,
      })
    } catch (error: any) {
      setErrorMotivo(error.response?.data?.detail || 'Error al cancelar pesaje')
    }
  }

  const handleDownloadPDF = async (id: string, numeroPesaje: number) => {
    try {
      await pesajesService.downloadTicketPDF(id, numeroPesaje)
    } catch (error) {
      alert('Error al descargar el ticket PDF')
    }
  }

  const handleDescargarListadoPDF = async () => {
    setDescargandoPDF(true)
    try {
      // Descargar listado de pesajes del día de hoy
      const hoy = new Date().toISOString().split('T')[0]
      await reportesService.exportarPDF('movimientos', hoy, hoy)
    } catch (error) {
      console.error('Error al descargar PDF:', error)
      alert('Error al descargar el PDF')
    } finally {
      setDescargandoPDF(false)
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
      accessorKey: 'estado',
      header: 'Estado',
      cell: ({ row }) => {
        const estado = row.getValue('estado') as string
        const pesaje = row.original
        if (estado === 'cancelado') {
          return (
            <div className="flex flex-col">
              <span className="inline-flex px-2 py-1 bg-red-100 text-red-700 text-xs font-semibold rounded">
                CANCELADO
              </span>
              {pesaje.motivo_cancelacion && (
                <span className="text-xs text-gray-500 mt-1 max-w-32 truncate" title={pesaje.motivo_cancelacion}>
                  {pesaje.motivo_cancelacion}
                </span>
              )}
            </div>
          )
        }
        if (estado === 'pendiente') {
          return (
            <span className="inline-flex px-2 py-1 bg-yellow-100 text-yellow-700 text-xs font-semibold rounded">
              Pendiente
            </span>
          )
        }
        return (
          <span className="inline-flex px-2 py-1 bg-green-100 text-green-700 text-xs font-semibold rounded">
            Completado
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
      accessorKey: 'patente',
      accessorFn: (row) => row.camion_patente || row.patente_externa || '',
      header: 'Camión',
      cell: ({ row }) => (
        <div className="font-medium">{row.getValue('patente') || '-'}</div>
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
      accessorKey: 'cliente_nombre',
      header: 'Cliente/Destino',
      cell: ({ row }) => (
        <div className="text-sm">{row.getValue('cliente_nombre') || '-'}</div>
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
        const estaCancelado = pesaje.estado === 'cancelado'

        return (
          <div className="flex items-center gap-2">
            {!estaCancelado && (
              <>
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
                  onClick={() => abrirModalCancelar(pesaje)}
                  disabled={cancelarMutation.isPending}
                  title="Cancelar pesaje"
                >
                  <Ban className="h-4 w-4 text-red-600" />
                </Button>
                {isAdmin && pesaje.estado === 'completado' && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => sincronizarMutation.mutate(pesaje.id)}
                    disabled={sincronizarMutation.isPending}
                    title="Sincronizar con cuenta corriente"
                  >
                    <RefreshCw className={`h-4 w-4 text-orange-600 ${sincronizarMutation.isPending ? 'animate-spin' : ''}`} />
                  </Button>
                )}
              </>
            )}
            {estaCancelado && (
              <span className="text-xs text-gray-400">Sin acciones</span>
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

  const totalToneladas = pesajesFiltrados.reduce((sum, p) => sum + (p.peso_neto || 0) / 1000, 0)

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
        <div className="flex gap-2 w-full sm:w-auto">
          <Button
            variant="outline"
            onClick={handleDescargarListadoPDF}
            disabled={descargandoPDF}
            title="Descargar listado de pesajes del día"
          >
            <FileDown className="h-4 w-4 mr-2" />
            {descargandoPDF ? 'Descargando...' : 'PDF del Día'}
          </Button>
          <Button onClick={() => navigate('/pesajes/nuevo')}>
            <Plus className="h-4 w-4 mr-2" />
            Nuevo Pesaje
          </Button>
        </div>
      </div>

      {/* Filtro de estado */}
      <Card>
        <CardContent className="py-3">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-sm font-medium text-gray-600">Mostrar:</span>
            <Button
              variant={filtroEstado === 'activos' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setFiltroEstado('activos')}
            >
              Activos (Completados + Pendientes)
            </Button>
            <Button
              variant={filtroEstado === 'cancelados' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setFiltroEstado('cancelados')}
              className={filtroEstado === 'cancelados' ? 'bg-red-600 hover:bg-red-700' : ''}
            >
              <Ban className="h-4 w-4 mr-1" />
              Cancelados (Auditoría)
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Estadísticas rápidas */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 sm:gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Total Pesajes</div>
            <div className="text-2xl font-bold">{pesajesFiltrados.length}</div>
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
              {pesajesFiltrados.length > 0 ? formatNumber(totalToneladas / pesajesFiltrados.length, 2) : 0} t
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader className="px-3 sm:px-6">
          <CardTitle className="text-lg sm:text-xl">
            {filtroEstado === 'cancelados' ? 'Pesajes Cancelados (Auditoría)' : 'Lista de Pesajes'}
          </CardTitle>
        </CardHeader>
        <CardContent className="px-3 sm:px-6">
          <DataTable
            columns={columns}
            data={pesajesFiltrados}
            searchPlaceholder="Buscar por patente, material, cliente..."
            defaultPageSize={10}
          />
        </CardContent>
      </Card>

      {/* Modal de cancelación */}
      {showCancelarModal && pesajeCancelar && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <Card className="w-full max-w-md">
            <CardHeader className="flex flex-row items-center justify-between">
              <div className="flex items-center gap-2">
                <AlertTriangle className="h-5 w-5 text-red-600" />
                <CardTitle>Cancelar Pesaje #{pesajeCancelar.numero_pesaje}</CardTitle>
              </div>
              <Button variant="ghost" size="sm" onClick={cerrarModalCancelar}>
                <X className="h-4 w-4" />
              </Button>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="bg-yellow-50 border border-yellow-200 rounded-md p-3 text-sm text-yellow-800">
                <p className="font-medium">Esta acción quedará registrada</p>
                <p className="mt-1">El pesaje NO se eliminará, se marcará como cancelado con su motivo. Quedará visible en la auditoría.</p>
              </div>

              <div>
                <p className="text-sm text-gray-600 mb-2">
                  <strong>Patente:</strong> {pesajeCancelar.camion_patente || pesajeCancelar.patente_externa || '-'}
                </p>
                <p className="text-sm text-gray-600 mb-2">
                  <strong>Cliente:</strong> {pesajeCancelar.cliente_nombre || '-'}
                </p>
                <p className="text-sm text-gray-600">
                  <strong>Tara:</strong> {formatNumber(pesajeCancelar.peso_tara || 0)} kg
                </p>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">
                  Motivo de cancelación <span className="text-red-500">*</span>
                </label>
                <textarea
                  value={motivoCancelacion}
                  onChange={(e) => {
                    setMotivoCancelacion(e.target.value)
                    setErrorMotivo('')
                  }}
                  placeholder="Explique por qué se cancela este pesaje (mínimo 10 caracteres)..."
                  className="w-full h-24 px-3 py-2 border rounded-md text-sm"
                />
                <p className="text-xs text-gray-500">
                  {motivoCancelacion.length}/10 caracteres mínimo
                </p>
                {errorMotivo && (
                  <p className="text-sm text-red-600">{errorMotivo}</p>
                )}
              </div>

              <div className="flex gap-2 justify-end pt-4 border-t">
                <Button variant="outline" onClick={cerrarModalCancelar}>
                  Volver
                </Button>
                <Button
                  variant="destructive"
                  onClick={handleCancelar}
                  disabled={cancelarMutation.isPending || motivoCancelacion.length < 10}
                >
                  {cancelarMutation.isPending ? 'Cancelando...' : 'Confirmar Cancelación'}
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}
