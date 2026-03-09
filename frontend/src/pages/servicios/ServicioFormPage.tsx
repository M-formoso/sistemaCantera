import { useEffect, useState } from 'react'
import { useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, Save, Plus, Trash2, Package, Calculator } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { serviciosService } from '@/services/serviciosService'
import { camionesService } from '@/services/camionesService'
import { repuestosService } from '@/services/repuestosService'
import { formatCurrency, getTodayLocalDate } from '@/lib/utils'

const servicioSchema = z.object({
  camion_id: z.string().min(1, 'Debe seleccionar un camión'),
  fecha: z.string().min(1, 'La fecha es requerida'),
  tipo: z.enum(['preventivo', 'correctivo', 'emergencia']),
  descripcion: z.string().min(5, 'La descripción debe tener al menos 5 caracteres'),
  costo_mano_obra: z.number().min(0, 'El costo debe ser positivo'),
  kilometraje_servicio: z.number().min(0, 'El kilometraje debe ser positivo').optional().nullable(),
  mecanico: z.string().optional().nullable(),
  observaciones: z.string().optional(),
})

type ServicioFormData = z.infer<typeof servicioSchema>

interface RepuestoSeleccionado {
  repuesto_id: string
  cantidad: number
  nombre?: string
  precio_unitario?: number
  stock_actual?: number
}

export default function ServicioFormPage() {
  const navigate = useNavigate()
  const { id } = useParams()
  const [searchParams] = useSearchParams()
  const queryClient = useQueryClient()
  const isEditing = !!id

  const [repuestosSeleccionados, setRepuestosSeleccionados] = useState<RepuestoSeleccionado[]>([])
  const [costoTotal, setCostoTotal] = useState(0)

  const { data: servicio } = useQuery({
    queryKey: ['servicio', id],
    queryFn: () => serviciosService.getById(id!),
    enabled: isEditing,
  })

  const { data: camiones = [] } = useQuery({
    queryKey: ['camiones'],
    queryFn: () => camionesService.getAll(true),
  })

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
    watch,
  } = useForm<ServicioFormData>({
    resolver: zodResolver(servicioSchema),
    defaultValues: {
      fecha: getTodayLocalDate(),
      tipo: 'preventivo',
      costo_mano_obra: 0,
    },
  })

  // Cargar repuestos filtrados por equipo seleccionado
  const camionIdSeleccionado = watch('camion_id')
  const costoManoObra = watch('costo_mano_obra')

  const { data: repuestos = [] } = useQuery({
    queryKey: ['repuestos-por-equipo', camionIdSeleccionado],
    queryFn: () =>
      camionIdSeleccionado
        ? repuestosService.getByEquipo(camionIdSeleccionado, true)
        : repuestosService.getAll(true),
    enabled: true,
  })

  // Obtener datos del equipo seleccionado para adaptar labels
  const equipoSeleccionado = camiones.find(c => c.id === camionIdSeleccionado)
  const esMaquina = equipoSeleccionado?.categoria === 'maquina'

  // Pre-seleccionar camión si viene del parámetro
  useEffect(() => {
    const camionId = searchParams.get('camion')
    if (camionId && !isEditing) {
      reset({ camion_id: camionId })
    }
  }, [searchParams, isEditing, reset])

  // Calcular costo total
  useEffect(() => {
    const costoRepuestos = repuestosSeleccionados.reduce(
      (sum, r) => sum + (r.precio_unitario || 0) * r.cantidad,
      0
    )
    const total = (Number(costoManoObra) || 0) + costoRepuestos
    setCostoTotal(total)
  }, [repuestosSeleccionados, costoManoObra])

  useEffect(() => {
    if (servicio) {
      reset({
        camion_id: servicio.camion_id,
        fecha: servicio.fecha.split('T')[0],
        tipo: servicio.tipo,
        descripcion: servicio.descripcion,
        costo_mano_obra: servicio.costo_mano_obra,
        kilometraje_servicio: servicio.kilometraje_servicio,
        mecanico: servicio.mecanico || '',
        observaciones: servicio.observaciones || '',
      })

      // Cargar repuestos del servicio
      if (servicio.repuestos_utilizados && servicio.repuestos_utilizados.length > 0) {
        setRepuestosSeleccionados(
          servicio.repuestos_utilizados.map((r: any) => ({
            repuesto_id: r.id,
            cantidad: r.cantidad || 1,
            nombre: r.nombre,
            precio_unitario: r.precio_unitario,
            stock_actual: r.stock_actual,
          }))
        )
      }
    }
  }, [servicio, reset])

  const createMutation = useMutation({
    mutationFn: (data: ServicioFormData & { repuestos: RepuestoSeleccionado[] }) =>
      serviciosService.create(data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['servicios'] })
      queryClient.invalidateQueries({ queryKey: ['repuestos'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard-resumen'] })
      queryClient.invalidateQueries({ queryKey: ['camion-servicios', variables.camion_id] })
      queryClient.invalidateQueries({ queryKey: ['camiones'] })
      navigate('/servicios')
    },
  })

  const updateMutation = useMutation({
    mutationFn: (data: ServicioFormData & { repuestos: RepuestoSeleccionado[] }) =>
      serviciosService.update(id!, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['servicios'] })
      queryClient.invalidateQueries({ queryKey: ['servicio', id] })
      queryClient.invalidateQueries({ queryKey: ['repuestos'] })
      queryClient.invalidateQueries({ queryKey: ['camion-servicios', variables.camion_id] })
      queryClient.invalidateQueries({ queryKey: ['camiones'] })
      navigate('/servicios')
    },
  })

  const agregarRepuesto = (repuestoId: string) => {
    if (!repuestoId) return

    const repuesto = repuestos.find(r => r.id === repuestoId)
    if (!repuesto) return

    // Verificar si ya está agregado
    if (repuestosSeleccionados.some(r => r.repuesto_id === repuestoId)) {
      alert('Este repuesto ya fue agregado')
      return
    }

    setRepuestosSeleccionados([
      ...repuestosSeleccionados,
      {
        repuesto_id: repuestoId,
        cantidad: 1,
        nombre: repuesto.nombre,
        precio_unitario: repuesto.precio_unitario,
        stock_actual: repuesto.stock_actual,
      },
    ])
  }

  const eliminarRepuesto = (repuestoId: string) => {
    setRepuestosSeleccionados(repuestosSeleccionados.filter(r => r.repuesto_id !== repuestoId))
  }

  const actualizarCantidad = (repuestoId: string, cantidad: number) => {
    setRepuestosSeleccionados(
      repuestosSeleccionados.map(r =>
        r.repuesto_id === repuestoId ? { ...r, cantidad: Math.max(1, cantidad) } : r
      )
    )
  }

  const onSubmit = async (data: ServicioFormData) => {
    try {
      const payload = {
        ...data,
        repuestos: repuestosSeleccionados.map(r => ({
          repuesto_id: r.repuesto_id,
          cantidad: r.cantidad,
        })),
      }

      if (isEditing) {
        await updateMutation.mutateAsync(payload)
      } else {
        await createMutation.mutateAsync(payload)
      }
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Error al guardar el servicio')
    }
  }

  const isLoading = createMutation.isPending || updateMutation.isPending

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="outline" onClick={() => navigate('/servicios')}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Volver
        </Button>
        <div>
          <h1 className="text-3xl font-bold text-gray-900">
            {isEditing ? 'Editar Servicio' : 'Nuevo Servicio'}
          </h1>
          <p className="text-gray-500 mt-1">
            {isEditing ? 'Modifica los datos del servicio' : 'Registra un nuevo servicio de mantenimiento'}
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          {/* Datos del servicio */}
          <Card>
            <CardHeader>
              <CardTitle>Datos del Servicio</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Equipo (Camión o Máquina) */}
                <div className="space-y-2">
                  <label htmlFor="camion_id" className="text-sm font-medium">
                    Equipo <span className="text-red-500">*</span>
                  </label>
                  <select
                    id="camion_id"
                    {...register('camion_id')}
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                  >
                    <option value="">Seleccionar equipo</option>
                    <optgroup label="🚛 Camiones">
                      {camiones.filter(c => c.categoria === 'camion' && c.activo).map((camion) => (
                        <option key={camion.id} value={camion.id}>
                          {camion.patente || camion.codigo_interno} - {camion.marca} {camion.modelo}
                        </option>
                      ))}
                    </optgroup>
                    <optgroup label="⚙️ Máquinas">
                      {camiones.filter(c => c.categoria === 'maquina' && c.activo).map((maquina) => (
                        <option key={maquina.id} value={maquina.id}>
                          {maquina.nombre || maquina.codigo_interno} - {maquina.marca} {maquina.modelo}
                        </option>
                      ))}
                    </optgroup>
                  </select>
                  {errors.camion_id && (
                    <p className="text-sm text-red-600">{errors.camion_id.message}</p>
                  )}
                </div>

                {/* Fecha */}
                <div className="space-y-2">
                  <label htmlFor="fecha" className="text-sm font-medium">
                    Fecha <span className="text-red-500">*</span>
                  </label>
                  <Input
                    id="fecha"
                    type="date"
                    {...register('fecha')}
                  />
                  {errors.fecha && (
                    <p className="text-sm text-red-600">{errors.fecha.message}</p>
                  )}
                </div>

                {/* Tipo */}
                <div className="space-y-2">
                  <label htmlFor="tipo" className="text-sm font-medium">
                    Tipo de Servicio <span className="text-red-500">*</span>
                  </label>
                  <select
                    id="tipo"
                    {...register('tipo')}
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                  >
                    <option value="preventivo">Preventivo</option>
                    <option value="correctivo">Correctivo</option>
                    <option value="emergencia">Emergencia</option>
                  </select>
                  {errors.tipo && (
                    <p className="text-sm text-red-600">{errors.tipo.message}</p>
                  )}
                </div>

                {/* Costo Mano de Obra */}
                <div className="space-y-2">
                  <label htmlFor="costo_mano_obra" className="text-sm font-medium">
                    Costo Mano de Obra <span className="text-red-500">*</span>
                  </label>
                  <Input
                    id="costo_mano_obra"
                    type="number"
                    step="0.01"
                    {...register('costo_mano_obra', { valueAsNumber: true })}
                    placeholder="0.00"
                  />
                  {errors.costo_mano_obra && (
                    <p className="text-sm text-red-600">{errors.costo_mano_obra.message}</p>
                  )}
                </div>

                {/* Kilometraje/Horómetro del Servicio */}
                <div className="space-y-2">
                  <label htmlFor="kilometraje_servicio" className="text-sm font-medium">
                    {esMaquina ? 'Horómetro del Servicio' : 'Kilometraje del Servicio'}
                  </label>
                  <Input
                    id="kilometraje_servicio"
                    type="number"
                    {...register('kilometraje_servicio', { valueAsNumber: true })}
                    placeholder={esMaquina ? '5000' : '50000'}
                  />
                  <p className="text-xs text-muted-foreground">
                    {esMaquina ? 'Horas de uso al momento del mantenimiento' : 'Km al momento del servicio'}
                  </p>
                </div>

                {/* Mecánico */}
                <div className="space-y-2">
                  <label htmlFor="mecanico" className="text-sm font-medium">
                    Mecánico
                  </label>
                  <Input
                    id="mecanico"
                    type="text"
                    {...register('mecanico')}
                    placeholder="Nombre del mecánico"
                  />
                </div>
              </div>

              {/* Descripción */}
              <div className="space-y-2">
                <label htmlFor="descripcion" className="text-sm font-medium">
                  Descripción <span className="text-red-500">*</span>
                </label>
                <textarea
                  id="descripcion"
                  {...register('descripcion')}
                  rows={3}
                  placeholder="Descripción detallada del servicio realizado..."
                  className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                />
                {errors.descripcion && (
                  <p className="text-sm text-red-600">{errors.descripcion.message}</p>
                )}
              </div>

              {/* Observaciones */}
              <div className="space-y-2">
                <label htmlFor="observaciones" className="text-sm font-medium">
                  Observaciones
                </label>
                <textarea
                  id="observaciones"
                  {...register('observaciones')}
                  rows={2}
                  placeholder="Notas adicionales..."
                  className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                />
              </div>
            </CardContent>
          </Card>

          {/* Repuestos utilizados */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-2">
                  <Package className="h-5 w-5" />
                  Repuestos Utilizados
                </CardTitle>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Selector de repuestos */}
              <div className="flex gap-2">
                <select
                  id="repuesto-selector"
                  className="flex-1 h-10 rounded-md border border-input bg-background px-3 py-2 text-sm"
                  onChange={(e) => {
                    agregarRepuesto(e.target.value)
                    e.target.value = ''
                  }}
                  defaultValue=""
                  disabled={!camionIdSeleccionado}
                >
                  <option value="">
                    {camionIdSeleccionado
                      ? 'Seleccionar repuesto...'
                      : 'Primero seleccione un equipo'}
                  </option>
                  {/* Repuestos asignados al equipo */}
                  {repuestos.filter(r => r.camion_id === camionIdSeleccionado).length > 0 && (
                    <optgroup label="📦 Asignados a este equipo">
                      {repuestos
                        .filter(r => r.camion_id === camionIdSeleccionado)
                        .map((repuesto) => (
                          <option key={repuesto.id} value={repuesto.id}>
                            {repuesto.nombre} - Stock: {repuesto.stock_actual} - {formatCurrency(repuesto.precio_unitario)}
                          </option>
                        ))}
                    </optgroup>
                  )}
                  {/* Repuestos generales */}
                  {repuestos.filter(r => !r.camion_id).length > 0 && (
                    <optgroup label="🔧 Repuestos generales">
                      {repuestos
                        .filter(r => !r.camion_id)
                        .map((repuesto) => (
                          <option key={repuesto.id} value={repuesto.id}>
                            {repuesto.nombre} - Stock: {repuesto.stock_actual} - {formatCurrency(repuesto.precio_unitario)}
                          </option>
                        ))}
                    </optgroup>
                  )}
                </select>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => navigate('/repuestos/nuevo')}
                >
                  <Plus className="h-4 w-4" />
                </Button>
              </div>
              {camionIdSeleccionado && repuestos.length === 0 && (
                <p className="text-sm text-muted-foreground italic">
                  No hay repuestos disponibles para este equipo
                </p>
              )}

              {/* Lista de repuestos seleccionados */}
              {repuestosSeleccionados.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  No se han agregado repuestos a este servicio
                </div>
              ) : (
                <div className="space-y-2">
                  {repuestosSeleccionados.map((rep) => (
                    <div
                      key={rep.repuesto_id}
                      className="flex items-center gap-4 p-3 border rounded-lg"
                    >
                      <div className="flex-1">
                        <p className="font-medium text-sm">{rep.nombre}</p>
                        <p className="text-xs text-muted-foreground">
                          Stock disponible: {rep.stock_actual}
                        </p>
                      </div>
                      <div className="flex items-center gap-2">
                        <label className="text-sm text-muted-foreground">Cant:</label>
                        <Input
                          type="number"
                          min="1"
                          max={rep.stock_actual}
                          value={rep.cantidad}
                          onChange={(e) =>
                            actualizarCantidad(rep.repuesto_id, parseInt(e.target.value))
                          }
                          className="w-20"
                        />
                      </div>
                      <div className="text-right min-w-[100px]">
                        <p className="font-semibold">
                          {formatCurrency((rep.precio_unitario || 0) * rep.cantidad)}
                        </p>
                      </div>
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={() => eliminarRepuesto(rep.repuesto_id)}
                      >
                        <Trash2 className="h-4 w-4 text-red-600" />
                      </Button>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Panel de resumen de costos */}
        <div>
          <Card className="sticky top-6">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Calculator className="h-5 w-5" />
                Resumen de Costos
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-3">
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Mano de Obra:</span>
                  <span className="font-medium">{formatCurrency(Number(costoManoObra) || 0)}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Repuestos ({repuestosSeleccionados.length}):</span>
                  <span className="font-medium">
                    {formatCurrency(
                      repuestosSeleccionados.reduce(
                        (sum, r) => sum + (r.precio_unitario || 0) * r.cantidad,
                        0
                      )
                    )}
                  </span>
                </div>
                <div className="border-t pt-3">
                  <div className="flex justify-between">
                    <span className="font-semibold">Costo Total:</span>
                    <span className="text-2xl font-bold text-green-600">
                      {formatCurrency(costoTotal)}
                    </span>
                  </div>
                </div>
              </div>

              {repuestosSeleccionados.some(r => r.cantidad > (r.stock_actual || 0)) && (
                <div className="bg-red-50 border border-red-200 rounded-md p-3 text-sm text-red-700">
                  Algunos repuestos exceden el stock disponible
                </div>
              )}

              <div className="pt-4 space-y-2">
                <Button type="submit" disabled={isLoading} className="w-full">
                  <Save className="h-4 w-4 mr-2" />
                  {isLoading ? 'Guardando...' : isEditing ? 'Actualizar Servicio' : 'Registrar Servicio'}
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => navigate('/servicios')}
                  disabled={isLoading}
                  className="w-full"
                >
                  Cancelar
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </form>
    </div>
  )
}
