import { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, Truck, Wrench, Calendar, Trash2, CalendarClock, AlertTriangle, Cog, Hammer, Plus, Package } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { camionesService } from '@/services/camionesService'
import { serviciosService } from '@/services/serviciosService'
import { trabajosService } from '@/services/trabajosService'
import { repuestosService } from '@/services/repuestosService'
import { formatDate, formatCurrency } from '@/lib/utils'
import { useIsAdmin } from '@/hooks/useIsAdmin'
import { Trabajo, Repuesto } from '@/types'

export default function CamionDetailPage() {
  const navigate = useNavigate()
  const { id } = useParams()
  const queryClient = useQueryClient()
  const isAdmin = useIsAdmin()
  const [showProximoServicio, setShowProximoServicio] = useState(false)
  const [proximoServicioFecha, setProximoServicioFecha] = useState('')
  const [proximoServicioKm, setProximoServicioKm] = useState('')
  const [proximoServicioHoras, setProximoServicioHoras] = useState('')

  // Estado para formulario de trabajo rápido
  const [showTrabajoForm, setShowTrabajoForm] = useState(false)
  const [trabajoDescripcion, setTrabajoDescripcion] = useState('')
  const [trabajoResponsable, setTrabajoResponsable] = useState('')
  const [trabajoCosto, setTrabajoCosto] = useState('')
  const [trabajoObservaciones, setTrabajoObservaciones] = useState('')
  const [trabajoRepuestos, setTrabajoRepuestos] = useState<{ repuesto_id: string; cantidad: number; nombre: string; precio: number }[]>([])

  const { data: camion, isLoading: isLoadingCamion } = useQuery({
    queryKey: ['camion', id],
    queryFn: () => camionesService.getById(id!),
  })

  const { data: servicios = [], isLoading: isLoadingServicios } = useQuery({
    queryKey: ['camion-servicios', id],
    queryFn: () => camionesService.getServicios(id!),
  })

  const { data: trabajos = [], isLoading: isLoadingTrabajos } = useQuery({
    queryKey: ['camion-trabajos', id],
    queryFn: () => trabajosService.getByEquipo(id!).catch(() => []),
    retry: false,
  })

  const { data: repuestosDisponibles = [] } = useQuery({
    queryKey: ['repuestos-equipo', id],
    queryFn: () => repuestosService.getByEquipo(id!, true).catch(() => []),
    enabled: showTrabajoForm,
    retry: false,
  })

  const deleteServicioMutation = useMutation({
    mutationFn: (servicioId: string) => serviciosService.delete(servicioId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['camion-servicios', id] })
      queryClient.invalidateQueries({ queryKey: ['camion', id] })
      queryClient.invalidateQueries({ queryKey: ['camiones'] })
    },
  })

  const createTrabajoMutation = useMutation({
    mutationFn: (data: any) => trabajosService.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['camion-trabajos', id] })
      queryClient.invalidateQueries({ queryKey: ['repuestos'] })
      resetTrabajoForm()
    },
  })

  const deleteTrabajoMutation = useMutation({
    mutationFn: (trabajoId: string) => trabajosService.delete(trabajoId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['camion-trabajos', id] })
    },
  })

  const resetTrabajoForm = () => {
    setShowTrabajoForm(false)
    setTrabajoDescripcion('')
    setTrabajoResponsable('')
    setTrabajoCosto('')
    setTrabajoObservaciones('')
    setTrabajoRepuestos([])
  }

  const agregarRepuestoTrabajo = (repuestoId: string) => {
    if (!repuestoId) return
    const repuesto = repuestosDisponibles.find((r: Repuesto) => r.id === repuestoId)
    if (!repuesto) return
    if (trabajoRepuestos.some(r => r.repuesto_id === repuestoId)) {
      alert('Este repuesto ya fue agregado')
      return
    }
    setTrabajoRepuestos([
      ...trabajoRepuestos,
      { repuesto_id: repuestoId, cantidad: 1, nombre: repuesto.nombre, precio: repuesto.precio_unitario }
    ])
  }

  const handleCrearTrabajo = async () => {
    if (!trabajoDescripcion.trim()) {
      alert('Ingrese una descripción')
      return
    }
    try {
      await createTrabajoMutation.mutateAsync({
        camion_id: id,
        fecha: new Date().toISOString().split('T')[0],
        descripcion: trabajoDescripcion,
        responsable: trabajoResponsable || undefined,
        costo_mano_obra: parseFloat(trabajoCosto) || 0,
        observaciones: trabajoObservaciones || undefined,
        repuestos: trabajoRepuestos.map(r => ({ repuesto_id: r.repuesto_id, cantidad: r.cantidad })),
      })
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Error al registrar el trabajo')
    }
  }

  const handleDeleteTrabajo = async (trabajoId: string) => {
    if (window.confirm('¿Está seguro de eliminar este trabajo?')) {
      try {
        await deleteTrabajoMutation.mutateAsync(trabajoId)
      } catch (error) {
        alert('Error al eliminar el trabajo')
      }
    }
  }

  const updateCamionMutation = useMutation({
    mutationFn: (data: { proximo_servicio_fecha?: string; proximo_servicio_km?: number; proximo_servicio_horas?: number }) =>
      camionesService.update(id!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['camion', id] })
      queryClient.invalidateQueries({ queryKey: ['camiones'] })
      setShowProximoServicio(false)
      setProximoServicioFecha('')
      setProximoServicioKm('')
      setProximoServicioHoras('')
    },
  })

  const handleDeleteServicio = async (servicioId: string) => {
    if (window.confirm('¿Está seguro de eliminar este servicio? Esta acción no se puede deshacer.')) {
      try {
        await deleteServicioMutation.mutateAsync(servicioId)
      } catch (error) {
        alert('Error al eliminar el servicio')
      }
    }
  }

  const handleGuardarProximoServicio = async () => {
    try {
      await updateCamionMutation.mutateAsync({
        proximo_servicio_fecha: proximoServicioFecha || undefined,
        proximo_servicio_km: proximoServicioKm ? parseInt(proximoServicioKm) : undefined,
        proximo_servicio_horas: proximoServicioHoras ? parseFloat(proximoServicioHoras) : undefined,
      })
    } catch (error) {
      alert('Error al guardar el próximo servicio')
    }
  }

  if (isLoadingCamion) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-gray-500">Cargando...</div>
      </div>
    )
  }

  if (!camion) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-gray-500">Equipo no encontrado</div>
      </div>
    )
  }

  const esMaquina = camion.categoria === 'maquina'
  const IconoEquipo = esMaquina ? Cog : Truck

  const estadoColorClass =
    camion.estado === 'operativo' ? 'bg-green-100 text-green-700' :
    camion.estado === 'en_servicio' ? 'bg-orange-100 text-orange-700' :
    'bg-red-100 text-red-700'

  // Para máquinas, calcular horas restantes
  const horasActuales = Number(camion.horometro_actual) || 0
  const proximoServicioHorasValue = Number(camion.proximo_servicio_horas) || 0
  const horasRestantes = proximoServicioHorasValue - horasActuales

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="outline" onClick={() => navigate('/camiones')}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Volver
        </Button>
        <div className="flex-1">
          <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
            <IconoEquipo className="h-8 w-8" />
            {camion.patente || camion.nombre || camion.codigo_interno}
          </h1>
          <p className="text-gray-500 mt-1">
            {camion.marca} {camion.modelo} {camion.año ? `- ${camion.año}` : ''}
          </p>
        </div>
        <Button onClick={() => navigate(`/camiones/${id}/editar`)}>
          Editar {esMaquina ? 'Máquina' : 'Camión'}
        </Button>
      </div>

      {/* Información del equipo */}
      <Card>
        <CardHeader>
          <CardTitle>Información {esMaquina ? 'de la Máquina' : 'del Camión'}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {!esMaquina && camion.patente && (
              <div>
                <p className="text-sm text-muted-foreground">Patente</p>
                <p className="text-lg font-semibold">{camion.patente}</p>
              </div>
            )}
            {esMaquina && (
              <div>
                <p className="text-sm text-muted-foreground">Nombre / Código</p>
                <p className="text-lg font-semibold">{camion.nombre || camion.codigo_interno}</p>
              </div>
            )}
            {esMaquina && camion.tipo_maquina && (
              <div>
                <p className="text-sm text-muted-foreground">Tipo</p>
                <p className="text-lg font-semibold capitalize">{camion.tipo_maquina.replace(/_/g, ' ')}</p>
              </div>
            )}
            <div>
              <p className="text-sm text-muted-foreground">Marca y Modelo</p>
              <p className="text-lg font-semibold">{camion.marca} {camion.modelo}</p>
            </div>
            {camion.año && (
              <div>
                <p className="text-sm text-muted-foreground">Año</p>
                <p className="text-lg font-semibold">{camion.año}</p>
              </div>
            )}
            {!esMaquina ? (
              <div>
                <p className="text-sm text-muted-foreground">Kilometraje Actual</p>
                <p className="text-lg font-semibold">{camion.kilometraje_actual != null ? `${camion.kilometraje_actual.toLocaleString('es-AR')} km` : '-'}</p>
              </div>
            ) : (
              <div>
                <p className="text-sm text-muted-foreground">Horómetro Actual</p>
                <p className="text-lg font-semibold">{horasActuales > 0 ? `${horasActuales.toLocaleString('es-AR')} hs` : '-'}</p>
              </div>
            )}
            <div>
              <p className="text-sm text-muted-foreground">Estado</p>
              <span className={`inline-flex px-3 py-1 text-sm font-semibold rounded-full ${estadoColorClass}`}>
                {camion.estado === 'operativo' ? 'Operativo' :
                 camion.estado === 'en_servicio' ? 'En servicio' :
                 'Fuera de servicio'}
              </span>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Último Servicio</p>
              <p className="text-lg font-semibold">
                {camion.ultimo_servicio ? formatDate(camion.ultimo_servicio) : 'Sin servicios'}
              </p>
            </div>
          </div>
          {camion.observaciones && (
            <div className="mt-6 pt-6 border-t">
              <p className="text-sm text-muted-foreground mb-2">Observaciones</p>
              <p className="text-sm">{camion.observaciones}</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Próximo Servicio Programado */}
      <Card className={camion.requiere_servicio ? 'border-orange-300 bg-orange-50' : ''}>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <CalendarClock className="h-5 w-5" />
                Próximo Servicio
                {camion.requiere_servicio && (
                  <AlertTriangle className="h-5 w-5 text-orange-500" />
                )}
              </CardTitle>
              <CardDescription>Programación del próximo mantenimiento</CardDescription>
            </div>
            <Button variant="outline" onClick={() => setShowProximoServicio(!showProximoServicio)}>
              {showProximoServicio ? 'Cancelar' : 'Programar Servicio'}
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {showProximoServicio ? (
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Fecha del próximo servicio</label>
                  <Input
                    type="date"
                    value={proximoServicioFecha}
                    onChange={(e) => setProximoServicioFecha(e.target.value)}
                  />
                  <p className="text-xs text-muted-foreground">Se alertará una semana antes</p>
                </div>
                {!esMaquina ? (
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Kilometraje del próximo servicio</label>
                    <Input
                      type="number"
                      placeholder={camion.kilometraje_actual ? `Ej: ${(camion.kilometraje_actual + 10000).toLocaleString()}` : ''}
                      value={proximoServicioKm}
                      onChange={(e) => setProximoServicioKm(e.target.value)}
                    />
                    <p className="text-xs text-muted-foreground">Se alertará cuando falten 1000 km</p>
                  </div>
                ) : (
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Horas del próximo servicio</label>
                    <Input
                      type="number"
                      step="0.5"
                      placeholder={horasActuales ? `Ej: ${(horasActuales + 250).toLocaleString()}` : ''}
                      value={proximoServicioHoras}
                      onChange={(e) => setProximoServicioHoras(e.target.value)}
                    />
                    <p className="text-xs text-muted-foreground">Se alertará cuando falten 50 horas</p>
                  </div>
                )}
              </div>
              <div className="flex gap-2">
                <Button onClick={handleGuardarProximoServicio} disabled={updateCamionMutation.isPending}>
                  {updateCamionMutation.isPending ? 'Guardando...' : 'Guardar'}
                </Button>
                <Button variant="outline" onClick={() => setShowProximoServicio(false)}>
                  Cancelar
                </Button>
              </div>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div>
                <p className="text-sm text-muted-foreground">Por Fecha</p>
                <p className="text-lg font-semibold">
                  {camion.proximo_servicio_fecha ? formatDate(camion.proximo_servicio_fecha) : 'No programado'}
                </p>
                {camion.proximo_servicio_fecha && (
                  <p className="text-xs text-muted-foreground">
                    {(() => {
                      const dias = Math.ceil((new Date(camion.proximo_servicio_fecha).getTime() - new Date().getTime()) / (1000 * 60 * 60 * 24))
                      if (dias < 0) return <span className="text-red-600 font-semibold">¡Vencido hace {Math.abs(dias)} días!</span>
                      if (dias <= 7) return <span className="text-orange-600 font-semibold">Faltan {dias} días</span>
                      return `Faltan ${dias} días`
                    })()}
                  </p>
                )}
              </div>
              {!esMaquina ? (
                <div>
                  <p className="text-sm text-muted-foreground">Por Kilometraje</p>
                  <p className="text-lg font-semibold">
                    {camion.proximo_servicio_km ? `${camion.proximo_servicio_km.toLocaleString('es-AR')} km` : 'No programado'}
                  </p>
                  {camion.km_para_proximo_servicio != null && (
                    <p className={`text-xs ${camion.km_para_proximo_servicio <= 0 ? 'text-red-600 font-semibold' : camion.km_para_proximo_servicio <= 1000 ? 'text-orange-600 font-semibold' : 'text-muted-foreground'}`}>
                      {camion.km_para_proximo_servicio <= 0
                        ? `¡Pasado por ${Math.abs(camion.km_para_proximo_servicio).toLocaleString('es-AR')} km!`
                        : `Faltan ${camion.km_para_proximo_servicio.toLocaleString('es-AR')} km`
                      }
                    </p>
                  )}
                </div>
              ) : (
                <div>
                  <p className="text-sm text-muted-foreground">Por Horas de Uso</p>
                  <p className="text-lg font-semibold">
                    {proximoServicioHorasValue > 0 ? `${proximoServicioHorasValue.toLocaleString('es-AR')} hs` : 'No programado'}
                  </p>
                  {proximoServicioHorasValue > 0 && (
                    <p className={`text-xs ${horasRestantes <= 0 ? 'text-red-600 font-semibold' : horasRestantes <= 50 ? 'text-orange-600 font-semibold' : 'text-muted-foreground'}`}>
                      {horasRestantes <= 0
                        ? `¡Pasado por ${Math.abs(horasRestantes).toLocaleString('es-AR')} hs!`
                        : `Faltan ${horasRestantes.toLocaleString('es-AR')} hs`
                      }
                    </p>
                  )}
                </div>
              )}
              <div>
                <p className="text-sm text-muted-foreground">Intervalo de Servicio</p>
                <p className="text-lg font-semibold">
                  {!esMaquina
                    ? (camion.intervalo_servicio_km ? `Cada ${camion.intervalo_servicio_km.toLocaleString('es-AR')} km` : 'No definido')
                    : (camion.intervalo_servicio_horas ? `Cada ${camion.intervalo_servicio_horas.toLocaleString('es-AR')} hs` : 'No definido')
                  }
                </p>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Historial de servicios */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Wrench className="h-5 w-5" />
                Historial de {esMaquina ? 'Mantenimientos' : 'Servicios'}
              </CardTitle>
              <CardDescription>
                {esMaquina
                  ? 'Trabajos y reparaciones realizados'
                  : 'Servicios realizados a este camión'}
              </CardDescription>
            </div>
            <Button onClick={() => navigate(`/servicios/nuevo?camion=${id}`)}>
              Registrar {esMaquina ? 'Mantenimiento' : 'Servicio'}
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {isLoadingServicios ? (
            <div className="text-center py-8 text-muted-foreground">
              Cargando servicios...
            </div>
          ) : servicios.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              No hay {esMaquina ? 'mantenimientos' : 'servicios'} registrados para {esMaquina ? 'esta máquina' : 'este camión'}
            </div>
          ) : (
            <div className="space-y-4">
              {servicios.map((servicio: any) => (
                <div
                  key={servicio.id}
                  className="border rounded-lg p-4 hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded ${
                          servicio.tipo === 'preventivo' ? 'bg-blue-100 text-blue-700' :
                          servicio.tipo === 'correctivo' ? 'bg-orange-100 text-orange-700' :
                          'bg-red-100 text-red-700'
                        }`}>
                          {servicio.tipo}
                        </span>
                        <span className="text-sm text-muted-foreground flex items-center gap-1">
                          <Calendar className="h-3 w-3" />
                          {formatDate(servicio.fecha)}
                        </span>
                        {servicio.mecanico && (
                          <span className="text-sm text-muted-foreground">
                            • Responsable: {servicio.mecanico}
                          </span>
                        )}
                      </div>
                      <p className="text-sm font-medium mb-1">{servicio.descripcion}</p>
                      {servicio.observaciones && (
                        <p className="text-sm text-muted-foreground">{servicio.observaciones}</p>
                      )}
                      {servicio.repuestos && servicio.repuestos.length > 0 && (
                        <div className="mt-2">
                          <p className="text-xs text-muted-foreground mb-1">Repuestos utilizados:</p>
                          <div className="flex flex-wrap gap-1">
                            {servicio.repuestos.map((rep: any) => (
                              <span
                                key={rep.id}
                                className="inline-flex px-2 py-0.5 bg-gray-100 text-gray-700 text-xs rounded"
                              >
                                {rep.nombre} (x{rep.cantidad})
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                    <div className="text-right ml-4 flex flex-col items-end gap-2">
                      <p className="text-lg font-bold text-gray-900">
                        {formatCurrency(servicio.costo_total || 0)}
                      </p>
                      {!esMaquina && servicio.kilometraje_servicio && (
                        <p className="text-xs text-muted-foreground">
                          {servicio.kilometraje_servicio.toLocaleString('es-AR')} km
                        </p>
                      )}
                      {esMaquina && servicio.horometro_servicio && (
                        <p className="text-xs text-muted-foreground">
                          {Number(servicio.horometro_servicio).toLocaleString('es-AR')} hs
                        </p>
                      )}
                      {isAdmin && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleDeleteServicio(servicio.id)}
                          disabled={deleteServicioMutation.isPending}
                          className="text-red-600 hover:text-red-700 hover:bg-red-50"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Trabajos y Reparaciones */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Hammer className="h-5 w-5" />
                Trabajos y Reparaciones
              </CardTitle>
              <CardDescription>
                Registro de arreglos y reparaciones realizadas
              </CardDescription>
            </div>
            <Button onClick={() => setShowTrabajoForm(!showTrabajoForm)}>
              <Plus className="h-4 w-4 mr-2" />
              Registrar Trabajo
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {/* Formulario de trabajo rápido */}
          {showTrabajoForm && (
            <div className="mb-6 p-4 border rounded-lg bg-gray-50 space-y-4">
              <h4 className="font-semibold">Nuevo Trabajo/Reparación</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Descripción *</label>
                  <Input
                    placeholder="Ej: Cambio de correa, Reparación de frenos..."
                    value={trabajoDescripcion}
                    onChange={(e) => setTrabajoDescripcion(e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Responsable</label>
                  <Input
                    placeholder="Quién realizó el trabajo"
                    value={trabajoResponsable}
                    onChange={(e) => setTrabajoResponsable(e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Costo Mano de Obra</label>
                  <Input
                    type="number"
                    placeholder="0"
                    value={trabajoCosto}
                    onChange={(e) => setTrabajoCosto(e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Observaciones</label>
                  <Input
                    placeholder="Notas adicionales..."
                    value={trabajoObservaciones}
                    onChange={(e) => setTrabajoObservaciones(e.target.value)}
                  />
                </div>
              </div>

              {/* Selector de repuestos */}
              <div className="space-y-2">
                <label className="text-sm font-medium flex items-center gap-2">
                  <Package className="h-4 w-4" />
                  Repuestos utilizados
                </label>
                <div className="flex gap-2">
                  <select
                    className="flex-1 h-10 rounded-md border border-input bg-background px-3 py-2 text-sm"
                    onChange={(e) => {
                      agregarRepuestoTrabajo(e.target.value)
                      e.target.value = ''
                    }}
                    defaultValue=""
                  >
                    <option value="">Agregar repuesto...</option>
                    {repuestosDisponibles.map((rep: Repuesto) => (
                      <option key={rep.id} value={rep.id}>
                        {rep.nombre} - Stock: {rep.stock_actual} - {formatCurrency(rep.precio_unitario)}
                      </option>
                    ))}
                  </select>
                </div>
                {trabajoRepuestos.length > 0 && (
                  <div className="space-y-2 mt-2">
                    {trabajoRepuestos.map((rep, idx) => (
                      <div key={rep.repuesto_id} className="flex items-center gap-2 p-2 bg-white border rounded">
                        <span className="flex-1 text-sm">{rep.nombre}</span>
                        <Input
                          type="number"
                          min="1"
                          className="w-20"
                          value={rep.cantidad}
                          onChange={(e) => {
                            const newList = [...trabajoRepuestos]
                            newList[idx].cantidad = parseInt(e.target.value) || 1
                            setTrabajoRepuestos(newList)
                          }}
                        />
                        <span className="text-sm text-muted-foreground w-24 text-right">
                          {formatCurrency(rep.precio * rep.cantidad)}
                        </span>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => setTrabajoRepuestos(trabajoRepuestos.filter((_, i) => i !== idx))}
                        >
                          <Trash2 className="h-4 w-4 text-red-500" />
                        </Button>
                      </div>
                    ))}
                    <div className="text-right text-sm font-semibold">
                      Total repuestos: {formatCurrency(trabajoRepuestos.reduce((sum, r) => sum + r.precio * r.cantidad, 0))}
                    </div>
                  </div>
                )}
              </div>

              <div className="flex gap-2 pt-2">
                <Button onClick={handleCrearTrabajo} disabled={createTrabajoMutation.isPending}>
                  {createTrabajoMutation.isPending ? 'Guardando...' : 'Guardar Trabajo'}
                </Button>
                <Button variant="outline" onClick={resetTrabajoForm}>
                  Cancelar
                </Button>
              </div>
            </div>
          )}

          {/* Lista de trabajos */}
          {isLoadingTrabajos ? (
            <div className="text-center py-8 text-muted-foreground">
              Cargando trabajos...
            </div>
          ) : trabajos.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              No hay trabajos registrados para {esMaquina ? 'esta máquina' : 'este camión'}
            </div>
          ) : (
            <div className="space-y-4">
              {trabajos.map((trabajo: Trabajo) => (
                <div
                  key={trabajo.id}
                  className="border rounded-lg p-4 hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <span className="text-sm text-muted-foreground flex items-center gap-1">
                          <Calendar className="h-3 w-3" />
                          {formatDate(trabajo.fecha)}
                        </span>
                        {trabajo.responsable && (
                          <span className="text-sm text-muted-foreground">
                            • Responsable: {trabajo.responsable}
                          </span>
                        )}
                      </div>
                      <p className="text-sm font-medium mb-1">{trabajo.descripcion}</p>
                      {trabajo.observaciones && (
                        <p className="text-sm text-muted-foreground">{trabajo.observaciones}</p>
                      )}
                      {trabajo.repuestos && trabajo.repuestos.length > 0 && (
                        <div className="mt-2">
                          <p className="text-xs text-muted-foreground mb-1">Repuestos utilizados:</p>
                          <div className="flex flex-wrap gap-1">
                            {trabajo.repuestos.map((rep) => (
                              <span
                                key={rep.id}
                                className="inline-flex px-2 py-0.5 bg-blue-100 text-blue-700 text-xs rounded"
                              >
                                {rep.nombre} (x{rep.cantidad})
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                    <div className="text-right ml-4 flex flex-col items-end gap-2">
                      <p className="text-lg font-bold text-gray-900">
                        {formatCurrency(trabajo.costo_total || 0)}
                      </p>
                      {isAdmin && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleDeleteTrabajo(trabajo.id)}
                          disabled={deleteTrabajoMutation.isPending}
                          className="text-red-600 hover:text-red-700 hover:bg-red-50"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
