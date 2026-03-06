import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Users, Plus, CreditCard, FileText, Download,
  TrendingUp, TrendingDown,
  X, ChevronDown, ChevronUp, Search
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { cuentaCorrienteService } from '@/services/cuentaCorrienteService'
import { empresasService } from '@/services/empresasService'
import { facturacionService } from '@/services/facturacionService'
import { formatDate, formatNumber } from '@/lib/utils'

export default function CuentaCorrienteTab() {
  const queryClient = useQueryClient()
  const [selectedCliente, setSelectedCliente] = useState<string | null>(null)
  const [showPagoModal, setShowPagoModal] = useState(false)
  const [showAjusteModal, setShowAjusteModal] = useState(false)
  const [busqueda, setBusqueda] = useState('')
  const [mostrarTodos, setMostrarTodos] = useState(false)

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
  const clientesFiltrados = todosClientes.filter(c =>
    c.nombre.toLowerCase().includes(busqueda.toLowerCase()) ||
    (c.cuit && c.cuit.includes(busqueda))
  )

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

  return (
    <div className="space-y-6">
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
                onChange={(e) => setBusqueda(e.target.value)}
                className="pl-10"
              />
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-2">
            {clientesFiltrados.slice(0, mostrarTodos ? undefined : 10).map((cliente) => {
              const deuda = clientesConDeuda.find(c => c.id === cliente.id)
              return (
                <button
                  key={cliente.id}
                  onClick={() => setSelectedCliente(cliente.id)}
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
          {clientesFiltrados.length > 10 && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setMostrarTodos(!mostrarTodos)}
              className="w-full mt-4"
            >
              {mostrarTodos ? (
                <>
                  <ChevronUp className="h-4 w-4 mr-2" />
                  Mostrar menos
                </>
              ) : (
                <>
                  <ChevronDown className="h-4 w-4 mr-2" />
                  Ver todos ({clientesFiltrados.length})
                </>
              )}
            </Button>
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
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200">
                      {movimientos.length === 0 ? (
                        <tr>
                          <td colSpan={7} className="px-4 py-8 text-center text-gray-500">
                            No hay movimientos
                          </td>
                        </tr>
                      ) : (
                        movimientos.map((mov) => (
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
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
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
  const [fecha, setFecha] = useState(new Date().toISOString().split('T')[0])
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
  const [fecha, setFecha] = useState(new Date().toISOString().split('T')[0])
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
