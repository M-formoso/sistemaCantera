import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  ClipboardList, Plus, Calendar, Truck, Package,
  CheckCircle, Clock, XCircle, ChevronRight, X,
  AlertCircle
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { ordenEntregaService, OrdenEntregaCreate } from '@/services/ordenEntregaService'
import { empresasService } from '@/services/empresasService'
import { formatDate, formatNumber } from '@/lib/utils'

const MATERIALES = ['10.30', '6.19', '0.20', '6.12', 'relleno', 'binder', '0.6']

export default function OrdenesEntregaTab() {
  const queryClient = useQueryClient()
  const [showModal, setShowModal] = useState(false)
  const [selectedOrden, setSelectedOrden] = useState<string | null>(null)
  const [filtroEstado, setFiltroEstado] = useState<string>('pendientes')

  // Queries
  const { data: ordenesPendientes = [] } = useQuery({
    queryKey: ['ordenes-pendientes'],
    queryFn: () => ordenEntregaService.getOrdenesPendientes(),
  })

  const { data: todasOrdenes = [] } = useQuery({
    queryKey: ['ordenes-todas'],
    queryFn: () => ordenEntregaService.getOrdenes(),
  })

  const { data: ordenDetalle } = useQuery({
    queryKey: ['orden-detalle', selectedOrden],
    queryFn: () => ordenEntregaService.getOrdenConPesajes(selectedOrden!),
    enabled: !!selectedOrden,
  })

  const { data: clientes = [] } = useQuery({
    queryKey: ['empresas-clientes'],
    queryFn: () => empresasService.getAll('cliente'),
  })

  // Mutations
  const crearMutation = useMutation({
    mutationFn: (data: OrdenEntregaCreate) => ordenEntregaService.crearOrden(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ordenes-pendientes'] })
      queryClient.invalidateQueries({ queryKey: ['ordenes-todas'] })
      setShowModal(false)
    },
  })

  const completarMutation = useMutation({
    mutationFn: (id: string) => ordenEntregaService.completarOrden(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ordenes-pendientes'] })
      queryClient.invalidateQueries({ queryKey: ['ordenes-todas'] })
      queryClient.invalidateQueries({ queryKey: ['orden-detalle'] })
    },
  })

  const cancelarMutation = useMutation({
    mutationFn: (id: string) => ordenEntregaService.cancelarOrden(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ordenes-pendientes'] })
      queryClient.invalidateQueries({ queryKey: ['ordenes-todas'] })
      setSelectedOrden(null)
    },
  })

  // Estadísticas
  const ordenesActivas = ordenesPendientes.length
  const cargasPendientes = ordenesPendientes.reduce((sum, o) => sum + (o.cargas_pendientes || 0), 0)
  const ordenesCompletadasHoy = todasOrdenes.filter(
    o => o.estado === 'completada' && o.fecha_entrega === new Date().toISOString().split('T')[0]
  ).length

  const ordenesMostrar = filtroEstado === 'pendientes' ? ordenesPendientes : todasOrdenes

  const getEstadoBadge = (estado: string) => {
    switch (estado) {
      case 'pendiente':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-1 bg-yellow-100 text-yellow-700 text-xs font-medium rounded">
            <Clock className="h-3 w-3" />
            Pendiente
          </span>
        )
      case 'en_proceso':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-1 bg-blue-100 text-blue-700 text-xs font-medium rounded">
            <Truck className="h-3 w-3" />
            En Proceso
          </span>
        )
      case 'completada':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-1 bg-green-100 text-green-700 text-xs font-medium rounded">
            <CheckCircle className="h-3 w-3" />
            Completada
          </span>
        )
      case 'cancelada':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-1 bg-red-100 text-red-700 text-xs font-medium rounded">
            <XCircle className="h-3 w-3" />
            Cancelada
          </span>
        )
      default:
        return null
    }
  }

  return (
    <div className="space-y-6">
      {/* Header con botón */}
      <div className="flex justify-between items-center">
        <div className="flex gap-2">
          <Button
            variant={filtroEstado === 'pendientes' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setFiltroEstado('pendientes')}
          >
            Pendientes ({ordenesPendientes.length})
          </Button>
          <Button
            variant={filtroEstado === 'todas' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setFiltroEstado('todas')}
          >
            Todas
          </Button>
        </div>
        <Button onClick={() => setShowModal(true)}>
          <Plus className="h-4 w-4 mr-2" />
          Nueva Orden
        </Button>
      </div>

      {/* Estadísticas */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Órdenes Activas</div>
            <div className="text-2xl font-bold text-blue-600">{ordenesActivas}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Cargas Pendientes</div>
            <div className="text-2xl font-bold text-orange-600">{cargasPendientes}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Completadas Hoy</div>
            <div className="text-2xl font-bold text-green-600">{ordenesCompletadasHoy}</div>
          </CardContent>
        </Card>
      </div>

      {/* Lista y Detalle */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Lista de órdenes */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <ClipboardList className="h-5 w-5" />
              Órdenes de Entrega
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 max-h-[600px] overflow-y-auto">
            {ordenesMostrar.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <Package className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>No hay órdenes {filtroEstado === 'pendientes' ? 'pendientes' : ''}</p>
              </div>
            ) : (
              ordenesMostrar.map((orden) => (
                <button
                  key={orden.id}
                  onClick={() => setSelectedOrden(orden.id)}
                  className={`w-full p-4 rounded-lg text-left transition-all border-2 ${
                    selectedOrden === orden.id
                      ? 'bg-blue-50 border-blue-500'
                      : 'bg-white hover:bg-gray-50 border-gray-200'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-bold text-lg">#{orden.numero_orden}</span>
                        {getEstadoBadge(orden.estado)}
                      </div>
                      <p className="font-medium text-gray-800">
                        {orden.cliente_nombre_completo || orden.cliente_nombre || 'Sin cliente'}
                      </p>
                      <div className="flex items-center gap-4 mt-2 text-sm text-gray-500">
                        <span className="flex items-center gap-1">
                          <Calendar className="h-3 w-3" />
                          {formatDate(orden.fecha_entrega)}
                        </span>
                        <span className="flex items-center gap-1">
                          <Package className="h-3 w-3" />
                          {orden.material}
                        </span>
                      </div>
                      {orden.solicitante && (
                        <p className="text-xs text-gray-400 mt-1">
                          Solicitado por: {orden.solicitante}
                        </p>
                      )}
                    </div>
                    <div className="text-right">
                      <div className="text-2xl font-bold">
                        {orden.cargas_entregadas}/{orden.cantidad_cargas}
                      </div>
                      <div className="text-xs text-gray-500">cargas</div>
                      {orden.cargas_pendientes && orden.cargas_pendientes > 0 && (
                        <div className="text-xs text-orange-600 font-medium mt-1">
                          {orden.cargas_pendientes} pendientes
                        </div>
                      )}
                    </div>
                  </div>
                  {/* Barra de progreso */}
                  <div className="mt-3 h-2 bg-gray-200 rounded-full overflow-hidden">
                    <div
                      className={`h-full transition-all ${
                        orden.estado === 'completada' ? 'bg-green-500' :
                        orden.estado === 'cancelada' ? 'bg-red-500' : 'bg-blue-500'
                      }`}
                      style={{ width: `${orden.porcentaje_completado || 0}%` }}
                    />
                  </div>
                </button>
              ))
            )}
          </CardContent>
        </Card>

        {/* Detalle de orden */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">
              {ordenDetalle ? `Detalle Orden #${ordenDetalle.numero_orden}` : 'Seleccione una orden'}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {!selectedOrden ? (
              <div className="text-center py-12 text-gray-500">
                <ChevronRight className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>Seleccione una orden para ver el detalle</p>
              </div>
            ) : ordenDetalle ? (
              <div className="space-y-6">
                {/* Info general */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-xs text-gray-500">Cliente</p>
                    <p className="font-medium">
                      {ordenDetalle.cliente_nombre_completo || ordenDetalle.cliente_nombre || '-'}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">Material</p>
                    <p className="font-medium">{ordenDetalle.material}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">Fecha Entrega</p>
                    <p className="font-medium">{formatDate(ordenDetalle.fecha_entrega)}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">Solicitante</p>
                    <p className="font-medium">{ordenDetalle.solicitante || '-'}</p>
                  </div>
                </div>

                {/* Progreso */}
                <div className="bg-gray-50 p-4 rounded-lg">
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-sm font-medium">Progreso de Entregas</span>
                    <span className="text-sm font-bold">
                      {ordenDetalle.cargas_entregadas} / {ordenDetalle.cantidad_cargas} cargas
                    </span>
                  </div>
                  <div className="h-3 bg-gray-200 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-blue-500 transition-all"
                      style={{ width: `${ordenDetalle.porcentaje_completado || 0}%` }}
                    />
                  </div>
                  {ordenDetalle.peso_total_entregado && ordenDetalle.peso_total_entregado > 0 && (
                    <p className="text-xs text-gray-500 mt-2">
                      Peso total entregado: {formatNumber(ordenDetalle.peso_total_entregado / 1000, 2)} t
                    </p>
                  )}
                </div>

                {/* Pesajes asociados */}
                <div>
                  <h4 className="font-medium mb-3">Pesajes/Remitos Asociados</h4>
                  {ordenDetalle.pesajes && ordenDetalle.pesajes.length > 0 ? (
                    <div className="space-y-2 max-h-[200px] overflow-y-auto">
                      {ordenDetalle.pesajes.map((pesaje) => (
                        <div key={pesaje.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                          <div>
                            <p className="font-medium">Pesaje #{pesaje.numero_pesaje}</p>
                            <p className="text-xs text-gray-500">
                              {formatDate(pesaje.fecha)} - {pesaje.patente || '-'}
                            </p>
                          </div>
                          <div className="text-right">
                            <p className="font-bold text-green-600">
                              {formatNumber(pesaje.peso_neto / 1000, 2)} t
                            </p>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-4 text-gray-400 text-sm">
                      <AlertCircle className="h-8 w-8 mx-auto mb-2 opacity-50" />
                      No hay pesajes asociados aún
                    </div>
                  )}
                </div>

                {/* Observaciones */}
                {ordenDetalle.observaciones && (
                  <div>
                    <p className="text-xs text-gray-500">Observaciones</p>
                    <p className="text-sm">{ordenDetalle.observaciones}</p>
                  </div>
                )}

                {/* Acciones */}
                {ordenDetalle.estado !== 'completada' && ordenDetalle.estado !== 'cancelada' && (
                  <div className="flex gap-2 pt-4 border-t">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        if (window.confirm('¿Marcar esta orden como completada?')) {
                          completarMutation.mutate(ordenDetalle.id)
                        }
                      }}
                      disabled={completarMutation.isPending}
                    >
                      <CheckCircle className="h-4 w-4 mr-1" />
                      Completar
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      className="text-red-600 hover:text-red-700"
                      onClick={() => {
                        if (window.confirm('¿Cancelar esta orden?')) {
                          cancelarMutation.mutate(ordenDetalle.id)
                        }
                      }}
                      disabled={cancelarMutation.isPending}
                    >
                      <XCircle className="h-4 w-4 mr-1" />
                      Cancelar
                    </Button>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">Cargando...</div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Modal Nueva Orden */}
      {showModal && (
        <NuevaOrdenModal
          clientes={clientes}
          onClose={() => setShowModal(false)}
          onSubmit={async (data) => {
            await crearMutation.mutateAsync(data)
          }}
          isLoading={crearMutation.isPending}
        />
      )}
    </div>
  )
}

// Modal para crear nueva orden
function NuevaOrdenModal({
  clientes,
  onClose,
  onSubmit,
  isLoading
}: {
  clientes: any[]
  onClose: () => void
  onSubmit: (data: OrdenEntregaCreate) => Promise<void>
  isLoading: boolean
}) {
  const [formData, setFormData] = useState<OrdenEntregaCreate>({
    fecha_entrega: new Date().toISOString().split('T')[0],
    material: '',
    cantidad_cargas: 1,
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!formData.material) {
      alert('Seleccione un material')
      return
    }
    if (formData.cantidad_cargas < 1) {
      alert('Ingrese al menos 1 carga')
      return
    }
    await onSubmit(formData)
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <Card className="w-full max-w-lg max-h-[90vh] overflow-y-auto">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <ClipboardList className="h-5 w-5" />
              Nueva Orden de Entrega
            </CardTitle>
            <Button variant="ghost" size="sm" onClick={onClose}>
              <X className="h-4 w-4" />
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Fecha de entrega */}
            <div>
              <label className="text-sm font-medium mb-1 block">Fecha de Entrega *</label>
              <Input
                type="date"
                value={formData.fecha_entrega}
                onChange={(e) => setFormData({ ...formData, fecha_entrega: e.target.value })}
                required
              />
            </div>

            {/* Cliente */}
            <div>
              <label className="text-sm font-medium mb-1 block">Cliente</label>
              <select
                value={formData.cliente_id || ''}
                onChange={(e) => setFormData({
                  ...formData,
                  cliente_id: e.target.value || undefined,
                  cliente_nombre: e.target.value ? undefined : formData.cliente_nombre
                })}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              >
                <option value="">Seleccionar cliente...</option>
                {clientes.map((c) => (
                  <option key={c.id} value={c.id}>{c.nombre}</option>
                ))}
              </select>
            </div>

            {/* Cliente nombre libre */}
            {!formData.cliente_id && (
              <div>
                <label className="text-sm font-medium mb-1 block">O escribir nombre</label>
                <Input
                  value={formData.cliente_nombre || ''}
                  onChange={(e) => setFormData({ ...formData, cliente_nombre: e.target.value })}
                  placeholder="Nombre del cliente"
                />
              </div>
            )}

            {/* Material */}
            <div>
              <label className="text-sm font-medium mb-1 block">Material *</label>
              <select
                value={formData.material}
                onChange={(e) => setFormData({ ...formData, material: e.target.value })}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                required
              >
                <option value="">Seleccionar material...</option>
                {MATERIALES.map((m) => (
                  <option key={m} value={m}>{m}</option>
                ))}
              </select>
            </div>

            {/* Cantidad de cargas */}
            <div>
              <label className="text-sm font-medium mb-1 block">Cantidad de Cargas *</label>
              <Input
                type="number"
                min="1"
                value={formData.cantidad_cargas}
                onChange={(e) => setFormData({ ...formData, cantidad_cargas: parseInt(e.target.value) || 1 })}
                required
              />
            </div>

            {/* Solicitante */}
            <div>
              <label className="text-sm font-medium mb-1 block">Solicitado por</label>
              <Input
                value={formData.solicitante || ''}
                onChange={(e) => setFormData({ ...formData, solicitante: e.target.value })}
                placeholder="Ej: Martín, Vero..."
              />
            </div>

            {/* Dirección */}
            <div>
              <label className="text-sm font-medium mb-1 block">Dirección de Entrega</label>
              <Input
                value={formData.direccion_entrega || ''}
                onChange={(e) => setFormData({ ...formData, direccion_entrega: e.target.value })}
                placeholder="Dirección..."
              />
            </div>

            {/* Observaciones */}
            <div>
              <label className="text-sm font-medium mb-1 block">Observaciones</label>
              <textarea
                value={formData.observaciones || ''}
                onChange={(e) => setFormData({ ...formData, observaciones: e.target.value })}
                rows={2}
                placeholder="Notas adicionales..."
                className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              />
            </div>

            {/* Botones */}
            <div className="flex gap-2 pt-4">
              <Button type="submit" disabled={isLoading} className="flex-1">
                {isLoading ? 'Guardando...' : 'Crear Orden'}
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
