import { useState, useMemo } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { ColumnDef } from '@tanstack/react-table'
import { Plus, Pencil, Trash2, Download, DollarSign, Scale, Clock, Filter, X, FileDown } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { DataTable } from '@/components/ui/data-table'
import { pesajesService } from '@/services/pesajesService'
import { reportesService } from '@/services/reportesService'
import { Pesaje } from '@/types'
import { formatDate, formatNumber } from '@/lib/utils'
import { useIsAdmin } from '@/hooks/useIsAdmin'

// Lista de materiales disponibles
const MATERIALES_DISPONIBLES = [
  '10.30',
  '6.19',
  '0.20',
  '6.12',
  'relleno',
  'binder',
  '0.6',
  'piedra partida',
  'suelo arena',
  'retiro',
]

export default function PesajesTab() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const isAdmin = useIsAdmin()

  // Estados para filtros
  const [filtroEstado, setFiltroEstado] = useState<string>('')
  const [filtroFechaDesde, setFiltroFechaDesde] = useState<string>('')
  const [filtroFechaHasta, setFiltroFechaHasta] = useState<string>('')
  const [filtroPatente, setFiltroPatente] = useState<string>('')
  const [filtroMaterial, setFiltroMaterial] = useState<string>('')
  const [filtroCliente, setFiltroCliente] = useState<string>('')
  const [mostrarFiltros, setMostrarFiltros] = useState<boolean>(false)
  const [descargandoPDF, setDescargandoPDF] = useState<boolean>(false)

  // Query para pesajes
  const { data: pesajesRaw = [], isLoading } = useQuery({
    queryKey: ['pesajes'],
    queryFn: () => pesajesService.getAll(0, 500),
  })

  // Filtrar pesajes según los filtros activos
  const pesajes = useMemo(() => {
    return pesajesRaw.filter((pesaje) => {
      // Filtro por estado
      if (filtroEstado && pesaje.estado !== filtroEstado) {
        return false
      }

      // Filtro por fecha desde
      if (filtroFechaDesde) {
        // Extraer solo la parte de fecha del pesaje (YYYY-MM-DD)
        const fechaPesajeStr = pesaje.fecha.split('T')[0]
        if (fechaPesajeStr < filtroFechaDesde) {
          return false
        }
      }

      // Filtro por fecha hasta
      if (filtroFechaHasta) {
        const fechaPesajeStr = pesaje.fecha.split('T')[0]
        if (fechaPesajeStr > filtroFechaHasta) {
          return false
        }
      }

      // Filtro por patente
      if (filtroPatente) {
        const patente = (pesaje.camion_patente || pesaje.patente_externa || '').toLowerCase()
        if (!patente.includes(filtroPatente.toLowerCase())) {
          return false
        }
      }

      // Filtro por material
      if (filtroMaterial && pesaje.material !== filtroMaterial) {
        return false
      }

      // Filtro por cliente
      if (filtroCliente) {
        const cliente = (pesaje.cliente_nombre || '').toLowerCase()
        if (!cliente.includes(filtroCliente.toLowerCase())) {
          return false
        }
      }

      return true
    })
  }, [pesajesRaw, filtroEstado, filtroFechaDesde, filtroFechaHasta, filtroPatente, filtroMaterial, filtroCliente])

  // Verificar si hay filtros activos
  const hayFiltrosActivos = filtroEstado || filtroFechaDesde || filtroFechaHasta || filtroPatente || filtroMaterial || filtroCliente

  // Limpiar todos los filtros
  const limpiarFiltros = () => {
    setFiltroEstado('')
    setFiltroFechaDesde('')
    setFiltroFechaHasta('')
    setFiltroPatente('')
    setFiltroMaterial('')
    setFiltroCliente('')
  }

  // Descargar PDF de pesajes
  const handleDescargarPDF = async () => {
    setDescargandoPDF(true)
    try {
      // Usar fechas de filtro o por defecto hoy
      const hoy = new Date().toISOString().split('T')[0]
      const fechaDesde = filtroFechaDesde || hoy
      const fechaHasta = filtroFechaHasta || hoy

      await reportesService.exportarPDF('movimientos', fechaDesde, fechaHasta)
    } catch (error) {
      console.error('Error al descargar PDF:', error)
      alert('Error al descargar el PDF')
    } finally {
      setDescargandoPDF(false)
    }
  }

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
      accessorKey: 'patente',
      accessorFn: (row) => row.camion_patente || row.patente_externa || '',
      header: 'Patente',
      cell: ({ row }) => {
        const patente = row.getValue('patente') as string
        return <div className="font-medium">{patente || '-'}</div>
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
      accessorKey: 'cliente_nombre',
      header: 'Cliente',
      cell: ({ row }) => {
        const cliente = row.getValue('cliente_nombre') as string
        return <div className="text-sm">{cliente || '-'}</div>
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
  const totalIngresos = pesajes.reduce((sum, p) => sum + (Number(p.importe_total) || 0), 0)

  // Obtener el número de pesaje más alto como indicador del total real de pesajes
  const ultimoNumeroPesaje = pesajesRaw.reduce((max, p) => Math.max(max, p.numero_pesaje || 0), 0)

  return (
    <div className="space-y-6">
      {/* Header con botones */}
      <div className="flex flex-col sm:flex-row justify-between gap-3">
        <div className="flex gap-2 flex-wrap">
          <Button
            variant="outline"
            onClick={() => setMostrarFiltros(!mostrarFiltros)}
            className={hayFiltrosActivos ? 'border-blue-500 text-blue-600' : ''}
          >
            <Filter className="h-4 w-4 mr-2" />
            Filtros
            {hayFiltrosActivos && (
              <span className="ml-2 bg-blue-500 text-white text-xs px-1.5 py-0.5 rounded-full">
                {[filtroEstado, filtroFechaDesde, filtroFechaHasta, filtroPatente, filtroMaterial, filtroCliente].filter(Boolean).length}
              </span>
            )}
          </Button>
          <Button
            variant="outline"
            onClick={handleDescargarPDF}
            disabled={descargandoPDF}
            title="Descargar listado de pesajes en PDF"
          >
            <FileDown className="h-4 w-4 mr-2" />
            {descargandoPDF ? 'Descargando...' : 'Descargar PDF'}
          </Button>
        </div>
        <Button onClick={() => navigate('/pesajes-remitos/nuevo')}>
          <Plus className="h-4 w-4 mr-2" />
          Nuevo Pesaje
        </Button>
      </div>

      {/* Panel de Filtros */}
      {mostrarFiltros && (
        <Card className="border-blue-200 bg-blue-50/50">
          <CardContent className="pt-4">
            <div className="flex flex-col gap-4">
              <div className="flex items-center justify-between">
                <h3 className="font-semibold text-sm text-gray-700">Filtrar pesajes</h3>
                {hayFiltrosActivos && (
                  <Button variant="ghost" size="sm" onClick={limpiarFiltros} className="text-red-600 hover:text-red-700">
                    <X className="h-4 w-4 mr-1" />
                    Limpiar filtros
                  </Button>
                )}
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-3">
                {/* Filtro Estado */}
                <div className="space-y-1">
                  <label className="text-xs font-medium text-gray-600">Estado</label>
                  <select
                    value={filtroEstado}
                    onChange={(e) => setFiltroEstado(e.target.value)}
                    className="w-full h-9 rounded-md border border-input bg-background px-3 py-1 text-sm"
                  >
                    <option value="">Todos</option>
                    <option value="completado">Completado</option>
                    <option value="pendiente">Pendiente</option>
                  </select>
                </div>

                {/* Filtro Fecha Desde */}
                <div className="space-y-1">
                  <label className="text-xs font-medium text-gray-600">Fecha desde</label>
                  <Input
                    type="date"
                    value={filtroFechaDesde}
                    onChange={(e) => setFiltroFechaDesde(e.target.value)}
                    className="h-9"
                  />
                </div>

                {/* Filtro Fecha Hasta */}
                <div className="space-y-1">
                  <label className="text-xs font-medium text-gray-600">Fecha hasta</label>
                  <Input
                    type="date"
                    value={filtroFechaHasta}
                    onChange={(e) => setFiltroFechaHasta(e.target.value)}
                    className="h-9"
                  />
                </div>

                {/* Filtro Patente */}
                <div className="space-y-1">
                  <label className="text-xs font-medium text-gray-600">Patente</label>
                  <Input
                    placeholder="Buscar patente..."
                    value={filtroPatente}
                    onChange={(e) => setFiltroPatente(e.target.value)}
                    className="h-9"
                  />
                </div>

                {/* Filtro Material */}
                <div className="space-y-1">
                  <label className="text-xs font-medium text-gray-600">Material</label>
                  <select
                    value={filtroMaterial}
                    onChange={(e) => setFiltroMaterial(e.target.value)}
                    className="w-full h-9 rounded-md border border-input bg-background px-3 py-1 text-sm"
                  >
                    <option value="">Todos</option>
                    {MATERIALES_DISPONIBLES.map((m) => (
                      <option key={m} value={m}>{m}</option>
                    ))}
                  </select>
                </div>

                {/* Filtro Cliente */}
                <div className="space-y-1">
                  <label className="text-xs font-medium text-gray-600">Cliente</label>
                  <Input
                    placeholder="Buscar cliente..."
                    value={filtroCliente}
                    onChange={(e) => setFiltroCliente(e.target.value)}
                    className="h-9"
                  />
                </div>
              </div>

              {hayFiltrosActivos && (
                <div className="text-sm text-blue-600">
                  Mostrando {pesajes.length} de {pesajesRaw.length} pesajes
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Estadísticas */}
      <div className={`grid grid-cols-1 gap-3 sm:gap-4 ${isAdmin ? 'sm:grid-cols-4' : 'sm:grid-cols-3'}`}>
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Total Pesajes</div>
            <div className="text-2xl font-bold">{ultimoNumeroPesaje}</div>
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
        {/* Solo visible para administradores */}
        {isAdmin && (
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
        )}
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
