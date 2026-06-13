import { useState, useMemo } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { ColumnDef } from '@tanstack/react-table'
import { Plus, Pencil, Trash2, Download, Scale, Clock, Filter, X, FileDown, MoreVertical, History, UserCog } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { DataTable } from '@/components/ui/data-table'
import { pesajesService } from '@/services/pesajesService'
import { empresasService } from '@/services/empresasService'
import { reportesService } from '@/services/reportesService'
import { Pesaje, Empresa } from '@/types'
import { formatDate, formatNumber } from '@/lib/utils'

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

// Tipo para historial
interface HistorialItem {
  id: string
  fecha: string
  usuario_nombre: string
  accion: string
}

export default function PesajesTab() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  // Estados para filtros
  const [filtroEstado, setFiltroEstado] = useState<string>('')
  const [filtroFechaDesde, setFiltroFechaDesde] = useState<string>('')
  const [filtroFechaHasta, setFiltroFechaHasta] = useState<string>('')
  const [filtroPatente, setFiltroPatente] = useState<string>('')
  const [filtroMaterial, setFiltroMaterial] = useState<string>('')
  const [filtroCliente, setFiltroCliente] = useState<string>('')
  const [filtroNumeroTicket, setFiltroNumeroTicket] = useState<string>('')
  const [mostrarFiltros, setMostrarFiltros] = useState<boolean>(false)
  const [descargandoPDF, setDescargandoPDF] = useState<boolean>(false)

  // Estados para historial
  const [showHistorialModal, setShowHistorialModal] = useState(false)
  const [historialPesaje, setHistorialPesaje] = useState<{ id: string; numero: number } | null>(null)
  const [historial, setHistorial] = useState<HistorialItem[]>([])
  const [cargandoHistorial, setCargandoHistorial] = useState(false)

  // Estado para cambiar cliente
  const [showCambiarClienteModal, setShowCambiarClienteModal] = useState(false)
  const [pesajeACambiar, setPesajeACambiar] = useState<Pesaje | null>(null)

  // Query para pesajes - incluir cancelados si el filtro está activo
  const { data: pesajesRaw = [], isLoading } = useQuery({
    queryKey: ['pesajes', filtroEstado],
    queryFn: () => pesajesService.getAll(0, 500, filtroEstado === 'cancelado'),
  })

  // Filtrar pesajes según los filtros activos
  const pesajes = useMemo(() => {
    return pesajesRaw.filter((pesaje) => {
      // Filtro por número de ticket (prioridad alta - si se busca por número, ignorar otros filtros de fecha)
      if (filtroNumeroTicket) {
        const numeroStr = pesaje.numero_pesaje?.toString() || ''
        if (!numeroStr.includes(filtroNumeroTicket)) {
          return false
        }
        // Si hay filtro de número de ticket, no aplicar filtros de fecha
        // para poder encontrar tickets viejos
      } else {
        // Solo aplicar filtros de fecha si NO hay búsqueda por número de ticket

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
      }

      // Filtro por estado
      if (filtroEstado && pesaje.estado !== filtroEstado) {
        return false
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
  }, [pesajesRaw, filtroEstado, filtroFechaDesde, filtroFechaHasta, filtroPatente, filtroMaterial, filtroCliente, filtroNumeroTicket])

  // Verificar si hay filtros activos
  const hayFiltrosActivos = filtroEstado || filtroFechaDesde || filtroFechaHasta || filtroPatente || filtroMaterial || filtroCliente || filtroNumeroTicket

  // Limpiar todos los filtros
  const limpiarFiltros = () => {
    setFiltroEstado('')
    setFiltroFechaDesde('')
    setFiltroFechaHasta('')
    setFiltroPatente('')
    setFiltroMaterial('')
    setFiltroCliente('')
    setFiltroNumeroTicket('')
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

  // Descargar Excel real (.xlsx) de movimientos
  const [descargandoExcel, setDescargandoExcel] = useState(false)
  const handleDescargarExcel = async () => {
    setDescargandoExcel(true)
    try {
      const hoy = new Date().toISOString().split('T')[0]
      const fechaDesde = filtroFechaDesde || hoy
      const fechaHasta = filtroFechaHasta || hoy
      await reportesService.exportarMovimientosXLSX(fechaDesde, fechaHasta)
    } catch (error) {
      console.error('Error al descargar Excel:', error)
      alert('Error al descargar el Excel')
    } finally {
      setDescargandoExcel(false)
    }
  }

  // Descargar CSV (legacy)
  const [descargandoCSV, setDescargandoCSV] = useState(false)
  const handleDescargarCSV = async () => {
    setDescargandoCSV(true)
    try {
      const hoy = new Date().toISOString().split('T')[0]
      const fechaDesde = filtroFechaDesde || hoy
      const fechaHasta = filtroFechaHasta || hoy
      await reportesService.exportarMovimientosExcel(fechaDesde, fechaHasta)
    } catch (error) {
      console.error('Error al descargar CSV:', error)
      alert('Error al descargar el CSV')
    } finally {
      setDescargandoCSV(false)
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

  const handleVerHistorial = async (id: string, numero: number) => {
    setHistorialPesaje({ id, numero })
    setCargandoHistorial(true)
    setShowHistorialModal(true)
    try {
      const data = await pesajesService.getHistorial(id)
      setHistorial(data)
    } catch (error) {
      console.error('Error al cargar historial:', error)
      setHistorial([])
    } finally {
      setCargandoHistorial(false)
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
        const estilos = {
          pendiente: 'bg-yellow-100 text-yellow-700',
          completado: 'bg-green-100 text-green-700',
          cancelado: 'bg-red-100 text-red-700',
        }
        const etiquetas = {
          pendiente: 'Pendiente',
          completado: 'Completado',
          cancelado: 'Cancelado',
        }
        return (
          <span className={`inline-flex items-center gap-1 px-2 py-1 text-xs font-semibold rounded ${
            estilos[estado as keyof typeof estilos] || 'bg-gray-100 text-gray-700'
          }`}>
            {estado === 'pendiente' ? <Clock className="h-3 w-3" /> : null}
            {etiquetas[estado as keyof typeof etiquetas] || estado}
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
        const [menuAbierto, setMenuAbierto] = useState(false)

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

            <Button
              variant="outline"
              size="sm"
              onClick={() => handleDelete(pesaje.id, pesaje.numero_pesaje)}
              disabled={deleteMutation.isPending}
              title="Eliminar"
            >
              <Trash2 className="h-4 w-4 text-red-600" />
            </Button>

            {/* Menú de tres puntitos */}
            <div className="relative">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setMenuAbierto(!menuAbierto)}
                title="Más opciones"
              >
                <MoreVertical className="h-4 w-4" />
              </Button>
              {menuAbierto && (
                <>
                  <div
                    className="fixed inset-0 z-10"
                    onClick={() => setMenuAbierto(false)}
                  />
                  <div className="absolute right-0 mt-1 w-44 bg-white border rounded-md shadow-lg z-20">
                    <button
                      className="flex items-center gap-2 w-full px-3 py-2 text-sm text-left hover:bg-gray-100"
                      onClick={() => {
                        setMenuAbierto(false)
                        handleVerHistorial(pesaje.id, pesaje.numero_pesaje)
                      }}
                    >
                      <History className="h-4 w-4 text-blue-600" />
                      Historial
                    </button>
                    <button
                      className="flex items-center gap-2 w-full px-3 py-2 text-sm text-left hover:bg-gray-100"
                      onClick={() => {
                        setMenuAbierto(false)
                        setPesajeACambiar(pesaje)
                        setShowCambiarClienteModal(true)
                      }}
                    >
                      <UserCog className="h-4 w-4 text-purple-600" />
                      Cambiar cliente
                    </button>
                  </div>
                </>
              )}
            </div>
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

  const totalToneladas = pesajes.reduce((sum, p) => sum + (Number(p.peso_neto) || 0) / 1000, 0)
  const promedioToneladas = pesajes.length > 0 ? totalToneladas / pesajes.length : 0
  // Cantidad de pesajes según los filtros activos.
  const cantidadFiltrada = pesajes.length

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
                {[filtroNumeroTicket, filtroEstado, filtroFechaDesde, filtroFechaHasta, filtroPatente, filtroMaterial, filtroCliente].filter(Boolean).length}
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
          <Button
            variant="outline"
            onClick={handleDescargarExcel}
            disabled={descargandoExcel}
            title="Descargar listado de pesajes en Excel (.xlsx)"
          >
            <FileDown className="h-4 w-4 mr-2" />
            {descargandoExcel ? 'Descargando...' : 'Descargar Excel'}
          </Button>
          <Button
            variant="outline"
            onClick={handleDescargarCSV}
            disabled={descargandoCSV}
            title="Descargar listado de pesajes en CSV (texto plano)"
          >
            <FileDown className="h-4 w-4 mr-2" />
            {descargandoCSV ? 'Descargando...' : 'Descargar CSV'}
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

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-7 gap-3">
                {/* Filtro Número de Ticket */}
                <div className="space-y-1">
                  <label className="text-xs font-medium text-gray-600">N° Ticket</label>
                  <Input
                    type="text"
                    placeholder="Ej: 481"
                    value={filtroNumeroTicket}
                    onChange={(e) => setFiltroNumeroTicket(e.target.value)}
                    className="h-9"
                  />
                </div>

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
                    <option value="cancelado">Cancelado</option>
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
      <div className="grid grid-cols-1 gap-3 sm:gap-4 sm:grid-cols-3">
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">
              {hayFiltrosActivos ? 'Pesajes filtrados' : 'Total Pesajes'}
            </div>
            <div className="text-2xl font-bold">{cantidadFiltrada}</div>
            {hayFiltrosActivos && (
              <div className="text-xs text-gray-500 mt-1">
                de {pesajesRaw.length} cargados
              </div>
            )}
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

      {/* Modal de Historial */}
      {showHistorialModal && historialPesaje && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <Card className="w-full max-w-md">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-2">
                  <History className="h-5 w-5 text-blue-600" />
                  Historial Pesaje #{historialPesaje.numero}
                </CardTitle>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    setShowHistorialModal(false)
                    setHistorialPesaje(null)
                    setHistorial([])
                  }}
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {cargandoHistorial ? (
                <div className="py-8 text-center text-gray-500">
                  Cargando historial...
                </div>
              ) : historial.length === 0 ? (
                <div className="py-8 text-center text-gray-500">
                  No hay registros de historial
                </div>
              ) : (
                <div className="space-y-2">
                  {historial.map((item) => {
                    const fecha = new Date(item.fecha)
                    const fechaStr = fecha.toLocaleDateString('es-AR', { day: '2-digit', month: '2-digit' })
                    const horaStr = fecha.toLocaleTimeString('es-AR', { hour: '2-digit', minute: '2-digit' })

                    return (
                      <div
                        key={item.id}
                        className="flex items-center justify-between py-2 px-3 bg-gray-50 rounded-lg"
                      >
                        <div className="flex items-center gap-3">
                          <span className="text-sm text-gray-600">
                            {fechaStr} - {horaStr}
                          </span>
                          <span className="font-medium text-sm">
                            {item.usuario_nombre.toUpperCase()}
                          </span>
                        </div>
                        <span className={`text-xs font-semibold px-2 py-1 rounded ${
                          item.accion === 'CREACION' ? 'bg-green-100 text-green-700' :
                          item.accion === 'COMPLETADO' ? 'bg-blue-100 text-blue-700' :
                          item.accion === 'MODIFICACION' ? 'bg-yellow-100 text-yellow-700' :
                          item.accion === 'CANCELACION' ? 'bg-red-100 text-red-700' :
                          item.accion === 'ELIMINACION' ? 'bg-red-100 text-red-700' :
                          'bg-gray-100 text-gray-700'
                        }`}>
                          {item.accion}
                        </span>
                      </div>
                    )
                  })}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* Modal Cambiar Cliente */}
      {showCambiarClienteModal && pesajeACambiar && (
        <CambiarClienteModal
          pesaje={pesajeACambiar}
          onClose={() => {
            setShowCambiarClienteModal(false)
            setPesajeACambiar(null)
          }}
          onSuccess={() => {
            setShowCambiarClienteModal(false)
            setPesajeACambiar(null)
            queryClient.invalidateQueries({ queryKey: ['pesajes'] })
            queryClient.invalidateQueries({ queryKey: ['cuenta-corriente-resumen'] })
            queryClient.invalidateQueries({ queryKey: ['cuenta-corriente-movimientos'] })
            queryClient.invalidateQueries({ queryKey: ['clientes-con-deuda'] })
          }}
        />
      )}
    </div>
  )
}

// Modal para cambiar el cliente de un pesaje
function CambiarClienteModal({
  pesaje,
  onClose,
  onSuccess,
}: {
  pesaje: Pesaje
  onClose: () => void
  onSuccess: () => void
}) {
  const [busqueda, setBusqueda] = useState('')
  const [clienteIdSeleccionado, setClienteIdSeleccionado] = useState<string>(pesaje.cliente_id || '')

  const { data: clientes = [], isLoading } = useQuery<Empresa[]>({
    queryKey: ['empresas-clientes'],
    queryFn: () => empresasService.getClientes(),
  })

  const clientesFiltrados = useMemo(() => {
    const q = busqueda.toLowerCase().trim()
    if (!q) return clientes
    return clientes.filter(c =>
      c.nombre.toLowerCase().includes(q) ||
      (c.cuit && c.cuit.includes(q))
    )
  }, [clientes, busqueda])

  const mutation = useMutation({
    mutationFn: () => pesajesService.cambiarCliente(pesaje.id, clienteIdSeleccionado),
    onSuccess,
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!clienteIdSeleccionado) {
      alert('Seleccione un cliente')
      return
    }
    if (clienteIdSeleccionado === pesaje.cliente_id) {
      alert('El cliente seleccionado es el mismo que el actual')
      return
    }
    mutation.mutate()
  }

  const importeTotal = pesaje.importe_total ?? 0
  const tieneImporte = importeTotal > 0
  const teniaCliente = !!pesaje.cliente_id

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <Card className="w-full max-w-lg">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <UserCog className="h-5 w-5 text-purple-600" />
              Cambiar Cliente — Pesaje #{pesaje.numero_pesaje}
            </CardTitle>
            <Button variant="ghost" size="sm" onClick={onClose}>
              <X className="h-4 w-4" />
            </Button>
          </div>
          <p className="text-sm text-gray-500 mt-1">
            Cliente actual: <strong>{pesaje.cliente_nombre || 'Sin cliente'}</strong>
          </p>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="bg-blue-50 border border-blue-200 p-3 rounded-lg text-xs text-blue-800 space-y-1">
              <p>
                {teniaCliente
                  ? '🔁 El cargo en cuenta corriente del cliente actual se transferirá al cliente nuevo.'
                  : '➕ Como el pesaje no tiene cliente asignado, se creará un nuevo movimiento en la cuenta corriente del cliente seleccionado.'}
              </p>
              {!tieneImporte && (
                <p>
                  Como el pesaje no tiene importe, se creará un cargo de <strong>$0</strong>. Después podés editarlo desde Cuenta Corriente.
                </p>
              )}
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Buscar cliente</label>
              <Input
                placeholder="Nombre o CUIT..."
                value={busqueda}
                onChange={(e) => setBusqueda(e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Seleccionar cliente *</label>
              <div className="border rounded-md max-h-60 overflow-y-auto">
                {isLoading ? (
                  <div className="p-3 text-sm text-gray-500">Cargando...</div>
                ) : clientesFiltrados.length === 0 ? (
                  <div className="p-3 text-sm text-gray-500">Sin resultados</div>
                ) : (
                  clientesFiltrados.map((cliente) => (
                    <button
                      key={cliente.id}
                      type="button"
                      onClick={() => setClienteIdSeleccionado(cliente.id)}
                      className={`w-full px-3 py-2 text-left text-sm border-b last:border-b-0 transition ${
                        clienteIdSeleccionado === cliente.id
                          ? 'bg-purple-100 border-purple-300'
                          : 'hover:bg-gray-50'
                      }`}
                    >
                      <div className="font-medium">{cliente.nombre}</div>
                      <div className="text-xs text-gray-500">
                        {cliente.cuit ? `CUIT: ${cliente.cuit}` : 'Sin CUIT'}
                        {cliente.id === pesaje.cliente_id && ' · (cliente actual)'}
                      </div>
                    </button>
                  ))
                )}
              </div>
            </div>

            <div className="flex gap-2 pt-2">
              <Button
                type="submit"
                disabled={mutation.isPending || !clienteIdSeleccionado || clienteIdSeleccionado === pesaje.cliente_id}
                className="flex-1 bg-purple-600 hover:bg-purple-700"
              >
                {mutation.isPending ? 'Aplicando...' : 'Aplicar cambio'}
              </Button>
              <Button type="button" variant="outline" onClick={onClose}>
                Cancelar
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
