import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Users, Plus, CreditCard, FileText,
  TrendingUp, TrendingDown, ArrowUpRight, ArrowDownRight,
  X
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { cuentaCorrienteService } from '@/services/cuentaCorrienteService'
import { empresasService } from '@/services/empresasService'
import { formatDate, formatNumber } from '@/lib/utils'

export default function CuentaCorrienteTab() {
  const queryClient = useQueryClient()
  const [selectedCliente, setSelectedCliente] = useState<string | null>(null)
  const [showPagoModal, setShowPagoModal] = useState(false)
  const [showAjusteModal, setShowAjusteModal] = useState(false)

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

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Lista de clientes */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle className="text-lg">Clientes</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 max-h-[500px] overflow-y-auto">
            {todosClientes.length === 0 ? (
              <p className="text-sm text-gray-500 text-center py-4">No hay clientes</p>
            ) : (
              todosClientes.map((cliente) => {
                const deuda = clientesConDeuda.find(c => c.id === cliente.id)
                return (
                  <button
                    key={cliente.id}
                    onClick={() => setSelectedCliente(cliente.id)}
                    className={`w-full p-3 rounded-lg text-left transition-colors ${
                      selectedCliente === cliente.id
                        ? 'bg-blue-50 border-2 border-blue-500'
                        : 'bg-gray-50 hover:bg-gray-100 border-2 border-transparent'
                    }`}
                  >
                    <div className="flex justify-between items-start">
                      <div>
                        <p className="font-medium text-sm">{cliente.nombre}</p>
                        {cliente.cuit && (
                          <p className="text-xs text-gray-500">CUIT: {cliente.cuit}</p>
                        )}
                      </div>
                      {deuda && deuda.saldo > 0 && (
                        <span className="text-sm font-bold text-red-600">
                          ${formatNumber(deuda.saldo, 2)}
                        </span>
                      )}
                    </div>
                  </button>
                )
              })
            )}
          </CardContent>
        </Card>

        {/* Detalle del cliente */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg">
                {resumen ? resumen.empresa_nombre : 'Seleccione un cliente'}
              </CardTitle>
              {selectedCliente && (
                <div className="flex gap-2">
                  <Button size="sm" onClick={() => setShowPagoModal(true)}>
                    <Plus className="h-4 w-4 mr-1" />
                    Registrar Pago
                  </Button>
                  <Button size="sm" variant="outline" onClick={() => setShowAjusteModal(true)}>
                    <FileText className="h-4 w-4 mr-1" />
                    Ajuste
                  </Button>
                </div>
              )}
            </div>
          </CardHeader>
          <CardContent>
            {!selectedCliente ? (
              <div className="text-center py-12 text-gray-500">
                <Users className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>Seleccione un cliente para ver su cuenta corriente</p>
              </div>
            ) : (
              <div className="space-y-6">
                {/* Resumen */}
                {resumen && (
                  <div className="grid grid-cols-3 gap-4">
                    <div className="bg-red-50 p-4 rounded-lg">
                      <p className="text-xs text-red-600 font-medium">Total Cargos</p>
                      <p className="text-xl font-bold text-red-700">
                        ${formatNumber(resumen.total_cargos, 2)}
                      </p>
                    </div>
                    <div className="bg-green-50 p-4 rounded-lg">
                      <p className="text-xs text-green-600 font-medium">Total Pagos</p>
                      <p className="text-xl font-bold text-green-700">
                        ${formatNumber(resumen.total_pagos, 2)}
                      </p>
                    </div>
                    <div className={`p-4 rounded-lg ${resumen.saldo_actual > 0 ? 'bg-orange-50' : 'bg-blue-50'}`}>
                      <p className={`text-xs font-medium ${resumen.saldo_actual > 0 ? 'text-orange-600' : 'text-blue-600'}`}>
                        Saldo Actual
                      </p>
                      <p className={`text-xl font-bold ${resumen.saldo_actual > 0 ? 'text-orange-700' : 'text-blue-700'}`}>
                        ${formatNumber(resumen.saldo_actual, 2)}
                      </p>
                    </div>
                  </div>
                )}

                {/* Movimientos */}
                <div>
                  <h4 className="font-medium mb-3">Movimientos</h4>
                  <div className="space-y-2 max-h-[350px] overflow-y-auto">
                    {movimientos.length === 0 ? (
                      <p className="text-sm text-gray-500 text-center py-4">
                        No hay movimientos
                      </p>
                    ) : (
                      movimientos.map((mov) => (
                        <div
                          key={mov.id}
                          className={`p-3 rounded-lg border ${
                            mov.anulado ? 'bg-gray-100 opacity-60' : 'bg-white'
                          }`}
                        >
                          <div className="flex items-start justify-between">
                            <div className="flex items-start gap-3">
                              <div className={`p-2 rounded-full ${
                                mov.tipo === 'cargo' ? 'bg-red-100' :
                                mov.tipo === 'pago' ? 'bg-green-100' : 'bg-blue-100'
                              }`}>
                                {mov.tipo === 'cargo' ? (
                                  <ArrowUpRight className="h-4 w-4 text-red-600" />
                                ) : mov.tipo === 'pago' ? (
                                  <ArrowDownRight className="h-4 w-4 text-green-600" />
                                ) : (
                                  <FileText className="h-4 w-4 text-blue-600" />
                                )}
                              </div>
                              <div>
                                <p className="font-medium text-sm">{mov.descripcion}</p>
                                <p className="text-xs text-gray-500">
                                  {formatDate(mov.fecha)}
                                  {mov.metodo_pago && ` - ${mov.metodo_pago}`}
                                </p>
                                {mov.anulado && (
                                  <span className="text-xs text-red-500 font-medium">ANULADO</span>
                                )}
                              </div>
                            </div>
                            <div className="text-right">
                              <p className={`font-bold ${
                                mov.tipo === 'cargo' ? 'text-red-600' :
                                mov.tipo === 'pago' ? 'text-green-600' : 'text-blue-600'
                              }`}>
                                {mov.tipo === 'cargo' ? '+' : '-'}${formatNumber(Math.abs(mov.monto), 2)}
                              </p>
                              <p className="text-xs text-gray-500">
                                Saldo: ${formatNumber(mov.saldo_posterior, 2)}
                              </p>
                            </div>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

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
