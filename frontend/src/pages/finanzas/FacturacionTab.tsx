import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  FileText, Plus, X, Check,
  CreditCard, AlertCircle, ChevronDown, ChevronUp
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { facturacionService, TIPOS_COMPROBANTE, FORMAS_PAGO, Factura } from '@/services/facturacionService'
import { empresasService } from '@/services/empresasService'
import { formatDate, formatNumber } from '@/lib/utils'

export default function FacturacionTab() {
  const queryClient = useQueryClient()
  const [selectedCliente, setSelectedCliente] = useState<string>('')
  const [showCrearFactura, setShowCrearFactura] = useState(false)
  const [showPagoModal, setShowPagoModal] = useState(false)
  const [facturaSeleccionada, setFacturaSeleccionada] = useState<Factura | null>(null)
  const [expandedFactura, setExpandedFactura] = useState<string | null>(null)

  // Queries
  const { data: clientes = [] } = useQuery({
    queryKey: ['empresas-clientes'],
    queryFn: () => empresasService.getClientes(),
  })

  const { data: facturas = [], isLoading } = useQuery({
    queryKey: ['facturas', selectedCliente],
    queryFn: () => facturacionService.getFacturas({
      empresa_id: selectedCliente || undefined,
      limit: 100
    }),
  })

  const { data: facturasPendientes = [] } = useQuery({
    queryKey: ['facturas-pendientes'],
    queryFn: () => facturacionService.getFacturasPendientes(),
  })

  // Estadísticas
  const totalPendiente = facturasPendientes.reduce((sum, f) => sum + f.saldo_pendiente, 0)
  const cantidadPendientes = facturasPendientes.length

  const handleVerDetalle = (factura: Factura) => {
    setExpandedFactura(expandedFactura === factura.id ? null : factura.id)
  }

  const handleRegistrarPago = (factura: Factura) => {
    setFacturaSeleccionada(factura)
    setShowPagoModal(true)
  }

  return (
    <div className="space-y-6">
      {/* Estadísticas */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Facturas Pendientes</div>
            <div className="text-2xl font-bold text-orange-600">{cantidadPendientes}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Total a Cobrar</div>
            <div className="text-2xl font-bold text-red-600">
              ${formatNumber(totalPendiente, 2)}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Total Facturas</div>
            <div className="text-2xl font-bold">{facturas.length}</div>
          </CardContent>
        </Card>
      </div>

      {/* Filtros y acciones */}
      <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
        <div className="flex gap-2 items-center flex-1">
          <select
            value={selectedCliente}
            onChange={(e) => setSelectedCliente(e.target.value)}
            className="h-10 rounded-md border border-input bg-background px-3 py-2 text-sm min-w-[200px]"
          >
            <option value="">Todos los clientes</option>
            {clientes.map((c) => (
              <option key={c.id} value={c.id}>{c.nombre}</option>
            ))}
          </select>
        </div>
        <Button onClick={() => setShowCrearFactura(true)}>
          <Plus className="h-4 w-4 mr-2" />
          Nueva Factura
        </Button>
      </div>

      {/* Lista de facturas */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Facturas</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="text-center py-8">Cargando...</div>
          ) : facturas.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <FileText className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>No hay facturas</p>
            </div>
          ) : (
            <div className="space-y-3">
              {facturas.map((factura) => (
                <div key={factura.id} className="border rounded-lg">
                  {/* Header de factura */}
                  <div
                    className={`p-4 cursor-pointer hover:bg-gray-50 ${
                      factura.anulada ? 'bg-gray-100 opacity-60' : ''
                    }`}
                    onClick={() => handleVerDetalle(factura)}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-4">
                        <div>
                          <p className="font-bold text-sm">{factura.numero_factura}</p>
                          <p className="text-xs text-gray-500">
                            {TIPOS_COMPROBANTE.find(t => t.value === factura.tipo_comprobante)?.label}
                          </p>
                        </div>
                        <div>
                          <p className="text-sm font-medium">{factura.empresa_nombre}</p>
                          <p className="text-xs text-gray-500">{formatDate(factura.fecha_emision)}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-4">
                        <div className="text-right">
                          <p className="font-bold">${formatNumber(factura.total, 2)}</p>
                          {factura.saldo_pendiente > 0 && (
                            <p className="text-xs text-red-600">
                              Pendiente: ${formatNumber(factura.saldo_pendiente, 2)}
                            </p>
                          )}
                        </div>
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                          factura.estado === 'pagada' ? 'bg-green-100 text-green-700' :
                          factura.estado === 'parcial' ? 'bg-yellow-100 text-yellow-700' :
                          factura.estado === 'anulada' ? 'bg-red-100 text-red-700' :
                          'bg-orange-100 text-orange-700'
                        }`}>
                          {factura.estado.toUpperCase()}
                        </span>
                        {expandedFactura === factura.id ? (
                          <ChevronUp className="h-5 w-5 text-gray-400" />
                        ) : (
                          <ChevronDown className="h-5 w-5 text-gray-400" />
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Detalle expandido */}
                  {expandedFactura === factura.id && (
                    <div className="border-t px-4 py-4 bg-gray-50">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {/* Info de la factura */}
                        <div className="space-y-3">
                          <h4 className="font-medium text-sm">Detalle</h4>
                          <div className="grid grid-cols-2 gap-2 text-sm">
                            <div>
                              <span className="text-gray-500">Subtotal:</span>
                              <span className="ml-2">${formatNumber(factura.subtotal, 2)}</span>
                            </div>
                            {factura.iva_21 > 0 && (
                              <div>
                                <span className="text-gray-500">IVA 21%:</span>
                                <span className="ml-2">${formatNumber(factura.iva_21, 2)}</span>
                              </div>
                            )}
                            {factura.percepciones_iibb > 0 && (
                              <div>
                                <span className="text-gray-500">Perc. IIBB:</span>
                                <span className="ml-2">${formatNumber(factura.percepciones_iibb, 2)}</span>
                              </div>
                            )}
                            <div>
                              <span className="text-gray-500 font-medium">Total:</span>
                              <span className="ml-2 font-bold">${formatNumber(factura.total, 2)}</span>
                            </div>
                          </div>

                          {factura.cae && (
                            <div className="text-xs text-gray-500">
                              CAE: {factura.cae} - Vto: {factura.cae_vencimiento}
                            </div>
                          )}
                        </div>

                        {/* Acciones */}
                        <div className="flex flex-col gap-2">
                          {!factura.anulada && factura.saldo_pendiente > 0 && (
                            <Button
                              size="sm"
                              onClick={(e) => {
                                e.stopPropagation()
                                handleRegistrarPago(factura)
                              }}
                            >
                              <CreditCard className="h-4 w-4 mr-2" />
                              Registrar Pago
                            </Button>
                          )}
                          {factura.estado === 'pagada' && (
                            <div className="flex items-center gap-2 text-green-600 text-sm">
                              <Check className="h-4 w-4" />
                              Pagada completamente
                            </div>
                          )}
                        </div>
                      </div>

                      {/* Pagos realizados */}
                      {factura.pagos && factura.pagos.length > 0 && (
                        <div className="mt-4 pt-4 border-t">
                          <h4 className="font-medium text-sm mb-2">Pagos Registrados</h4>
                          <div className="space-y-2">
                            {factura.pagos.map((pago) => (
                              <div key={pago.id} className="flex justify-between items-center text-sm bg-white p-2 rounded">
                                <div>
                                  <span className="font-medium">{formatDate(pago.fecha)}</span>
                                  <span className="mx-2">-</span>
                                  <span className="text-gray-600">
                                    {FORMAS_PAGO.find(f => f.value === pago.forma_pago)?.label}
                                  </span>
                                  {pago.es_retencion && (
                                    <span className="ml-2 text-xs bg-blue-100 text-blue-700 px-1 rounded">
                                      Retención
                                    </span>
                                  )}
                                </div>
                                <span className="font-bold text-green-600">
                                  ${formatNumber(pago.monto, 2)}
                                </span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Modal Crear Factura */}
      {showCrearFactura && (
        <CrearFacturaModal
          clientes={clientes}
          onClose={() => setShowCrearFactura(false)}
          onSuccess={() => {
            setShowCrearFactura(false)
            queryClient.invalidateQueries({ queryKey: ['facturas'] })
            queryClient.invalidateQueries({ queryKey: ['facturas-pendientes'] })
          }}
        />
      )}

      {/* Modal Pago */}
      {showPagoModal && facturaSeleccionada && (
        <PagoFacturaModal
          factura={facturaSeleccionada}
          onClose={() => {
            setShowPagoModal(false)
            setFacturaSeleccionada(null)
          }}
          onSuccess={() => {
            setShowPagoModal(false)
            setFacturaSeleccionada(null)
            queryClient.invalidateQueries({ queryKey: ['facturas'] })
            queryClient.invalidateQueries({ queryKey: ['facturas-pendientes'] })
          }}
        />
      )}
    </div>
  )
}

// Modal para crear factura
function CrearFacturaModal({
  clientes,
  onClose,
  onSuccess
}: {
  clientes: any[]
  onClose: () => void
  onSuccess: () => void
}) {
  const [empresaId, setEmpresaId] = useState('')
  const [tipoComprobante, setTipoComprobante] = useState('factura_b')
  const [fechaEmision, setFechaEmision] = useState(new Date().toISOString().split('T')[0])
  const [remitosSeleccionados, setRemitosSeleccionados] = useState<string[]>([])
  const [subtotal, setSubtotal] = useState(0)
  const [iva21, setIva21] = useState(0)
  const [total, setTotal] = useState(0)
  const [observaciones, setObservaciones] = useState('')

  // Query remitos pendientes
  const { data: remitosPendientes = [] } = useQuery({
    queryKey: ['remitos-pendientes', empresaId],
    queryFn: () => facturacionService.getRemitosPendientesCliente(empresaId, true, true),
    enabled: !!empresaId,
  })

  // Mutation
  const mutation = useMutation({
    mutationFn: () => facturacionService.crearFactura({
      empresa_id: empresaId,
      tipo_comprobante: tipoComprobante,
      fecha_emision: fechaEmision,
      subtotal,
      iva_21: iva21,
      total,
      remito_ids: remitosSeleccionados,
      observaciones,
    }),
    onSuccess,
  })

  // Calcular totales cuando cambian los remitos seleccionados
  const handleToggleRemito = (remitoId: string, _importe: number) => {
    let nuevosSeleccionados: string[]
    if (remitosSeleccionados.includes(remitoId)) {
      nuevosSeleccionados = remitosSeleccionados.filter(id => id !== remitoId)
    } else {
      nuevosSeleccionados = [...remitosSeleccionados, remitoId]
    }
    setRemitosSeleccionados(nuevosSeleccionados)

    // Recalcular totales
    const nuevoSubtotal = remitosPendientes
      .filter(r => nuevosSeleccionados.includes(r.id))
      .reduce((sum, r) => sum + (r.importe || 0), 0)

    setSubtotal(nuevoSubtotal)
    const nuevoIva = tipoComprobante.includes('_a') ? nuevoSubtotal * 0.21 : 0
    setIva21(nuevoIva)
    setTotal(nuevoSubtotal + nuevoIva)
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!empresaId) {
      alert('Seleccione un cliente')
      return
    }
    if (total <= 0) {
      alert('El total debe ser mayor a 0')
      return
    }
    mutation.mutate()
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4 overflow-y-auto">
      <Card className="w-full max-w-3xl my-8">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5 text-blue-600" />
              Nueva Factura
            </CardTitle>
            <Button variant="ghost" size="sm" onClick={onClose}>
              <X className="h-4 w-4" />
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Cliente y tipo */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">Cliente *</label>
                <select
                  value={empresaId}
                  onChange={(e) => {
                    setEmpresaId(e.target.value)
                    setRemitosSeleccionados([])
                    setSubtotal(0)
                    setIva21(0)
                    setTotal(0)
                  }}
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  required
                >
                  <option value="">Seleccionar cliente</option>
                  {clientes.map((c) => (
                    <option key={c.id} value={c.id}>{c.nombre}</option>
                  ))}
                </select>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">Tipo de Comprobante *</label>
                <select
                  value={tipoComprobante}
                  onChange={(e) => setTipoComprobante(e.target.value)}
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                >
                  {TIPOS_COMPROBANTE.filter(t =>
                    t.value.startsWith('factura') || t.value === 'recibo'
                  ).map((t) => (
                    <option key={t.value} value={t.value}>{t.label}</option>
                  ))}
                </select>
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Fecha de Emisión *</label>
              <Input
                type="date"
                value={fechaEmision}
                onChange={(e) => setFechaEmision(e.target.value)}
              />
            </div>

            {/* Remitos pendientes */}
            {empresaId && (
              <div className="space-y-2">
                <label className="text-sm font-medium">Remitos a Incluir</label>
                {remitosPendientes.length === 0 ? (
                  <div className="text-sm text-gray-500 p-4 bg-gray-50 rounded-lg text-center">
                    <AlertCircle className="h-8 w-8 mx-auto mb-2 opacity-50" />
                    No hay remitos pendientes de facturar
                  </div>
                ) : (
                  <div className="border rounded-lg max-h-60 overflow-y-auto">
                    {remitosPendientes.map((remito) => (
                      <label
                        key={remito.id}
                        className={`flex items-center justify-between p-3 border-b last:border-b-0 cursor-pointer hover:bg-gray-50 ${
                          remitosSeleccionados.includes(remito.id) ? 'bg-blue-50' : ''
                        }`}
                      >
                        <div className="flex items-center gap-3">
                          <input
                            type="checkbox"
                            checked={remitosSeleccionados.includes(remito.id)}
                            onChange={() => handleToggleRemito(remito.id, remito.importe)}
                            className="rounded"
                          />
                          <div>
                            <p className="font-medium text-sm">Remito #{remito.numero_remito}</p>
                            <p className="text-xs text-gray-500">
                              {formatDate(remito.fecha)} - {remito.producto} - {remito.peso_neto} kg
                            </p>
                          </div>
                        </div>
                        <span className="font-bold">${formatNumber(remito.importe, 2)}</span>
                      </label>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Totales */}
            <div className="bg-gray-50 p-4 rounded-lg space-y-2">
              <div className="flex justify-between text-sm">
                <span>Subtotal:</span>
                <span>${formatNumber(subtotal, 2)}</span>
              </div>
              {tipoComprobante.includes('_a') && (
                <div className="flex justify-between text-sm">
                  <span>IVA 21%:</span>
                  <span>${formatNumber(iva21, 2)}</span>
                </div>
              )}
              <div className="flex justify-between font-bold text-lg pt-2 border-t">
                <span>TOTAL:</span>
                <span>${formatNumber(total, 2)}</span>
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Observaciones</label>
              <Input
                value={observaciones}
                onChange={(e) => setObservaciones(e.target.value)}
                placeholder="Observaciones opcionales"
              />
            </div>

            <div className="flex gap-2 pt-4">
              <Button type="submit" disabled={mutation.isPending} className="flex-1">
                {mutation.isPending ? 'Guardando...' : 'Crear Factura'}
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

// Modal para pago de factura
function PagoFacturaModal({
  factura,
  onClose,
  onSuccess
}: {
  factura: Factura
  onClose: () => void
  onSuccess: () => void
}) {
  const [monto, setMonto] = useState(factura.saldo_pendiente.toString())
  const [fecha, setFecha] = useState(new Date().toISOString().split('T')[0])
  const [formaPago, setFormaPago] = useState('transferencia')
  const [banco, setBanco] = useState('')
  const [numeroCheque, setNumeroCheque] = useState('')
  const [fechaCheque, setFechaCheque] = useState('')
  const [esRetencion, setEsRetencion] = useState(false)
  const [tipoRetencion] = useState('')
  const [numeroCertificado, setNumeroCertificado] = useState('')
  const [referencia, setReferencia] = useState('')
  const [registrarEnCC, setRegistrarEnCC] = useState(true)

  const mutation = useMutation({
    mutationFn: () => facturacionService.registrarPagoFactura(
      factura.id,
      {
        fecha,
        monto: parseFloat(monto),
        forma_pago: formaPago,
        banco: banco || undefined,
        numero_cheque: numeroCheque || undefined,
        fecha_cheque: fechaCheque || undefined,
        es_retencion: esRetencion,
        tipo_retencion: esRetencion ? tipoRetencion : undefined,
        numero_certificado: numeroCertificado || undefined,
        referencia: referencia || undefined,
      },
      registrarEnCC
    ),
    onSuccess,
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!monto || parseFloat(monto) <= 0) {
      alert('Ingrese un monto válido')
      return
    }
    if (parseFloat(monto) > factura.saldo_pendiente) {
      alert('El monto no puede superar el saldo pendiente')
      return
    }
    mutation.mutate()
  }

  const esCheque = formaPago === 'cheque' || formaPago === 'e_cheque'

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
          <p className="text-sm text-gray-500">
            Factura: {factura.numero_factura}
          </p>
          <p className="text-sm font-medium">
            Saldo pendiente: <span className="text-red-600">${formatNumber(factura.saldo_pendiente, 2)}</span>
          </p>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">Monto *</label>
                <Input
                  type="number"
                  step="0.01"
                  value={monto}
                  onChange={(e) => setMonto(e.target.value)}
                  max={factura.saldo_pendiente}
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
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Forma de Pago *</label>
              <select
                value={formaPago}
                onChange={(e) => {
                  setFormaPago(e.target.value)
                  setEsRetencion(e.target.value.startsWith('retencion'))
                }}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              >
                {FORMAS_PAGO.map((f) => (
                  <option key={f.value} value={f.value}>{f.label}</option>
                ))}
              </select>
            </div>

            {esCheque && (
              <>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Banco</label>
                    <Input
                      value={banco}
                      onChange={(e) => setBanco(e.target.value)}
                      placeholder="Nombre del banco"
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Nº Cheque</label>
                    <Input
                      value={numeroCheque}
                      onChange={(e) => setNumeroCheque(e.target.value)}
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Fecha de Cobro</label>
                  <Input
                    type="date"
                    value={fechaCheque}
                    onChange={(e) => setFechaCheque(e.target.value)}
                  />
                </div>
              </>
            )}

            {esRetencion && (
              <div className="space-y-2">
                <label className="text-sm font-medium">Nº Certificado Retención</label>
                <Input
                  value={numeroCertificado}
                  onChange={(e) => setNumeroCertificado(e.target.value)}
                  placeholder="Número de certificado"
                />
              </div>
            )}

            {formaPago === 'transferencia' && (
              <div className="space-y-2">
                <label className="text-sm font-medium">Referencia/Nº Transferencia</label>
                <Input
                  value={referencia}
                  onChange={(e) => setReferencia(e.target.value)}
                />
              </div>
            )}

            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="registrarCC"
                checked={registrarEnCC}
                onChange={(e) => setRegistrarEnCC(e.target.checked)}
                className="rounded"
              />
              <label htmlFor="registrarCC" className="text-sm">
                Registrar en Cuenta Corriente
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
