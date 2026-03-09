import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  DollarSign,
  TrendingUp,
  TrendingDown,
  Plus,
  Filter,
  Building2,
  Truck,
  FileText,
  X
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { finanzasService } from '@/services/finanzasService'
import { camionesService } from '@/services/camionesService'
import { empresasService } from '@/services/empresasService'
import { formatNumber, formatDate, getTodayLocalDate } from '@/lib/utils'
import { MovimientoFinancieroCreate, TipoMovimiento } from '@/types'

export default function MovimientosTab() {
  const queryClient = useQueryClient()
  const [showModal, setShowModal] = useState(false)
  const [tipoFiltro, setTipoFiltro] = useState<TipoMovimiento | ''>('')
  const [fechaDesde, setFechaDesde] = useState('')
  const [fechaHasta, setFechaHasta] = useState('')

  // Form state
  const [formData, setFormData] = useState<MovimientoFinancieroCreate>({
    tipo: 'ingreso',
    fecha: getTodayLocalDate(),
    monto: 0,
    descripcion: '',
    estado: 'completado'
  })

  // Queries
  const { data: resumen } = useQuery({
    queryKey: ['finanzas-resumen', fechaDesde, fechaHasta],
    queryFn: () => finanzasService.getResumen(fechaDesde || undefined, fechaHasta || undefined)
  })

  const { data: movimientos = [], isLoading } = useQuery({
    queryKey: ['finanzas-movimientos', tipoFiltro, fechaDesde, fechaHasta],
    queryFn: () => finanzasService.getMovimientos({
      tipo: tipoFiltro || undefined,
      fecha_desde: fechaDesde || undefined,
      fecha_hasta: fechaHasta || undefined,
      limit: 100
    })
  })

  const { data: categorias = [] } = useQuery({
    queryKey: ['finanzas-categorias'],
    queryFn: () => finanzasService.getCategorias()
  })

  const { data: camiones = [] } = useQuery({
    queryKey: ['camiones'],
    queryFn: () => camionesService.getAll(true)
  })

  const { data: empresas = [] } = useQuery({
    queryKey: ['empresas'],
    queryFn: () => empresasService.getAll()
  })

  const createMutation = useMutation({
    mutationFn: (data: MovimientoFinancieroCreate) => finanzasService.createMovimiento(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['finanzas-movimientos'] })
      queryClient.invalidateQueries({ queryKey: ['finanzas-resumen'] })
      setShowModal(false)
      resetForm()
    }
  })

  const resetForm = () => {
    setFormData({
      tipo: 'ingreso',
      fecha: getTodayLocalDate(),
      monto: 0,
      descripcion: '',
      estado: 'completado'
    })
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await createMutation.mutateAsync(formData)
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Error al guardar')
    }
  }

  const categoriasIngreso = categorias.filter(c => c.tipo === 'ingreso')
  const categoriasEgreso = categorias.filter(c => c.tipo === 'egreso')

  return (
    <div className="space-y-6">
      {/* Header con botón */}
      <div className="flex justify-end">
        <Button onClick={() => setShowModal(true)}>
          <Plus className="h-4 w-4 mr-2" />
          Nuevo Movimiento
        </Button>
      </div>

      {/* Resumen Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-gray-500">
              Total Ingresos
            </CardTitle>
            <TrendingUp className="h-5 w-5 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              ${formatNumber(resumen?.total_ingresos || 0)}
            </div>
            <p className="text-xs text-gray-500 mt-1">
              {resumen?.cantidad_ingresos || 0} movimientos
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-gray-500">
              Total Egresos
            </CardTitle>
            <TrendingDown className="h-5 w-5 text-red-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">
              ${formatNumber(resumen?.total_egresos || 0)}
            </div>
            <p className="text-xs text-gray-500 mt-1">
              {resumen?.cantidad_egresos || 0} movimientos
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-gray-500">
              Balance
            </CardTitle>
            <DollarSign className="h-5 w-5 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${(resumen?.balance || 0) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              ${formatNumber(resumen?.balance || 0)}
            </div>
            <p className="text-xs text-gray-500 mt-1">
              Período seleccionado
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Filtros */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Filter className="h-5 w-5" />
            Filtros
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="text-sm font-medium mb-1 block">Tipo</label>
              <select
                value={tipoFiltro}
                onChange={(e) => setTipoFiltro(e.target.value as TipoMovimiento | '')}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              >
                <option value="">Todos</option>
                <option value="ingreso">Ingresos</option>
                <option value="egreso">Egresos</option>
              </select>
            </div>
            <div>
              <label className="text-sm font-medium mb-1 block">Desde</label>
              <Input
                type="date"
                value={fechaDesde}
                onChange={(e) => setFechaDesde(e.target.value)}
              />
            </div>
            <div>
              <label className="text-sm font-medium mb-1 block">Hasta</label>
              <Input
                type="date"
                value={fechaHasta}
                onChange={(e) => setFechaHasta(e.target.value)}
              />
            </div>
            <div className="flex items-end">
              <Button
                variant="outline"
                onClick={() => {
                  setTipoFiltro('')
                  setFechaDesde('')
                  setFechaHasta('')
                }}
              >
                Limpiar
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Tabla de Movimientos */}
      <Card>
        <CardHeader>
          <CardTitle>Movimientos</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="text-center py-8 text-gray-500">Cargando...</div>
          ) : movimientos.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              No hay movimientos registrados
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-3 px-2 font-medium">Fecha</th>
                    <th className="text-left py-3 px-2 font-medium">Tipo</th>
                    <th className="text-left py-3 px-2 font-medium">Categoría</th>
                    <th className="text-left py-3 px-2 font-medium">Descripción</th>
                    <th className="text-left py-3 px-2 font-medium">Referencia</th>
                    <th className="text-right py-3 px-2 font-medium">Monto</th>
                  </tr>
                </thead>
                <tbody>
                  {movimientos.map((mov) => (
                    <tr key={mov.id} className="border-b hover:bg-gray-50">
                      <td className="py-3 px-2">{formatDate(mov.fecha)}</td>
                      <td className="py-3 px-2">
                        <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                          mov.tipo === 'ingreso'
                            ? 'bg-green-100 text-green-800'
                            : 'bg-red-100 text-red-800'
                        }`}>
                          {mov.tipo === 'ingreso' ? (
                            <TrendingUp className="h-3 w-3 mr-1" />
                          ) : (
                            <TrendingDown className="h-3 w-3 mr-1" />
                          )}
                          {mov.tipo}
                        </span>
                      </td>
                      <td className="py-3 px-2">{mov.categoria_nombre || '-'}</td>
                      <td className="py-3 px-2 max-w-xs truncate">{mov.descripcion}</td>
                      <td className="py-3 px-2">
                        <div className="text-sm">
                          {mov.camion_identificador && (
                            <span className="flex items-center gap-1 text-gray-600">
                              <Truck className="h-3 w-3" />
                              {mov.camion_identificador}
                            </span>
                          )}
                          {mov.empresa_nombre && (
                            <span className="flex items-center gap-1 text-gray-600">
                              <Building2 className="h-3 w-3" />
                              {mov.empresa_nombre}
                            </span>
                          )}
                          {mov.numero_comprobante && (
                            <span className="flex items-center gap-1 text-gray-600">
                              <FileText className="h-3 w-3" />
                              {mov.numero_comprobante}
                            </span>
                          )}
                        </div>
                      </td>
                      <td className={`py-3 px-2 text-right font-medium ${
                        mov.tipo === 'ingreso' ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {mov.tipo === 'ingreso' ? '+' : '-'}${formatNumber(mov.monto)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Modal Nuevo Movimiento */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <Card className="w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Nuevo Movimiento</CardTitle>
                <Button variant="ghost" size="sm" onClick={() => setShowModal(false)}>
                  <X className="h-4 w-4" />
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-4">
                {/* Tipo */}
                <div className="flex gap-2">
                  <Button
                    type="button"
                    variant={formData.tipo === 'ingreso' ? 'default' : 'outline'}
                    className={`flex-1 ${formData.tipo === 'ingreso' ? 'bg-green-600 hover:bg-green-700' : ''}`}
                    onClick={() => setFormData({ ...formData, tipo: 'ingreso', categoria_id: undefined })}
                  >
                    <TrendingUp className="h-4 w-4 mr-2" />
                    Ingreso
                  </Button>
                  <Button
                    type="button"
                    variant={formData.tipo === 'egreso' ? 'default' : 'outline'}
                    className={`flex-1 ${formData.tipo === 'egreso' ? 'bg-red-600 hover:bg-red-700' : ''}`}
                    onClick={() => setFormData({ ...formData, tipo: 'egreso', categoria_id: undefined })}
                  >
                    <TrendingDown className="h-4 w-4 mr-2" />
                    Egreso
                  </Button>
                </div>

                {/* Fecha y Monto */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium mb-1 block">Fecha *</label>
                    <Input
                      type="date"
                      value={formData.fecha}
                      onChange={(e) => setFormData({ ...formData, fecha: e.target.value })}
                      required
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium mb-1 block">Monto *</label>
                    <Input
                      type="number"
                      step="0.01"
                      min="0.01"
                      value={formData.monto || ''}
                      onChange={(e) => setFormData({ ...formData, monto: parseFloat(e.target.value) || 0 })}
                      placeholder="0.00"
                      required
                    />
                  </div>
                </div>

                {/* Categoría */}
                <div>
                  <label className="text-sm font-medium mb-1 block">Categoría</label>
                  <select
                    value={formData.categoria_id || ''}
                    onChange={(e) => setFormData({ ...formData, categoria_id: e.target.value || undefined })}
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  >
                    <option value="">Seleccionar categoría</option>
                    {(formData.tipo === 'ingreso' ? categoriasIngreso : categoriasEgreso).map((cat) => (
                      <option key={cat.id} value={cat.id}>{cat.nombre}</option>
                    ))}
                  </select>
                </div>

                {/* Descripción */}
                <div>
                  <label className="text-sm font-medium mb-1 block">Descripción *</label>
                  <Input
                    value={formData.descripcion}
                    onChange={(e) => setFormData({ ...formData, descripcion: e.target.value })}
                    placeholder="Descripción del movimiento"
                    required
                  />
                </div>

                {/* Camión/Máquina */}
                <div>
                  <label className="text-sm font-medium mb-1 block">Camión/Máquina (opcional)</label>
                  <select
                    value={formData.camion_id || ''}
                    onChange={(e) => setFormData({ ...formData, camion_id: e.target.value || undefined })}
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  >
                    <option value="">Sin asignar</option>
                    {camiones.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.patente || c.nombre || c.codigo_interno}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Empresa */}
                <div>
                  <label className="text-sm font-medium mb-1 block">
                    {formData.tipo === 'ingreso' ? 'Cliente' : 'Proveedor'} (opcional)
                  </label>
                  <select
                    value={formData.empresa_id || ''}
                    onChange={(e) => setFormData({ ...formData, empresa_id: e.target.value || undefined })}
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  >
                    <option value="">Sin asignar</option>
                    {empresas.map((emp) => (
                      <option key={emp.id} value={emp.id}>{emp.nombre}</option>
                    ))}
                  </select>
                </div>

                {/* Comprobante */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium mb-1 block">Tipo Comprobante</label>
                    <select
                      value={formData.tipo_comprobante || ''}
                      onChange={(e) => setFormData({ ...formData, tipo_comprobante: e.target.value || undefined })}
                      className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                    >
                      <option value="">Seleccionar</option>
                      <option value="factura">Factura</option>
                      <option value="recibo">Recibo</option>
                      <option value="ticket">Ticket</option>
                      <option value="remito">Remito</option>
                      <option value="otro">Otro</option>
                    </select>
                  </div>
                  <div>
                    <label className="text-sm font-medium mb-1 block">N° Comprobante</label>
                    <Input
                      value={formData.numero_comprobante || ''}
                      onChange={(e) => setFormData({ ...formData, numero_comprobante: e.target.value || undefined })}
                      placeholder="0001-00000001"
                    />
                  </div>
                </div>

                {/* Método de pago */}
                <div>
                  <label className="text-sm font-medium mb-1 block">Método de Pago</label>
                  <select
                    value={formData.metodo_pago || ''}
                    onChange={(e) => setFormData({ ...formData, metodo_pago: e.target.value || undefined })}
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  >
                    <option value="">Seleccionar</option>
                    <option value="efectivo">Efectivo</option>
                    <option value="transferencia">Transferencia</option>
                    <option value="cheque">Cheque</option>
                    <option value="tarjeta">Tarjeta</option>
                  </select>
                </div>

                {/* Notas */}
                <div>
                  <label className="text-sm font-medium mb-1 block">Notas</label>
                  <textarea
                    value={formData.notas || ''}
                    onChange={(e) => setFormData({ ...formData, notas: e.target.value || undefined })}
                    rows={2}
                    placeholder="Notas adicionales..."
                    className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  />
                </div>

                {/* Botones */}
                <div className="flex justify-end gap-2 pt-4">
                  <Button type="button" variant="outline" onClick={() => setShowModal(false)}>
                    Cancelar
                  </Button>
                  <Button type="submit" disabled={createMutation.isPending}>
                    {createMutation.isPending ? 'Guardando...' : 'Guardar'}
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}
