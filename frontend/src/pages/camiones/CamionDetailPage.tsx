import { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, Truck, Wrench, Calendar, Trash2, CalendarClock, AlertTriangle } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { camionesService } from '@/services/camionesService'
import { serviciosService } from '@/services/serviciosService'
import { formatDate, formatCurrency } from '@/lib/utils'
import { useIsAdmin } from '@/hooks/useIsAdmin'

export default function CamionDetailPage() {
  const navigate = useNavigate()
  const { id } = useParams()
  const queryClient = useQueryClient()
  const isAdmin = useIsAdmin()
  const [showProximoServicio, setShowProximoServicio] = useState(false)
  const [proximoServicioFecha, setProximoServicioFecha] = useState('')
  const [proximoServicioKm, setProximoServicioKm] = useState('')

  const { data: camion, isLoading: isLoadingCamion } = useQuery({
    queryKey: ['camion', id],
    queryFn: () => camionesService.getById(id!),
  })

  const { data: servicios = [], isLoading: isLoadingServicios } = useQuery({
    queryKey: ['camion-servicios', id],
    queryFn: () => camionesService.getServicios(id!),
  })

  const deleteServicioMutation = useMutation({
    mutationFn: (servicioId: string) => serviciosService.delete(servicioId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['camion-servicios', id] })
      queryClient.invalidateQueries({ queryKey: ['camion', id] })
      queryClient.invalidateQueries({ queryKey: ['camiones'] })
    },
  })

  const updateCamionMutation = useMutation({
    mutationFn: (data: { proximo_servicio_fecha?: string; proximo_servicio_km?: number }) =>
      camionesService.update(id!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['camion', id] })
      queryClient.invalidateQueries({ queryKey: ['camiones'] })
      setShowProximoServicio(false)
      setProximoServicioFecha('')
      setProximoServicioKm('')
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
      })
    } catch (error) {
      alert('Error al guardar el próximo servicio')
    }
  }

  if (isLoadingCamion) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-gray-500">Cargando camión...</div>
      </div>
    )
  }

  if (!camion) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-gray-500">Camión no encontrado</div>
      </div>
    )
  }

  const estadoColorClass =
    camion.estado === 'operativo' ? 'bg-green-100 text-green-700' :
    camion.estado === 'en_servicio' ? 'bg-orange-100 text-orange-700' :
    'bg-red-100 text-red-700'

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="outline" onClick={() => navigate('/camiones')}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Volver
        </Button>
        <div className="flex-1">
          <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
            <Truck className="h-8 w-8" />
            {camion.patente}
          </h1>
          <p className="text-gray-500 mt-1">
            {camion.marca} {camion.modelo} - {camion.año}
          </p>
        </div>
        <Button onClick={() => navigate(`/camiones/${id}/editar`)}>
          Editar Camión
        </Button>
      </div>

      {/* Información del camión */}
      <Card>
        <CardHeader>
          <CardTitle>Información del Camión</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <div>
              <p className="text-sm text-muted-foreground">Patente</p>
              <p className="text-lg font-semibold">{camion.patente}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Marca y Modelo</p>
              <p className="text-lg font-semibold">{camion.marca} {camion.modelo}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Año</p>
              <p className="text-lg font-semibold">{camion.año}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Kilometraje Actual</p>
              <p className="text-lg font-semibold">{camion.kilometraje_actual != null ? `${camion.kilometraje_actual.toLocaleString('es-AR')} km` : '-'}</p>
            </div>
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
              <div>
                <p className="text-sm text-muted-foreground">Intervalo de Servicio</p>
                <p className="text-lg font-semibold">
                  {camion.intervalo_servicio_km ? `Cada ${camion.intervalo_servicio_km.toLocaleString('es-AR')} km` : 'No definido'}
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
                Historial de Servicios
              </CardTitle>
              <CardDescription>Servicios realizados a este camión</CardDescription>
            </div>
            <Button onClick={() => navigate(`/servicios/nuevo?camion=${id}`)}>
              Registrar Servicio
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
              No hay servicios registrados para este camión
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
                        <span className="inline-flex px-2 py-1 bg-blue-100 text-blue-700 text-xs font-semibold rounded">
                          {servicio.tipo}
                        </span>
                        <span className="text-sm text-muted-foreground flex items-center gap-1">
                          <Calendar className="h-3 w-3" />
                          {formatDate(servicio.fecha)}
                        </span>
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
                      {servicio.kilometraje_servicio && (
                        <p className="text-xs text-muted-foreground">
                          {servicio.kilometraje_servicio.toLocaleString('es-AR')} km
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
    </div>
  )
}
