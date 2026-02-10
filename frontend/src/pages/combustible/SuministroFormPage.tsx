import { useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, Save, TrendingDown, Calculator } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { combustibleService } from '@/services/combustibleService'
import { camionesService } from '@/services/camionesService'
import { formatNumber } from '@/lib/utils'

const suministroSchema = z.object({
  cisterna_id: z.string().min(1, 'Debe seleccionar una cisterna'),
  camion_id: z.string().min(1, 'Debe seleccionar un camión'),
  fecha: z.string().min(1, 'La fecha es requerida'),
  litros: z.number().min(1, 'Los litros deben ser mayor a 0'),
  kilometraje_actual: z.number().min(0, 'El kilometraje debe ser positivo').optional().nullable(),
  observaciones: z.string().optional(),
})

type SuministroFormData = z.infer<typeof suministroSchema>

export default function SuministroFormPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const queryClient = useQueryClient()

  const { data: cisternas = [] } = useQuery({
    queryKey: ['cisternas'],
    queryFn: () => combustibleService.getCisternas(),
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
  } = useForm<SuministroFormData>({
    resolver: zodResolver(suministroSchema),
    defaultValues: {
      fecha: new Date().toISOString().split('T')[0],
      litros: 0,
    },
  })

  const litros = watch('litros')
  const cisternaId = watch('cisterna_id')
  const camionId = watch('camion_id')

  const cisternaSeleccionada = cisternas.find(c => c.id === cisternaId)
  const camionSeleccionado = camiones.find(c => c.id === camionId)
  const nuevoNivel = (cisternaSeleccionada?.nivel_actual || 0) - (Number(litros) || 0)
  const insuficiente = nuevoNivel < 0

  // Pre-seleccionar cisterna o camión si viene del parámetro
  useEffect(() => {
    const cisterna = searchParams.get('cisterna')
    const camion = searchParams.get('camion')
    if (cisterna || camion) {
      reset({
        cisterna_id: cisterna || undefined,
        camion_id: camion || undefined,
      })
    }
  }, [searchParams, reset])

  const createMutation = useMutation({
    mutationFn: (data: SuministroFormData) => {
      const cleanData = {
        ...data,
        kilometraje_actual: data.kilometraje_actual ?? undefined,
      }
      return combustibleService.registrarSuministro(cleanData)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['suministros'] })
      queryClient.invalidateQueries({ queryKey: ['cisternas'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard-resumen'] })
      navigate('/combustible')
    },
  })

  const onSubmit = async (data: SuministroFormData) => {
    if (insuficiente) {
      alert('No hay suficiente combustible en la cisterna')
      return
    }

    try {
      await createMutation.mutateAsync(data)
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Error al registrar el suministro')
    }
  }

  const isLoading = createMutation.isPending

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="outline" onClick={() => navigate('/combustible')}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Volver
        </Button>
        <div>
          <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
            <TrendingDown className="h-8 w-8 text-orange-600" />
            Nuevo Suministro de Combustible
          </h1>
          <p className="text-gray-500 mt-1">Registra un suministro de combustible a camión</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle>Datos del Suministro</CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* Cisterna */}
                  <div className="space-y-2">
                    <label htmlFor="cisterna_id" className="text-sm font-medium">
                      Cisterna <span className="text-red-500">*</span>
                    </label>
                    <select
                      id="cisterna_id"
                      {...register('cisterna_id')}
                      className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                    >
                      <option value="">Seleccionar cisterna</option>
                      {cisternas.map((cisterna) => (
                        <option key={cisterna.id} value={cisterna.id}>
                          {cisterna.nombre} - Disponible: {formatNumber(cisterna.nivel_actual)} L
                        </option>
                      ))}
                    </select>
                    {errors.cisterna_id && (
                      <p className="text-sm text-red-600">{errors.cisterna_id.message}</p>
                    )}
                  </div>

                  {/* Camión */}
                  <div className="space-y-2">
                    <label htmlFor="camion_id" className="text-sm font-medium">
                      Camión <span className="text-red-500">*</span>
                    </label>
                    <select
                      id="camion_id"
                      {...register('camion_id')}
                      className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                    >
                      <option value="">Seleccionar camión</option>
                      {camiones.map((camion) => (
                        <option key={camion.id} value={camion.id}>
                          {camion.patente} - {camion.marca} {camion.modelo}
                        </option>
                      ))}
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

                  {/* Litros */}
                  <div className="space-y-2">
                    <label htmlFor="litros" className="text-sm font-medium">
                      Litros <span className="text-red-500">*</span>
                    </label>
                    <Input
                      id="litros"
                      type="number"
                      step="0.01"
                      {...register('litros', { valueAsNumber: true })}
                      placeholder="100"
                    />
                    {errors.litros && (
                      <p className="text-sm text-red-600">{errors.litros.message}</p>
                    )}
                  </div>

                  {/* Kilometraje actual */}
                  <div className="space-y-2">
                    <label htmlFor="kilometraje_actual" className="text-sm font-medium">
                      Kilometraje Actual
                    </label>
                    <Input
                      id="kilometraje_actual"
                      type="number"
                      {...register('kilometraje_actual', { valueAsNumber: true })}
                      placeholder={camionSeleccionado ? `Actual: ${camionSeleccionado.kilometraje_actual}` : '50000'}
                    />
                    {camionSeleccionado && (
                      <p className="text-xs text-muted-foreground">
                        Último registrado: {formatNumber(camionSeleccionado.kilometraje_actual)} km
                      </p>
                    )}
                  </div>
                </div>

                {/* Observaciones */}
                <div className="space-y-2">
                  <label htmlFor="observaciones" className="text-sm font-medium">
                    Observaciones
                  </label>
                  <textarea
                    id="observaciones"
                    {...register('observaciones')}
                    rows={3}
                    placeholder="Notas adicionales..."
                    className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                  />
                </div>

                {/* Botones */}
                <div className="flex items-center gap-4 pt-4 border-t">
                  <Button type="submit" disabled={isLoading || insuficiente}>
                    <Save className="h-4 w-4 mr-2" />
                    {isLoading ? 'Guardando...' : 'Registrar Suministro'}
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => navigate('/combustible')}
                    disabled={isLoading}
                  >
                    Cancelar
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </div>

        {/* Panel de resumen */}
        <div>
          <Card className="sticky top-6">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Calculator className="h-5 w-5" />
                Resumen
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {cisternaSeleccionada && camionSeleccionado ? (
                <>
                  <div className="space-y-3">
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Cisterna:</span>
                      <span className="font-medium">{cisternaSeleccionada.nombre}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Camión:</span>
                      <span className="font-medium">{camionSeleccionado.patente}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Disponible:</span>
                      <span className="font-medium">
                        {formatNumber(cisternaSeleccionada.nivel_actual)} L
                      </span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Suministro:</span>
                      <span className="font-medium text-orange-600">
                        -{formatNumber(litros || 0)} L
                      </span>
                    </div>
                    <div className="border-t pt-3">
                      <div className="flex justify-between">
                        <span className="font-semibold">Nivel Resultante:</span>
                        <span className={`text-xl font-bold ${insuficiente ? 'text-red-600' : 'text-blue-600'}`}>
                          {formatNumber(nuevoNivel)} L
                        </span>
                      </div>
                      <div className="text-xs text-muted-foreground text-right mt-1">
                        de {formatNumber(cisternaSeleccionada.capacidad_total)} L
                      </div>
                    </div>
                  </div>

                  {insuficiente && (
                    <div className="bg-red-50 border border-red-200 rounded-md p-3 text-sm text-red-700">
                      ⚠️ No hay suficiente combustible en la cisterna
                    </div>
                  )}

                  {nuevoNivel > 0 && nuevoNivel <= cisternaSeleccionada.nivel_minimo && (
                    <div className="bg-orange-50 border border-orange-200 rounded-md p-3 text-sm text-orange-700">
                      ⚠️ El nivel quedará por debajo del mínimo ({formatNumber(cisternaSeleccionada.nivel_minimo)} L)
                    </div>
                  )}

                  {!insuficiente && nuevoNivel > cisternaSeleccionada.nivel_minimo && (
                    <div className="bg-green-50 border border-green-200 rounded-md p-3 text-sm text-green-700">
                      ✓ Suministro válido
                    </div>
                  )}
                </>
              ) : (
                <div className="text-center py-8 text-muted-foreground text-sm">
                  Selecciona cisterna y camión para ver el resumen
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
