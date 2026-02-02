import { useNavigate, useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ArrowLeft, Truck, Wrench, Calendar } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { camionesService } from '@/services/camionesService'
import { formatDate, formatCurrency } from '@/lib/utils'

export default function CamionDetailPage() {
  const navigate = useNavigate()
  const { id } = useParams()

  const { data: camion, isLoading: isLoadingCamion } = useQuery({
    queryKey: ['camion', id],
    queryFn: () => camionesService.getById(id!),
  })

  const { data: servicios = [], isLoading: isLoadingServicios } = useQuery({
    queryKey: ['camion-servicios', id],
    queryFn: () => camionesService.getServicios(id!),
  })

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
              <p className="text-sm text-muted-foreground">Kilometraje</p>
              <p className="text-lg font-semibold">{camion.kilometraje.toLocaleString('es-AR')} km</p>
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
                    <div className="text-right ml-4">
                      <p className="text-lg font-bold text-gray-900">
                        {formatCurrency(servicio.costo_total || 0)}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {servicio.kilometraje_actual?.toLocaleString('es-AR')} km
                      </p>
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
