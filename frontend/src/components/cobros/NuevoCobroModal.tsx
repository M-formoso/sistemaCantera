import { useState, useEffect, useMemo } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  X, Plus, Trash2, AlertTriangle, CheckCircle, DollarSign,
  CreditCard, FileText, Receipt, ArrowRight, Loader2,
  AlertCircle
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { cobrosService, ItemCobro, TIPOS_ITEM_HABER, CobroClienteCreateWithItems, DocumentosPendientes } from '@/services/cobrosService'
import { empresasService } from '@/services/empresasService'
import { formatNumber, getTodayLocalDate } from '@/lib/utils'
import { Empresa } from '@/types'

interface NuevoCobroModalProps {
  isOpen: boolean
  onClose: () => void
  clienteId?: string  // Si viene de un cliente específico
  onSuccess?: () => void
}

type Paso = 'cabecera' | 'haber' | 'debe' | 'resumen'

export default function NuevoCobroModal({
  isOpen,
  onClose,
  clienteId,
  onSuccess
}: NuevoCobroModalProps) {
  const queryClient = useQueryClient()

  // Estado del flujo
  const [paso, setPaso] = useState<Paso>('cabecera')

  // Datos de cabecera
  const [empresaId, setEmpresaId] = useState(clienteId || '')
  const [fecha, setFecha] = useState(getTodayLocalDate())
  const [montoTotal, setMontoTotal] = useState<number>(0)
  const [numeroOrdenPago, setNumeroOrdenPago] = useState('')
  const [observaciones, setObservaciones] = useState('')

  // Items
  const [itemsHaber, setItemsHaber] = useState<ItemCobro[]>([])
  const [itemsDebe, setItemsDebe] = useState<ItemCobro[]>([])

  // UI
  const [clienteBusqueda, setClienteBusqueda] = useState('')
  const [showSugerencias, setShowSugerencias] = useState(false)

  // Queries
  const { data: clientes = [] } = useQuery({
    queryKey: ['clientes'],
    queryFn: () => empresasService.getAll('cliente'),
  })

  const { data: documentosPendientes } = useQuery({
    queryKey: ['documentos-pendientes', empresaId],
    queryFn: () => cobrosService.getDocumentosPendientes(empresaId),
    enabled: !!empresaId && paso !== 'cabecera',
  })

  // Mutation
  const crearCobroMutation = useMutation({
    mutationFn: (data: CobroClienteCreateWithItems) => cobrosService.crearConItems(data),
    onSuccess: async (cobro) => {
      // Aplicar el cobro directamente
      try {
        await cobrosService.aplicar(cobro.id)
        queryClient.invalidateQueries({ queryKey: ['cuenta-corriente'] })
        queryClient.invalidateQueries({ queryKey: ['cobros'] })
        queryClient.invalidateQueries({ queryKey: ['clientes-con-deuda'] })
        onSuccess?.()
        onClose()
      } catch (error) {
        console.error('Error aplicando cobro:', error)
        alert('El cobro se creó pero hubo un error al aplicarlo')
      }
    },
  })

  // Calcular totales
  const totalHaber = useMemo(() =>
    itemsHaber.reduce((sum, item) => sum + (item.monto || 0), 0),
    [itemsHaber]
  )

  const totalDebe = useMemo(() =>
    itemsDebe.reduce((sum, item) => sum + (item.monto || 0), 0),
    [itemsDebe]
  )

  const diferencia = totalHaber - totalDebe
  const diferenciaOrden = montoTotal - totalHaber

  // Filtrar sugerencias de clientes
  const clientesFiltrados = useMemo(() => {
    if (!clienteBusqueda) return []
    return clientes.filter(c =>
      c.nombre.toLowerCase().includes(clienteBusqueda.toLowerCase())
    ).slice(0, 10)
  }, [clientes, clienteBusqueda])

  // Seleccionar cliente
  const seleccionarCliente = (cliente: Empresa) => {
    setEmpresaId(cliente.id)
    setClienteBusqueda(cliente.nombre)
    setShowSugerencias(false)
  }

  // Agregar item al HABER
  const agregarItemHaber = (tipo: string) => {
    const nuevoItem: ItemCobro = {
      tipo_item: tipo,
      concepto: 'haber',
      monto: 0,
      descripcion: TIPOS_ITEM_HABER.find(t => t.value === tipo)?.label || tipo,
    }
    setItemsHaber([...itemsHaber, nuevoItem])
  }

  // Agregar item al DEBE (factura o ticket)
  const agregarItemDebeFactura = (factura: DocumentosPendientes['facturas'][0]) => {
    const nuevoItem: ItemCobro = {
      tipo_item: 'factura',
      concepto: 'debe',
      monto: factura.saldo_pendiente,
      descripcion: `Factura ${factura.numero_factura}`,
      factura_id: factura.id,
    }
    setItemsDebe([...itemsDebe, nuevoItem])
  }

  const agregarItemDebeTicket = (ticket: DocumentosPendientes['tickets'][0]) => {
    const nuevoItem: ItemCobro = {
      tipo_item: 'ticket',
      concepto: 'debe',
      monto: ticket.saldo_pendiente,
      descripcion: `${ticket.tipo === 'remito' ? 'Remito' : 'Ticket'} #${ticket.numero}`,
      remito_id: ticket.id,
    }
    setItemsDebe([...itemsDebe, nuevoItem])
  }

  // Actualizar monto de item HABER
  const actualizarMontoHaber = (index: number, monto: number) => {
    const nuevos = [...itemsHaber]
    nuevos[index] = { ...nuevos[index], monto }
    setItemsHaber(nuevos)
  }

  // Actualizar detalles de item HABER
  const actualizarDetalleHaber = (index: number, campo: string, valor: string) => {
    const nuevos = [...itemsHaber]
    nuevos[index] = { ...nuevos[index], [campo]: valor }
    setItemsHaber(nuevos)
  }

  // Actualizar monto de item DEBE
  const actualizarMontoDebe = (index: number, monto: number) => {
    const nuevos = [...itemsDebe]
    nuevos[index] = { ...nuevos[index], monto }
    setItemsDebe(nuevos)
  }

  // Eliminar items
  const eliminarItemHaber = (index: number) => {
    setItemsHaber(itemsHaber.filter((_, i) => i !== index))
  }

  const eliminarItemDebe = (index: number) => {
    setItemsDebe(itemsDebe.filter((_, i) => i !== index))
  }

  // Navegar entre pasos
  const siguientePaso = () => {
    if (paso === 'cabecera') {
      if (!empresaId || !montoTotal) {
        alert('Complete el cliente y el monto total')
        return
      }
      setPaso('haber')
    } else if (paso === 'haber') {
      if (itemsHaber.length === 0) {
        alert('Agregue al menos un medio de pago')
        return
      }
      if (Math.abs(diferenciaOrden) > 0.01) {
        if (!confirm(`El total de medios de pago ($${formatNumber(totalHaber, 2)}) no coincide con el monto de la orden ($${formatNumber(montoTotal, 2)}). ¿Continuar de todos modos?`)) {
          return
        }
      }
      setPaso('debe')
    } else if (paso === 'debe') {
      setPaso('resumen')
    }
  }

  const pasoAnterior = () => {
    if (paso === 'haber') setPaso('cabecera')
    else if (paso === 'debe') setPaso('haber')
    else if (paso === 'resumen') setPaso('debe')
  }

  // Guardar cobro
  const guardarCobro = () => {
    const data: CobroClienteCreateWithItems = {
      empresa_id: empresaId,
      fecha,
      monto_total: montoTotal,
      numero_orden_pago: numeroOrdenPago || undefined,
      observaciones: observaciones || undefined,
      items: [...itemsHaber, ...itemsDebe],
    }

    crearCobroMutation.mutate(data)
  }

  // Reset al cerrar
  useEffect(() => {
    if (!isOpen) {
      setPaso('cabecera')
      setEmpresaId(clienteId || '')
      setFecha(getTodayLocalDate())
      setMontoTotal(0)
      setNumeroOrdenPago('')
      setObservaciones('')
      setItemsHaber([])
      setItemsDebe([])
      setClienteBusqueda('')
    }
  }, [isOpen, clienteId])

  // Cargar nombre del cliente si viene preseleccionado
  useEffect(() => {
    if (clienteId && clientes.length > 0) {
      const cliente = clientes.find(c => c.id === clienteId)
      if (cliente) {
        setClienteBusqueda(cliente.nombre)
      }
    }
  }, [clienteId, clientes])

  if (!isOpen) return null

  const clienteSeleccionado = clientes.find(c => c.id === empresaId)

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <Card className="w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
        <CardHeader className="flex-shrink-0 border-b">
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <DollarSign className="h-5 w-5" />
              Nuevo Cobro
            </CardTitle>
            <Button variant="ghost" size="sm" onClick={onClose}>
              <X className="h-5 w-5" />
            </Button>
          </div>
          {/* Progress steps */}
          <div className="flex items-center gap-2 mt-4">
            {['cabecera', 'haber', 'debe', 'resumen'].map((p, i) => (
              <div key={p} className="flex items-center">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                  paso === p ? 'bg-blue-600 text-white' :
                  ['cabecera', 'haber', 'debe', 'resumen'].indexOf(paso) > i
                    ? 'bg-green-500 text-white' : 'bg-gray-200 text-gray-600'
                }`}>
                  {i + 1}
                </div>
                {i < 3 && <ArrowRight className="h-4 w-4 mx-2 text-gray-400" />}
              </div>
            ))}
          </div>
          <div className="flex gap-4 text-xs text-gray-500 mt-1">
            <span className={paso === 'cabecera' ? 'font-bold text-blue-600' : ''}>Orden de Pago</span>
            <span className={paso === 'haber' ? 'font-bold text-blue-600' : ''}>Medios de Pago</span>
            <span className={paso === 'debe' ? 'font-bold text-blue-600' : ''}>Aplicación</span>
            <span className={paso === 'resumen' ? 'font-bold text-blue-600' : ''}>Confirmar</span>
          </div>
        </CardHeader>

        <CardContent className="flex-1 overflow-y-auto p-6">
          {/* PASO 1: CABECERA */}
          {paso === 'cabecera' && (
            <div className="space-y-6">
              <div className="bg-blue-50 border border-blue-200 rounded-md p-4 text-sm text-blue-700">
                <p className="font-medium">Paso 1: Datos de la Orden de Pago</p>
                <p>Ingrese el cliente, la fecha y el monto total de la orden de pago recibida.</p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Cliente */}
                <div className="space-y-2 relative">
                  <label className="text-sm font-medium">Cliente *</label>
                  <Input
                    value={clienteBusqueda}
                    onChange={(e) => {
                      setClienteBusqueda(e.target.value)
                      setShowSugerencias(true)
                      setEmpresaId('')
                    }}
                    onFocus={() => setShowSugerencias(true)}
                    placeholder="Buscar cliente..."
                  />
                  {showSugerencias && clientesFiltrados.length > 0 && (
                    <div className="absolute z-10 w-full mt-1 bg-white border rounded-md shadow-lg max-h-48 overflow-y-auto">
                      {clientesFiltrados.map((cliente) => (
                        <button
                          key={cliente.id}
                          type="button"
                          className="w-full px-3 py-2 text-left hover:bg-gray-100 text-sm"
                          onClick={() => seleccionarCliente(cliente)}
                        >
                          {cliente.nombre}
                        </button>
                      ))}
                    </div>
                  )}
                </div>

                {/* Fecha */}
                <div className="space-y-2">
                  <label className="text-sm font-medium">Fecha *</label>
                  <Input
                    type="date"
                    value={fecha}
                    onChange={(e) => setFecha(e.target.value)}
                  />
                </div>

                {/* Monto Total */}
                <div className="space-y-2">
                  <label className="text-sm font-medium">Monto Total de la Orden de Pago *</label>
                  <div className="relative">
                    <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500">$</span>
                    <Input
                      type="number"
                      step="0.01"
                      value={montoTotal || ''}
                      onChange={(e) => setMontoTotal(parseFloat(e.target.value) || 0)}
                      placeholder="0.00"
                      className="pl-8 text-lg"
                    />
                  </div>
                </div>

                {/* Número Orden de Pago */}
                <div className="space-y-2">
                  <label className="text-sm font-medium">Número de Orden de Pago</label>
                  <Input
                    value={numeroOrdenPago}
                    onChange={(e) => setNumeroOrdenPago(e.target.value)}
                    placeholder="Ej: OP-2024-001"
                  />
                </div>
              </div>

              {/* Observaciones */}
              <div className="space-y-2">
                <label className="text-sm font-medium">Observaciones</label>
                <textarea
                  value={observaciones}
                  onChange={(e) => setObservaciones(e.target.value)}
                  rows={2}
                  className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  placeholder="Notas adicionales..."
                />
              </div>
            </div>
          )}

          {/* PASO 2: HABER (Medios de Pago) */}
          {paso === 'haber' && (
            <div className="space-y-6">
              <div className="bg-green-50 border border-green-200 rounded-md p-4 text-sm text-green-700">
                <p className="font-medium">Paso 2: Medios de Pago (HABER)</p>
                <p>Desglose cómo se compone el pago: efectivo, cheques, transferencias, retenciones.</p>
                <p className="mt-2 font-bold">Monto de la orden: ${formatNumber(montoTotal, 2)}</p>
              </div>

              {/* Agregar medio de pago */}
              <div>
                <p className="text-sm font-medium mb-2">Agregar medio de pago:</p>
                <div className="flex flex-wrap gap-2">
                  {TIPOS_ITEM_HABER.map((tipo) => (
                    <Button
                      key={tipo.value}
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => agregarItemHaber(tipo.value)}
                    >
                      <Plus className="h-4 w-4 mr-1" />
                      {tipo.label}
                    </Button>
                  ))}
                </div>
              </div>

              {/* Lista de items HABER */}
              <div className="space-y-3">
                {itemsHaber.map((item, index) => (
                  <div key={index} className="border rounded-lg p-4 bg-white">
                    <div className="flex items-start gap-4">
                      <div className="flex-1 grid grid-cols-1 md:grid-cols-3 gap-3">
                        <div>
                          <label className="text-xs text-gray-500">Tipo</label>
                          <p className="font-medium">{item.descripcion}</p>
                        </div>
                        <div>
                          <label className="text-xs text-gray-500">Monto</label>
                          <div className="relative">
                            <span className="absolute left-2 top-1/2 -translate-y-1/2 text-gray-500 text-sm">$</span>
                            <Input
                              type="number"
                              step="0.01"
                              value={item.monto || ''}
                              onChange={(e) => actualizarMontoHaber(index, parseFloat(e.target.value) || 0)}
                              className="pl-6"
                            />
                          </div>
                        </div>

                        {/* Campos adicionales según tipo */}
                        {(item.tipo_item === 'cheque' || item.tipo_item === 'e_cheque') && (
                          <>
                            <div>
                              <label className="text-xs text-gray-500">Banco</label>
                              <Input
                                value={item.banco || ''}
                                onChange={(e) => actualizarDetalleHaber(index, 'banco', e.target.value)}
                                placeholder="Banco"
                              />
                            </div>
                            <div>
                              <label className="text-xs text-gray-500">Nº Cheque</label>
                              <Input
                                value={item.numero_cheque || ''}
                                onChange={(e) => actualizarDetalleHaber(index, 'numero_cheque', e.target.value)}
                                placeholder="Número"
                              />
                            </div>
                            <div>
                              <label className="text-xs text-gray-500">Fecha Cheque</label>
                              <Input
                                type="date"
                                value={item.fecha_cheque || ''}
                                onChange={(e) => actualizarDetalleHaber(index, 'fecha_cheque', e.target.value)}
                              />
                            </div>
                          </>
                        )}

                        {item.tipo_item === 'transferencia' && (
                          <div>
                            <label className="text-xs text-gray-500">Referencia</label>
                            <Input
                              value={item.referencia_transferencia || ''}
                              onChange={(e) => actualizarDetalleHaber(index, 'referencia_transferencia', e.target.value)}
                              placeholder="Nº operación"
                            />
                          </div>
                        )}

                        {item.tipo_item.startsWith('retencion_') && (
                          <div>
                            <label className="text-xs text-gray-500">Nº Certificado</label>
                            <Input
                              value={item.numero_certificado || ''}
                              onChange={(e) => actualizarDetalleHaber(index, 'numero_certificado', e.target.value)}
                              placeholder="Certificado"
                            />
                          </div>
                        )}
                      </div>

                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={() => eliminarItemHaber(index)}
                        className="text-red-600 hover:text-red-700"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                ))}

                {itemsHaber.length === 0 && (
                  <div className="text-center py-8 text-gray-500">
                    <CreditCard className="h-12 w-12 mx-auto mb-2 opacity-50" />
                    <p>No hay medios de pago agregados</p>
                  </div>
                )}
              </div>

              {/* Resumen parcial */}
              <div className="bg-gray-50 rounded-lg p-4">
                <div className="flex justify-between items-center">
                  <span className="font-medium">Total medios de pago:</span>
                  <span className={`text-xl font-bold ${Math.abs(diferenciaOrden) < 0.01 ? 'text-green-600' : 'text-orange-600'}`}>
                    ${formatNumber(totalHaber, 2)}
                  </span>
                </div>
                {Math.abs(diferenciaOrden) > 0.01 && (
                  <div className="mt-2 flex items-center gap-2 text-orange-600 text-sm">
                    <AlertTriangle className="h-4 w-4" />
                    <span>
                      Diferencia con la orden: ${formatNumber(diferenciaOrden, 2)}
                      {diferenciaOrden > 0 ? ' (faltan medios de pago)' : ' (excede la orden)'}
                    </span>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* PASO 3: DEBE (Aplicación) */}
          {paso === 'debe' && (
            <div className="space-y-6">
              <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4 text-sm text-yellow-700">
                <p className="font-medium">Paso 3: Aplicación del Cobro (DEBE)</p>
                <p>Seleccione las facturas o tickets a los que se aplicará este cobro.</p>
                <p className="mt-2 font-bold">Total a aplicar: ${formatNumber(totalHaber, 2)}</p>
              </div>

              {/* Documentos pendientes */}
              {documentosPendientes && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Facturas */}
                  <div>
                    <h4 className="font-medium mb-2 flex items-center gap-2">
                      <FileText className="h-4 w-4" />
                      Facturas Pendientes
                    </h4>
                    <div className="space-y-2 max-h-48 overflow-y-auto">
                      {documentosPendientes.facturas.map((factura) => {
                        const yaAgregada = itemsDebe.some(i => i.factura_id === factura.id)
                        return (
                          <div
                            key={factura.id}
                            className={`border rounded p-2 text-sm flex justify-between items-center ${
                              yaAgregada ? 'bg-green-50 border-green-200' : 'hover:bg-gray-50 cursor-pointer'
                            }`}
                            onClick={() => !yaAgregada && agregarItemDebeFactura(factura)}
                          >
                            <div>
                              <p className="font-medium">{factura.numero_factura}</p>
                              <p className="text-xs text-gray-500">{factura.fecha_emision}</p>
                            </div>
                            <div className="text-right">
                              <p className="font-medium">${formatNumber(factura.saldo_pendiente, 2)}</p>
                              {yaAgregada && <CheckCircle className="h-4 w-4 text-green-600 ml-auto" />}
                            </div>
                          </div>
                        )
                      })}
                      {documentosPendientes.facturas.length === 0 && (
                        <p className="text-gray-500 text-sm">No hay facturas pendientes</p>
                      )}
                    </div>
                  </div>

                  {/* Tickets */}
                  <div>
                    <h4 className="font-medium mb-2 flex items-center gap-2">
                      <Receipt className="h-4 w-4" />
                      Tickets/Remitos Pendientes
                    </h4>
                    <div className="space-y-2 max-h-48 overflow-y-auto">
                      {documentosPendientes.tickets.map((ticket) => {
                        const yaAgregado = itemsDebe.some(i => i.remito_id === ticket.id)
                        return (
                          <div
                            key={ticket.id}
                            className={`border rounded p-2 text-sm flex justify-between items-center ${
                              yaAgregado ? 'bg-green-50 border-green-200' : 'hover:bg-gray-50 cursor-pointer'
                            }`}
                            onClick={() => !yaAgregado && agregarItemDebeTicket(ticket)}
                          >
                            <div>
                              <p className="font-medium">#{ticket.numero}</p>
                              <p className="text-xs text-gray-500">{ticket.material}</p>
                            </div>
                            <div className="text-right">
                              <p className="font-medium">${formatNumber(ticket.saldo_pendiente, 2)}</p>
                              {yaAgregado && <CheckCircle className="h-4 w-4 text-green-600 ml-auto" />}
                            </div>
                          </div>
                        )
                      })}
                      {documentosPendientes.tickets.length === 0 && (
                        <p className="text-gray-500 text-sm">No hay tickets pendientes</p>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {/* Items seleccionados */}
              <div>
                <h4 className="font-medium mb-2">Documentos seleccionados para aplicar:</h4>
                <div className="space-y-2">
                  {itemsDebe.map((item, index) => (
                    <div key={index} className="border rounded p-3 bg-white flex justify-between items-center">
                      <div>
                        <p className="font-medium">{item.descripcion}</p>
                      </div>
                      <div className="flex items-center gap-3">
                        <div className="relative w-32">
                          <span className="absolute left-2 top-1/2 -translate-y-1/2 text-gray-500 text-sm">$</span>
                          <Input
                            type="number"
                            step="0.01"
                            value={item.monto || ''}
                            onChange={(e) => actualizarMontoDebe(index, parseFloat(e.target.value) || 0)}
                            className="pl-6 text-sm"
                          />
                        </div>
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          onClick={() => eliminarItemDebe(index)}
                          className="text-red-600 hover:text-red-700"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  ))}

                  {itemsDebe.length === 0 && (
                    <div className="text-center py-4 text-gray-500">
                      <p>Seleccione facturas o tickets para aplicar el cobro</p>
                    </div>
                  )}
                </div>
              </div>

              {/* Balance */}
              <div className="bg-gray-50 rounded-lg p-4 space-y-2">
                <div className="flex justify-between">
                  <span>Total HABER (medios de pago):</span>
                  <span className="font-medium">${formatNumber(totalHaber, 2)}</span>
                </div>
                <div className="flex justify-between">
                  <span>Total DEBE (aplicaciones):</span>
                  <span className="font-medium">${formatNumber(totalDebe, 2)}</span>
                </div>
                <div className="border-t pt-2 flex justify-between items-center">
                  <span className="font-medium">Diferencia:</span>
                  <span className={`text-lg font-bold ${
                    Math.abs(diferencia) < 0.01 ? 'text-green-600' :
                    diferencia > 0 ? 'text-blue-600' : 'text-orange-600'
                  }`}>
                    ${formatNumber(diferencia, 2)}
                    {diferencia > 0.01 && ' (saldo a favor)'}
                    {diferencia < -0.01 && ' (falta aplicar)'}
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* PASO 4: RESUMEN */}
          {paso === 'resumen' && (
            <div className="space-y-6">
              <div className={`border rounded-md p-4 ${
                Math.abs(diferencia) < 0.01
                  ? 'bg-green-50 border-green-200'
                  : 'bg-yellow-50 border-yellow-200'
              }`}>
                <div className="flex items-center gap-2">
                  {Math.abs(diferencia) < 0.01 ? (
                    <CheckCircle className="h-6 w-6 text-green-600" />
                  ) : (
                    <AlertCircle className="h-6 w-6 text-yellow-600" />
                  )}
                  <div>
                    <p className="font-medium">
                      {Math.abs(diferencia) < 0.01
                        ? 'Cobro balanceado correctamente'
                        : diferencia > 0
                          ? `Quedará saldo a favor del cliente: $${formatNumber(diferencia, 2)}`
                          : `Quedará saldo pendiente: $${formatNumber(Math.abs(diferencia), 2)}`
                      }
                    </p>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Resumen cabecera */}
                <div className="space-y-4">
                  <h4 className="font-medium border-b pb-2">Datos del Cobro</h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-500">Cliente:</span>
                      <span className="font-medium">{clienteSeleccionado?.nombre}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">Fecha:</span>
                      <span className="font-medium">{fecha}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">Monto Orden de Pago:</span>
                      <span className="font-medium">${formatNumber(montoTotal, 2)}</span>
                    </div>
                    {numeroOrdenPago && (
                      <div className="flex justify-between">
                        <span className="text-gray-500">Nº Orden:</span>
                        <span className="font-medium">{numeroOrdenPago}</span>
                      </div>
                    )}
                  </div>
                </div>

                {/* Resumen totales */}
                <div className="space-y-4">
                  <h4 className="font-medium border-b pb-2">Balance</h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-500">Total HABER:</span>
                      <span className="font-medium text-green-600">${formatNumber(totalHaber, 2)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">Total DEBE:</span>
                      <span className="font-medium text-red-600">${formatNumber(totalDebe, 2)}</span>
                    </div>
                    <div className="border-t pt-2 flex justify-between">
                      <span className="font-medium">Diferencia:</span>
                      <span className={`font-bold ${
                        Math.abs(diferencia) < 0.01 ? 'text-green-600' : 'text-yellow-600'
                      }`}>
                        ${formatNumber(diferencia, 2)}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Detalle de items */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <h4 className="font-medium mb-2 text-green-700">Medios de Pago (HABER)</h4>
                  <div className="space-y-1 text-sm">
                    {itemsHaber.map((item, i) => (
                      <div key={i} className="flex justify-between">
                        <span>{item.descripcion}</span>
                        <span>${formatNumber(item.monto, 2)}</span>
                      </div>
                    ))}
                  </div>
                </div>
                <div>
                  <h4 className="font-medium mb-2 text-red-700">Aplicaciones (DEBE)</h4>
                  <div className="space-y-1 text-sm">
                    {itemsDebe.map((item, i) => (
                      <div key={i} className="flex justify-between">
                        <span>{item.descripcion}</span>
                        <span>${formatNumber(item.monto, 2)}</span>
                      </div>
                    ))}
                    {itemsDebe.length === 0 && (
                      <p className="text-gray-500">Sin aplicaciones (queda todo a favor)</p>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}
        </CardContent>

        {/* Footer con botones */}
        <div className="flex-shrink-0 border-t p-4 bg-gray-50 flex justify-between">
          <div>
            {paso !== 'cabecera' && (
              <Button variant="outline" onClick={pasoAnterior}>
                Anterior
              </Button>
            )}
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={onClose}>
              Cancelar
            </Button>
            {paso !== 'resumen' ? (
              <Button onClick={siguientePaso}>
                Siguiente
                <ArrowRight className="h-4 w-4 ml-2" />
              </Button>
            ) : (
              <Button
                onClick={guardarCobro}
                disabled={crearCobroMutation.isPending}
                className="bg-green-600 hover:bg-green-700"
              >
                {crearCobroMutation.isPending ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Guardando...
                  </>
                ) : (
                  <>
                    <CheckCircle className="h-4 w-4 mr-2" />
                    Confirmar y Aplicar Cobro
                  </>
                )}
              </Button>
            )}
          </div>
        </div>
      </Card>
    </div>
  )
}
