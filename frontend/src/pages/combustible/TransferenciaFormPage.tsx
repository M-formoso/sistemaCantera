import { useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, Save, ArrowRightLeft, Calculator } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { combustibleService } from '@/services/combustibleService'
import { formatNumber, getTodayLocalDate } from '@/lib/utils'

const transferenciaSchema = z.object({
  cisterna_origen_id: z.string().min(1, 'Debe seleccionar la cisterna de origen'),
  cisterna_destino_id: z.string().min(1, 'Debe seleccionar la cisterna de destino'),
  fecha: z.string().min(1, 'La fecha es requerida'),
  litros: z.number().min(1, 'Los litros deben ser mayor a 0'),
  observaciones: z.string().optional(),
})

type TransferenciaFormData = z.infer<typeof transferenciaSchema>

export default function TransferenciaFormPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const queryClient = useQueryClient()

  const { data: cisternas = [] } = useQuery({
    queryKey: ['cisternas'],
    queryFn: () => combustibleService.getCisternas(),
  })

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
    watch,
  } = useForm<TransferenciaFormData>({
    resolver: zodResolver(transferenciaSchema),
    defaultValues: {
      fecha: getTodayLocalDate(),
      litros: 0,
    },
  })

  const litros = watch('litros')
  const origenId = watch('cisterna_origen_id')
  const destinoId = watch('cisterna_destino_id')

  const cisternaOrigen = cisternas.find(c => c.id === origenId)
  const cisternaDestino = cisternas.find(c => c.id === destinoId)

  const nuevoNivelOrigen = (cisternaOrigen?.nivel_actual || 0) - (Number(litros) || 0)
  const nuevoNivelDestino = (cisternaDestino?.nivel_actual || 0) + (Number(litros) || 0)

  const insuficiente = nuevoNivelOrigen < 0
  const excedeCapacidad = cisternaDestino && nuevoNivelDestino > cisternaDestino.capacidad_total
  const mismaCisterna = Boolean(origenId && destinoId && origenId === destinoId)

  // Pre-seleccionar cisterna origen si viene del parámetro
  useEffect(() => {
    const origen = searchParams.get('origen')
    if (origen) {
      reset({
        cisterna_origen_id: origen,
        fecha: getTodayLocalDate(),
        litros: 0,
      })
    }
  }, [searchParams, reset])

  const createMutation = useMutation({
    mutationFn: (data: TransferenciaFormData) => combustibleService.registrarTransferencia(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cisternas'] })
      queryClient.invalidateQueries({ queryKey: ['transferencias'] })
      navigate('/combustible')
    },
  })

  const onSubmit = async (data: TransferenciaFormData) => {
    if (mismaCisterna) {
      alert('La cisterna de origen y destino deben ser diferentes')
      return
    }

    if (insuficiente) {
      alert('No hay suficiente combustible en la cisterna de origen')
      return
    }

    if (excedeCapacidad) {
      const confirmar = window.confirm(
        `La transferencia excede la capacidad de la cisterna destino (${formatNumber(cisternaDestino!.capacidad_total)} L). ¿Desea continuar?`
      )
      if (!confirmar) return
    }

    try {
      await createMutation.mutateAsync(data)
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Error al registrar la transferencia')
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
            <ArrowRightLeft className="h-8 w-8 text-purple-600" />
            Transferencia entre Cisternas
          </h1>
          <p className="text-gray-500 mt-1">Transfiere combustible de una cisterna a otra</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle>Datos de la Transferencia</CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* Cisterna Origen */}
                  <div className="space-y-2">
                    <label htmlFor="cisterna_origen_id" className="text-sm font-medium">
                      Cisterna de Origen <span className="text-red-500">*</span>
                    </label>
                    <select
                      id="cisterna_origen_id"
                      {...register('cisterna_origen_id')}
                      className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                    >
                      <option value="">Seleccionar cisterna origen</option>
                      {cisternas.map((cisterna) => (
                        <option key={cisterna.id} value={cisterna.id}>
                          {cisterna.nombre} - Disponible: {formatNumber(cisterna.nivel_actual)} L
                        </option>
                      ))}
                    </select>
                    {errors.cisterna_origen_id && (
                      <p className="text-sm text-red-600">{errors.cisterna_origen_id.message}</p>
                    )}
                  </div>

                  {/* Cisterna Destino */}
                  <div className="space-y-2">
                    <label htmlFor="cisterna_destino_id" className="text-sm font-medium">
                      Cisterna de Destino <span className="text-red-500">*</span>
                    </label>
                    <select
                      id="cisterna_destino_id"
                      {...register('cisterna_destino_id')}
                      className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                    >
                      <option value="">Seleccionar cisterna destino</option>
                      {cisternas.map((cisterna) => (
                        <option key={cisterna.id} value={cisterna.id}>
                          {cisterna.nombre} - Actual: {formatNumber(cisterna.nivel_actual)} L
                        </option>
                      ))}
                    </select>
                    {errors.cisterna_destino_id && (
                      <p className="text-sm text-red-600">{errors.cisterna_destino_id.message}</p>
                    )}
                    {mismaCisterna && (
                      <p className="text-sm text-red-600">Las cisternas deben ser diferentes</p>
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
                      Litros a transferir <span className="text-red-500">*</span>
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
                  <Button type="submit" disabled={isLoading || insuficiente || mismaCisterna}>
                    <Save className="h-4 w-4 mr-2" />
                    {isLoading ? 'Transfiriendo...' : 'Realizar Transferencia'}
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
              {cisternaOrigen && cisternaDestino && !mismaCisterna ? (
                <>
                  {/* Cisterna Origen */}
                  <div className="space-y-2 pb-3 border-b">
                    <div className="text-sm font-medium text-orange-600">Origen: {cisternaOrigen.nombre}</div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Nivel Actual:</span>
                      <span className="font-medium">{formatNumber(cisternaOrigen.nivel_actual)} L</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Transferencia:</span>
                      <span className="font-medium text-orange-600">-{formatNumber(litros || 0)} L</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="font-semibold text-sm">Nuevo Nivel:</span>
                      <span className={`font-bold ${insuficiente ? 'text-red-600' : 'text-blue-600'}`}>
                        {formatNumber(nuevoNivelOrigen)} L
                      </span>
                    </div>
                  </div>

                  {/* Cisterna Destino */}
                  <div className="space-y-2 pb-3 border-b">
                    <div className="text-sm font-medium text-green-600">Destino: {cisternaDestino.nombre}</div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Nivel Actual:</span>
                      <span className="font-medium">{formatNumber(cisternaDestino.nivel_actual)} L</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Transferencia:</span>
                      <span className="font-medium text-green-600">+{formatNumber(litros || 0)} L</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="font-semibold text-sm">Nuevo Nivel:</span>
                      <span className={`font-bold ${excedeCapacidad ? 'text-red-600' : 'text-green-600'}`}>
                        {formatNumber(nuevoNivelDestino)} L
                      </span>
                    </div>
                    <div className="text-xs text-muted-foreground text-right">
                      de {formatNumber(cisternaDestino.capacidad_total)} L
                    </div>
                  </div>

                  {/* Alertas */}
                  {insuficiente && (
                    <div className="bg-red-50 border border-red-200 rounded-md p-3 text-sm text-red-700">
                      No hay suficiente combustible en la cisterna de origen
                    </div>
                  )}

                  {excedeCapacidad && (
                    <div className="bg-orange-50 border border-orange-200 rounded-md p-3 text-sm text-orange-700">
                      La transferencia excede la capacidad de la cisterna destino
                    </div>
                  )}

                  {!insuficiente && !excedeCapacidad && litros > 0 && (
                    <div className="bg-green-50 border border-green-200 rounded-md p-3 text-sm text-green-700">
                      Transferencia válida
                    </div>
                  )}
                </>
              ) : (
                <div className="text-center py-8 text-muted-foreground text-sm">
                  {mismaCisterna
                    ? 'Selecciona cisternas diferentes'
                    : 'Selecciona las cisternas para ver el resumen'}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
