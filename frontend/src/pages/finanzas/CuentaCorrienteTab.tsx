import { useState, useMemo } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Users, Plus, CreditCard, FileText, Download,
  TrendingUp, TrendingDown,
  X, Search, Pencil, DollarSign, Trash2, MoreVertical, History, RefreshCw
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Pagination } from '@/components/ui/pagination'
import { cuentaCorrienteService, type HistorialMovimientoItem } from '@/services/cuentaCorrienteService'
import { empresasService } from '@/services/empresasService'
import { facturacionService } from '@/services/facturacionService'
import { formatDate, formatNumber, getTodayLocalDate } from '@/lib/utils'
import { useIsAdmin } from '@/hooks/useIsAdmin'
import NuevoCobroModal from '@/components/cobros/NuevoCobroModal'

export default function CuentaCorrienteTab() {
  const queryClient = useQueryClient()
  const isAdmin = useIsAdmin()
  const [selectedCliente, setSelectedCliente] = useState<string | null>(null)
  const [showPagoModal, setShowPagoModal] = useState(false)
  const [showAjusteModal, setShowAjusteModal] = useState(false)
  const [showEditarMontoModal, setShowEditarMontoModal] = useState(false)
  const [showNuevoCobroModal, setShowNuevoCobroModal] = useState(false)
  const [showAnularModal, setShowAnularModal] = useState(false)
  const [showHistorialModal, setShowHistorialModal] = useState(false)
  const [movimientoAEditar, setMovimientoAEditar] = useState<any>(null)
  const [movimientoAAnular, setMovimientoAAnular] = useState<any>(null)
  const [historialMovimiento, setHistorialMovimiento] = useState<any>(null)
  const [historial, setHistorial] = useState<HistorialMovimientoItem[]>([])
  const [cargandoHistorial, setCargandoHistorial] = useState(false)
  const [menuAbiertoId, setMenuAbiertoId] = useState<string | null>(null)
  const [descargandoComprobante, setDescargandoComprobante] = useState<string | null>(null)
  const [busqueda, setBusqueda] = useState('')
  const [recalculando, setRecalculando] = useState(false)

  // Paginación de clientes
  const [clientesPage, setClientesPage] = useState(1)
  const [clientesPageSize, setClientesPageSize] = useState(10)

  // Paginación de movimientos
  const [movimientosPage, setMovimientosPage] = useState(1)
  const [movimientosPageSize, setMovimientosPageSize] = useState(10)

  // Queries
  const { data: clientesConDeuda = [] } = useQuery({
    queryKey: ['clientes-con-deuda'],
    queryFn: () => cuentaCorrienteService.getClientesConDeuda(),
  })

  const { data: todosClientes = [] } = useQuery({
    queryKey: ['empresas-clientes'],
    queryFn: () => empresasService.getClientes(),
  })

  const { data: resumen } = useQuery({
    queryKey: ['cuenta-corriente-resumen', selectedCliente],
    queryFn: () => cuentaCorrienteService.getResumenCliente(selectedCliente!),
    enabled: !!selectedCliente,
  })

  const { data: movimientos = [] } = useQuery({
    queryKey: ['cuenta-corriente-movimientos', selectedCliente],
    queryFn: () => cuentaCorrienteService.getMovimientosCliente(selectedCliente!),
    enabled: !!selectedCliente,
  })

  // Calcular totales
  const totalDeuda = clientesConDeuda.reduce((sum, c) => sum + c.saldo, 0)

  // Filtrar clientes
  const clientesFiltrados = useMemo(() => {
    return todosClientes.filter(c =>
      c.nombre.toLowerCase().includes(busqueda.toLowerCase()) ||
      (c.cuit && c.cuit.includes(busqueda))
    )
  }, [todosClientes, busqueda])

  // Paginar clientes
  const clientesTotalPages = Math.ceil(clientesFiltrados.length / clientesPageSize)
  const clientesPaginados = useMemo(() => {
    const start = (clientesPage - 1) * clientesPageSize
    return clientesFiltrados.slice(start, start + clientesPageSize)
  }, [clientesFiltrados, clientesPage, clientesPageSize])

  // Paginar movimientos
  const movimientosTotalPages = Math.ceil(movimientos.length / movimientosPageSize)
  const movimientosPaginados = useMemo(() => {
    const start = (movimientosPage - 1) * movimientosPageSize
    return movimientos.slice(start, start + movimientosPageSize)
  }, [movimientos, movimientosPage, movimientosPageSize])

  // Reset página cuando cambia búsqueda
  const handleBusquedaChange = (value: string) => {
    setBusqueda(value)
    setClientesPage(1)
  }

  // Reset página movimientos cuando cambia cliente
  const handleSelectCliente = (id: string) => {
    setSelectedCliente(id)
    setMovimientosPage(1)
  }

  // Descargar PDF estado de cuenta
  const handleDescargarPDF = async () => {
    if (!selectedCliente) return
    try {
      const blob = await facturacionService.descargarEstadoCuentaPDF(selectedCliente)
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `estado_cuenta_${resumen?.empresa_nombre || 'cliente'}.pdf`
      a.click()
      window.URL.revokeObjectURL(url)
    } catch (error) {
      console.error('Error al descargar PDF:', error)
      alert('Error al descargar el PDF')
    }
  }

  // Descargar comprobante de un movimiento
  const handleDescargarComprobante = async (mov: any) => {
    setDescargandoComprobante(mov.id)
    try {
      const fechaStr = mov.fecha?.replace(/-/g, '') || 'sin_fecha'
      const filename = `comprobante_${mov.tipo}_${fechaStr}.pdf`
      await cuentaCorrienteService.descargarComprobantePDF(mov.id, filename)
    } catch (error) {
      console.error('Error al descargar comprobante:', error)
      alert('Error al descargar el comprobante')
    } finally {
      setDescargandoComprobante(null)
    }
  }

  // Recalcular saldos acumulados del cliente
  const handleRecalcularSaldos = async () => {
    if (!selectedCliente) return
    const ok = window.confirm(
      'Esto recorre todos los movimientos no anulados en orden cronológico y reescribe la columna SALDO. ¿Continuar?'
    )
    if (!ok) return
    setRecalculando(true)
    try {
      const res = await cuentaCorrienteService.recalcularSaldosCliente(selectedCliente)
      queryClient.invalidateQueries({ queryKey: ['cuenta-corriente-resumen'] })
      queryClient.invalidateQueries({ queryKey: ['cuenta-corriente-movimientos'] })
      queryClient.invalidateQueries({ queryKey: ['clientes-con-deuda'] })
      alert(
        `Saldos recalculados.\n` +
        `Movimientos procesados: ${res.movimientos_procesados}\n` +
        `Filas actualizadas: ${res.movimientos_actualizados}\n` +
        `Saldo: $${formatNumber(res.saldo_recalculado, 2)}`
      )
    } catch (error) {
      console.error('Error al recalcular saldos:', error)
      alert('Error al recalcular saldos')
    } finally {
      setRecalculando(false)
    }
  }

  // Ver historial de un movimiento
  const handleVerHistorial = async (mov: any) => {
    setHistorialMovimiento(mov)
    setShowHistorialModal(true)
    setCargandoHistorial(true)
    try {
      const data = await cuentaCorrienteService.getHistorialMovimiento(mov.id)
      setHistorial(data)
    } catch (error) {
      console.error('Error al cargar historial:', error)
      setHistorial([])
    } finally {
      setCargandoHistorial(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Cabecera con botón Nuevo Cobro */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <h2 className="text-xl font-semibold">Cuenta Corriente</h2>
        <Button onClick={() => setShowNuevoCobroModal(true)} className="bg-green-600 hover:bg-green-700">
          <DollarSign className="h-4 w-4 mr-2" />
          Nuevo Cobro
        </Button>
      </div>

      {/* Estadísticas */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Clientes con Deuda</div>
            <div className="text-2xl font-bold">{clientesConDeuda.length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Total a Cobrar</div>
            <div className="text-2xl font-bold text-red-600">
              ${formatNumber(totalDeuda, 2)}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Total Clientes</div>
            <div className="text-2xl font-bold">{todosClientes.length}</div>
          </CardContent>
        </Card>
      </div>

      {/* Selector de cliente con búsqueda */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <CardTitle className="text-lg">Seleccionar Cliente</CardTitle>
            <div className="relative flex-1 max-w-md">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <Input
                placeholder="Buscar por nombre o CUIT..."
                value={busqueda}
                onChange={(e) => handleBusquedaChange(e.target.value)}
                className="pl-10"
              />
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-2">
            {clientesPaginados.map((cliente) => {
              const deuda = clientesConDeuda.find(c => c.id === cliente.id)
              return (
                <button
                  key={cliente.id}
                  onClick={() => handleSelectCliente(cliente.id)}
                  className={`p-3 rounded-lg text-left transition-all ${
                    selectedCliente === cliente.id
                      ? 'bg-blue-100 border-2 border-blue-500 shadow-md'
                      : 'bg-gray-50 hover:bg-gray-100 border-2 border-transparent hover:border-gray-300'
                  }`}
                >
                  <p className="font-medium text-sm truncate">{cliente.nombre}</p>
                  {deuda && deuda.saldo > 0 ? (
                    <p className="text-xs font-bold text-red-600 mt-1">
                      ${formatNumber(deuda.saldo, 2)}
                    </p>
                  ) : (
                    <p className="text-xs text-green-600 mt-1">Sin deuda</p>
                  )}
                </button>
              )
            })}
          </div>
          {clientesFiltrados.length > 0 && (
            <Pagination
              currentPage={clientesPage}
              totalPages={clientesTotalPages}
              totalItems={clientesFiltrados.length}
              pageSize={clientesPageSize}
              onPageChange={setClientesPage}
              onPageSizeChange={(size) => {
                setClientesPageSize(size)
                setClientesPage(1)
              }}
            />
          )}
        </CardContent>
      </Card>

      {/* Detalle del cliente - Ancho completo */}
      {selectedCliente && (
        <Card>
          <CardHeader>
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <CardTitle className="text-xl">
                  {resumen ? resumen.empresa_nombre : 'Cargando...'}
                </CardTitle>
                {resumen && (
                  <p className="text-sm text-gray-500 mt-1">
                    CUIT: {todosClientes.find(c => c.id === selectedCliente)?.cuit || '-'}
                  </p>
                )}
              </div>
              <div className="flex flex-wrap gap-2">
                <Button size="sm" onClick={() => setShowPagoModal(true)}>
                  <Plus className="h-4 w-4 mr-1" />
                  Registrar Pago
                </Button>
                <Button size="sm" variant="outline" onClick={() => setShowAjusteModal(true)}>
                  <FileText className="h-4 w-4 mr-1" />
                  Ajuste
                </Button>
                {isAdmin && (
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={handleRecalcularSaldos}
                    disabled={recalculando}
                    title="Reconcilia la columna Saldo recorriendo los movimientos en orden cronológico"
                  >
                    <RefreshCw className={`h-4 w-4 mr-1 ${recalculando ? 'animate-spin' : ''}`} />
                    {recalculando ? 'Recalculando...' : 'Recalcular saldos'}
                  </Button>
                )}
                <Button size="sm" variant="outline" onClick={handleDescargarPDF}>
                  <Download className="h-4 w-4 mr-1" />
                  PDF
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              {/* Resumen */}
              {resumen && (
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  <div className="bg-red-50 p-4 rounded-lg">
                    <p className="text-xs text-red-600 font-medium">Total Cargos</p>
                    <p className="text-2xl font-bold text-red-700">
                      ${formatNumber(resumen.total_cargos, 2)}
                    </p>
                  </div>
                  <div className="bg-green-50 p-4 rounded-lg">
                    <p className="text-xs text-green-600 font-medium">Total Pagos</p>
                    <p className="text-2xl font-bold text-green-700">
                      ${formatNumber(resumen.total_pagos, 2)}
                    </p>
                  </div>
                  <div className={`p-4 rounded-lg ${resumen.saldo_actual > 0 ? 'bg-orange-50' : 'bg-blue-50'}`}>
                    <p className={`text-xs font-medium ${resumen.saldo_actual > 0 ? 'text-orange-600' : 'text-blue-600'}`}>
                      Saldo Actual
                    </p>
                    <p className={`text-2xl font-bold ${resumen.saldo_actual > 0 ? 'text-orange-700' : 'text-blue-700'}`}>
                      ${formatNumber(resumen.saldo_actual, 2)}
                    </p>
                  </div>
                </div>
              )}

              {/* Tabla de Movimientos - Ancho completo */}
              <div>
                <h4 className="font-medium mb-3">Movimientos</h4>
                <div className="border rounded-lg overflow-hidden">
                  <table className="w-full">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Fecha</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Tipo</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Descripción</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Método</th>
                        <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Debe</th>
                        <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Haber</th>
                        <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Saldo</th>
                        <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Acciones</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200">
                      {movimientos.length === 0 ? (
                        <tr>
                          <td colSpan={8} className="px-4 py-8 text-center text-gray-500">
                            No hay movimientos
                          </td>
                        </tr>
                      ) : (
                        movimientosPaginados.map((mov) => (
                          <tr key={mov.id} className={mov.anulado ? 'bg-gray-50 opacity-60' : 'hover:bg-gray-50'}>
                            <td className="px-4 py-3 text-sm">{formatDate(mov.fecha)}</td>
                            <td className="px-4 py-3">
                              <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                                mov.tipo === 'cargo' ? 'bg-red-100 text-red-700' :
                                mov.tipo === 'pago' ? 'bg-green-100 text-green-700' :
                                'bg-blue-100 text-blue-700'
                              }`}>
                                {mov.tipo.toUpperCase()}
                              </span>
                              {mov.anulado && (
                                <span className="ml-2 text-xs text-red-500">(ANULADO)</span>
                              )}
                              {mov.tipo === 'cargo' && mov.monto === 0 && !mov.anulado && (
                                <span className="ml-2 text-xs text-orange-500">(Sin precio)</span>
                              )}
                            </td>
                            <td className="px-4 py-3 text-sm">{mov.descripcion}</td>
                            <td className="px-4 py-3 text-sm text-gray-500">{mov.metodo_pago || '-'}</td>
                            <td className="px-4 py-3 text-sm text-right font-medium text-red-600">
                              {mov.tipo === 'cargo' ? `$${formatNumber(mov.monto, 2)}` : '-'}
                            </td>
                            <td className="px-4 py-3 text-sm text-right font-medium text-green-600">
                              {mov.tipo === 'pago' ? `$${formatNumber(mov.monto, 2)}` : '-'}
                            </td>
                            <td className="px-4 py-3 text-sm text-right font-bold">
                              ${formatNumber(mov.saldo_posterior, 2)}
                            </td>
                            <td className="px-4 py-3">
                              <div className="flex items-center justify-center gap-1">
                                {/* Descargar comprobante */}
                                <Button
                                  variant="outline"
                                  size="sm"
                                  onClick={() => handleDescargarComprobante(mov)}
                                  disabled={descargandoComprobante === mov.id}
                                  title="Descargar comprobante"
                                >
                                  <Download className="h-4 w-4 text-green-600" />
                                </Button>

                                {/* Editar monto (solo para cargos) */}
                                {mov.tipo === 'cargo' && !mov.anulado && (
                                  <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={() => {
                                      setMovimientoAEditar(mov)
                                      setShowEditarMontoModal(true)
                                    }}
                                    title="Editar monto"
                                  >
                                    <Pencil className="h-4 w-4 text-blue-600" />
                                  </Button>
                                )}

                                {/* Anular movimiento */}
                                {isAdmin && !mov.anulado && (
                                  <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={() => {
                                      setMovimientoAAnular(mov)
                                      setShowAnularModal(true)
                                    }}
                                    title="Anular movimiento"
                                  >
                                    <Trash2 className="h-4 w-4 text-red-600" />
                                  </Button>
                                )}

                                {/* Menú 3 puntos: Historial */}
                                <div className="relative">
                                  <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={() => setMenuAbiertoId(menuAbiertoId === mov.id ? null : mov.id)}
                                    title="Más opciones"
                                  >
                                    <MoreVertical className="h-4 w-4" />
                                  </Button>
                                  {menuAbiertoId === mov.id && (
                                    <>
                                      <div
                                        className="fixed inset-0 z-10"
                                        onClick={() => setMenuAbiertoId(null)}
                                      />
                                      <div className="absolute right-0 mt-1 w-40 bg-white border rounded-md shadow-lg z-20">
                                        <button
                                          className="flex items-center gap-2 w-full px-3 py-2 text-sm text-left hover:bg-gray-100"
                                          onClick={() => {
                                            setMenuAbiertoId(null)
                                            handleVerHistorial(mov)
                                          }}
                                        >
                                          <History className="h-4 w-4 text-blue-600" />
                                          Historial
                                        </button>
                                      </div>
                                    </>
                                  )}
                                </div>
                              </div>
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
                {movimientos.length > 0 && (
                  <Pagination
                    currentPage={movimientosPage}
                    totalPages={movimientosTotalPages}
                    totalItems={movimientos.length}
                    pageSize={movimientosPageSize}
                    onPageChange={setMovimientosPage}
                    onPageSizeChange={(size) => {
                      setMovimientosPageSize(size)
                      setMovimientosPage(1)
                    }}
                  />
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Mensaje cuando no hay cliente seleccionado */}
      {!selectedCliente && (
        <Card>
          <CardContent className="py-12">
            <div className="text-center text-gray-500">
              <Users className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>Seleccione un cliente para ver su cuenta corriente</p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Modal Pago */}
      {showPagoModal && selectedCliente && (
        <PagoModal
          empresaId={selectedCliente}
          empresaNombre={resumen?.empresa_nombre || ''}
          onClose={() => setShowPagoModal(false)}
          onSuccess={() => {
            setShowPagoModal(false)
            queryClient.invalidateQueries({ queryKey: ['cuenta-corriente-resumen'] })
            queryClient.invalidateQueries({ queryKey: ['cuenta-corriente-movimientos'] })
            queryClient.invalidateQueries({ queryKey: ['clientes-con-deuda'] })
          }}
        />
      )}

      {/* Modal Ajuste */}
      {showAjusteModal && selectedCliente && (
        <AjusteModal
          empresaId={selectedCliente}
          empresaNombre={resumen?.empresa_nombre || ''}
          onClose={() => setShowAjusteModal(false)}
          onSuccess={() => {
            setShowAjusteModal(false)
            queryClient.invalidateQueries({ queryKey: ['cuenta-corriente-resumen'] })
            queryClient.invalidateQueries({ queryKey: ['cuenta-corriente-movimientos'] })
            queryClient.invalidateQueries({ queryKey: ['clientes-con-deuda'] })
          }}
        />
      )}

      {/* Modal Editar Monto */}
      {showEditarMontoModal && movimientoAEditar && (
        <EditarMontoModal
          movimiento={movimientoAEditar}
          onClose={() => {
            setShowEditarMontoModal(false)
            setMovimientoAEditar(null)
          }}
          onSuccess={() => {
            setShowEditarMontoModal(false)
            setMovimientoAEditar(null)
            queryClient.invalidateQueries({ queryKey: ['cuenta-corriente-resumen'] })
            queryClient.invalidateQueries({ queryKey: ['cuenta-corriente-movimientos'] })
            queryClient.invalidateQueries({ queryKey: ['clientes-con-deuda'] })
          }}
        />
      )}

      {/* Modal Nuevo Cobro */}
      <NuevoCobroModal
        isOpen={showNuevoCobroModal}
        onClose={() => setShowNuevoCobroModal(false)}
        clienteId={selectedCliente || undefined}
        onSuccess={() => {
          queryClient.invalidateQueries({ queryKey: ['cuenta-corriente-resumen'] })
          queryClient.invalidateQueries({ queryKey: ['cuenta-corriente-movimientos'] })
          queryClient.invalidateQueries({ queryKey: ['clientes-con-deuda'] })
        }}
      />

      {/* Modal Anular Movimiento */}
      {showAnularModal && movimientoAAnular && (
        <AnularMovimientoModal
          movimiento={movimientoAAnular}
          onClose={() => {
            setShowAnularModal(false)
            setMovimientoAAnular(null)
          }}
          onSuccess={() => {
            setShowAnularModal(false)
            setMovimientoAAnular(null)
            queryClient.invalidateQueries({ queryKey: ['cuenta-corriente-resumen'] })
            queryClient.invalidateQueries({ queryKey: ['cuenta-corriente-movimientos'] })
            queryClient.invalidateQueries({ queryKey: ['clientes-con-deuda'] })
          }}
        />
      )}

      {/* Modal Historial */}
      {showHistorialModal && historialMovimiento && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <Card className="w-full max-w-md">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-2">
                  <History className="h-5 w-5 text-blue-600" />
                  Historial del Movimiento
                </CardTitle>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    setShowHistorialModal(false)
                    setHistorialMovimiento(null)
                    setHistorial([])
                  }}
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
              <p className="text-sm text-gray-500 mt-1 truncate">{historialMovimiento.descripcion}</p>
            </CardHeader>
            <CardContent>
              {cargandoHistorial ? (
                <div className="py-8 text-center text-gray-500">Cargando historial...</div>
              ) : historial.length === 0 ? (
                <div className="py-8 text-center text-gray-500">No hay registros de historial</div>
              ) : (
                <div className="space-y-2">
                  {historial.map((item, idx) => {
                    const fecha = new Date(item.fecha)
                    const fechaStr = fecha.toLocaleDateString('es-AR', { day: '2-digit', month: '2-digit', year: '2-digit' })
                    const horaStr = fecha.toLocaleTimeString('es-AR', { hour: '2-digit', minute: '2-digit' })
                    return (
                      <div
                        key={item.id || `idx-${idx}`}
                        className="py-2 px-3 bg-gray-50 rounded-lg"
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-3">
                            <span className="text-sm text-gray-600">{fechaStr} - {horaStr}</span>
                            <span className="font-medium text-sm">
                              {item.usuario_nombre.toUpperCase()}
                            </span>
                          </div>
                          <span className={`text-xs font-semibold px-2 py-1 rounded ${
                            item.accion === 'CREACION' ? 'bg-green-100 text-green-700' :
                            item.accion === 'MODIFICACION' ? 'bg-yellow-100 text-yellow-700' :
                            item.accion === 'ANULACION' ? 'bg-red-100 text-red-700' :
                            'bg-gray-100 text-gray-700'
                          }`}>
                            {item.accion}
                          </span>
                        </div>
                        {item.detalle && (
                          <p className="text-xs text-gray-500 mt-1 italic">{item.detalle}</p>
                        )}
                      </div>
                    )
                  })}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}

// Modal para anular un movimiento
function AnularMovimientoModal({
  movimiento,
  onClose,
  onSuccess,
}: {
  movimiento: any
  onClose: () => void
  onSuccess: () => void
}) {
  const [motivo, setMotivo] = useState('')

  const mutation = useMutation({
    mutationFn: () => cuentaCorrienteService.anularMovimiento(movimiento.id, motivo),
    onSuccess,
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (motivo.trim().length < 5) {
      alert('El motivo debe tener al menos 5 caracteres')
      return
    }
    mutation.mutate()
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <Card className="w-full max-w-md">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2 text-red-600">
              <Trash2 className="h-5 w-5" />
              Anular Movimiento
            </CardTitle>
            <Button variant="ghost" size="sm" onClick={onClose}>
              <X className="h-4 w-4" />
            </Button>
          </div>
          <p className="text-sm text-gray-500 mt-1">{movimiento.descripcion}</p>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="bg-red-50 border border-red-200 p-3 rounded-lg text-sm text-red-700">
              Esta acción revertirá el saldo del cliente. El movimiento quedará marcado como anulado y no se eliminará.
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Motivo de anulación *</label>
              <Input
                value={motivo}
                onChange={(e) => setMotivo(e.target.value)}
                placeholder="Indique el motivo (mínimo 5 caracteres)"
              />
            </div>
            <div className="flex gap-2 pt-4">
              <Button
                type="submit"
                disabled={mutation.isPending}
                className="flex-1 bg-red-600 hover:bg-red-700"
              >
                {mutation.isPending ? 'Anulando...' : 'Anular Movimiento'}
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

// Modal para registrar pago
function PagoModal({
  empresaId,
  empresaNombre,
  onClose,
  onSuccess
}: {
  empresaId: string
  empresaNombre: string
  onClose: () => void
  onSuccess: () => void
}) {
  const [monto, setMonto] = useState('')
  const [fecha, setFecha] = useState(getTodayLocalDate())
  const [descripcion, setDescripcion] = useState('Pago recibido')
  const [metodoPago, setMetodoPago] = useState('efectivo')
  const [registrarIngreso, setRegistrarIngreso] = useState(true)

  const mutation = useMutation({
    mutationFn: () => cuentaCorrienteService.registrarPago({
      empresa_id: empresaId,
      monto: parseFloat(monto),
      fecha,
      descripcion,
      metodo_pago: metodoPago,
      registrar_ingreso: registrarIngreso,
    }),
    onSuccess,
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!monto || parseFloat(monto) <= 0) {
      alert('Ingrese un monto válido')
      return
    }
    mutation.mutate()
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <Card className="w-full max-w-md">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <CreditCard className="h-5 w-5 text-green-600" />
              Registrar Pago
            </CardTitle>
            <Button variant="ghost" size="sm" onClick={onClose}>
              <X className="h-4 w-4" />
            </Button>
          </div>
          <p className="text-sm text-gray-500">{empresaNombre}</p>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Monto *</label>
              <Input
                type="number"
                step="0.01"
                value={monto}
                onChange={(e) => setMonto(e.target.value)}
                placeholder="0.00"
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Fecha *</label>
              <Input
                type="date"
                value={fecha}
                onChange={(e) => setFecha(e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Método de Pago</label>
              <select
                value={metodoPago}
                onChange={(e) => setMetodoPago(e.target.value)}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              >
                <option value="efectivo">Efectivo</option>
                <option value="transferencia">Transferencia</option>
                <option value="cheque">Cheque</option>
                <option value="tarjeta">Tarjeta</option>
              </select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Descripción</label>
              <Input
                value={descripcion}
                onChange={(e) => setDescripcion(e.target.value)}
                placeholder="Pago recibido"
              />
            </div>

            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="registrarIngreso"
                checked={registrarIngreso}
                onChange={(e) => setRegistrarIngreso(e.target.checked)}
                className="rounded"
              />
              <label htmlFor="registrarIngreso" className="text-sm">
                Registrar como ingreso en Finanzas
              </label>
            </div>

            <div className="flex gap-2 pt-4">
              <Button type="submit" disabled={mutation.isPending} className="flex-1">
                {mutation.isPending ? 'Guardando...' : 'Registrar Pago'}
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

// Modal para ajuste
function AjusteModal({
  empresaId,
  empresaNombre,
  onClose,
  onSuccess
}: {
  empresaId: string
  empresaNombre: string
  onClose: () => void
  onSuccess: () => void
}) {
  const [monto, setMonto] = useState('')
  const [esCredito, setEsCredito] = useState(true)
  const [fecha, setFecha] = useState(getTodayLocalDate())
  const [descripcion, setDescripcion] = useState('')

  const mutation = useMutation({
    mutationFn: () => cuentaCorrienteService.registrarAjuste({
      empresa_id: empresaId,
      monto: parseFloat(monto),
      es_credito: esCredito,
      fecha,
      descripcion,
    }),
    onSuccess,
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!monto || parseFloat(monto) <= 0) {
      alert('Ingrese un monto válido')
      return
    }
    if (!descripcion.trim()) {
      alert('Ingrese una descripción')
      return
    }
    mutation.mutate()
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <Card className="w-full max-w-md">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5 text-blue-600" />
              Registrar Ajuste
            </CardTitle>
            <Button variant="ghost" size="sm" onClick={onClose}>
              <X className="h-4 w-4" />
            </Button>
          </div>
          <p className="text-sm text-gray-500">{empresaNombre}</p>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Tipo de Ajuste</label>
              <div className="flex gap-2">
                <Button
                  type="button"
                  variant={esCredito ? 'default' : 'outline'}
                  onClick={() => setEsCredito(true)}
                  className="flex-1"
                >
                  <TrendingDown className="h-4 w-4 mr-1" />
                  Nota de Crédito
                </Button>
                <Button
                  type="button"
                  variant={!esCredito ? 'default' : 'outline'}
                  onClick={() => setEsCredito(false)}
                  className="flex-1"
                >
                  <TrendingUp className="h-4 w-4 mr-1" />
                  Nota de Débito
                </Button>
              </div>
              <p className="text-xs text-gray-500">
                {esCredito ? 'Reduce la deuda del cliente' : 'Aumenta la deuda del cliente'}
              </p>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Monto *</label>
              <Input
                type="number"
                step="0.01"
                value={monto}
                onChange={(e) => setMonto(e.target.value)}
                placeholder="0.00"
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Fecha *</label>
              <Input
                type="date"
                value={fecha}
                onChange={(e) => setFecha(e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Descripción/Motivo *</label>
              <Input
                value={descripcion}
                onChange={(e) => setDescripcion(e.target.value)}
                placeholder="Motivo del ajuste"
              />
            </div>

            <div className="flex gap-2 pt-4">
              <Button type="submit" disabled={mutation.isPending} className="flex-1">
                {mutation.isPending ? 'Guardando...' : 'Registrar Ajuste'}
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

// Modal para editar monto de cargo
function EditarMontoModal({
  movimiento,
  onClose,
  onSuccess
}: {
  movimiento: any
  onClose: () => void
  onSuccess: () => void
}) {
  // Extraer peso en toneladas del descripción si es un pesaje
  const extractPesoTn = (descripcion: string): number | null => {
    const match = descripcion.match(/\((\d+(?:[.,]\d+)?)\s*tn\)/)
    if (match) {
      return parseFloat(match[1].replace(',', '.'))
    }
    return null
  }

  const pesoTn = extractPesoTn(movimiento.descripcion)
  const [precioUnitario, setPrecioUnitario] = useState('')
  const [montoTotal, setMontoTotal] = useState(movimiento.monto.toString())

  // Calcular monto automáticamente cuando cambia precio unitario
  const handlePrecioChange = (value: string) => {
    setPrecioUnitario(value)
    if (pesoTn && value) {
      const precio = parseFloat(value)
      if (!isNaN(precio)) {
        const total = pesoTn * precio
        setMontoTotal(total.toFixed(2))
      }
    }
  }

  const mutation = useMutation({
    mutationFn: () => cuentaCorrienteService.actualizarMontoCargo(
      movimiento.id,
      parseFloat(montoTotal),
      precioUnitario ? parseFloat(precioUnitario) : undefined
    ),
    onSuccess,
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!montoTotal || parseFloat(montoTotal) < 0) {
      alert('Ingrese un monto válido')
      return
    }
    mutation.mutate()
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <Card className="w-full max-w-md">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Pencil className="h-5 w-5 text-blue-600" />
              Editar Monto
            </CardTitle>
            <Button variant="ghost" size="sm" onClick={onClose}>
              <X className="h-4 w-4" />
            </Button>
          </div>
          <p className="text-sm text-gray-500">{movimiento.descripcion}</p>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {pesoTn && (
              <div className="bg-blue-50 p-3 rounded-lg">
                <p className="text-sm text-blue-700">
                  <strong>Peso:</strong> {pesoTn.toFixed(2)} toneladas
                </p>
                <p className="text-xs text-blue-600 mt-1">
                  Ingrese el precio por tonelada para calcular el monto automáticamente
                </p>
              </div>
            )}

            {pesoTn && (
              <div className="space-y-2">
                <label className="text-sm font-medium">Precio por Tonelada</label>
                <Input
                  type="number"
                  step="0.01"
                  value={precioUnitario}
                  onChange={(e) => handlePrecioChange(e.target.value)}
                  placeholder="0.00"
                />
              </div>
            )}

            <div className="space-y-2">
              <label className="text-sm font-medium">Monto Total *</label>
              <Input
                type="number"
                step="0.01"
                value={montoTotal}
                onChange={(e) => setMontoTotal(e.target.value)}
                placeholder="0.00"
              />
              {movimiento.monto > 0 && (
                <p className="text-xs text-gray-500">
                  Monto anterior: ${formatNumber(movimiento.monto, 2)}
                </p>
              )}
            </div>

            <div className="flex gap-2 pt-4">
              <Button type="submit" disabled={mutation.isPending} className="flex-1">
                {mutation.isPending ? 'Guardando...' : 'Guardar Monto'}
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
