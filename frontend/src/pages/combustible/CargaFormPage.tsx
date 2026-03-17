import { useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, Save, TrendingUp, Calculator } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { combustibleService } from '@/services/combustibleService'
import { formatNumber, formatCurrency, getTodayLocalDate } from '@/lib/utils'

const cargaSchema = z.object({
  cisterna_id: z.string().min(1, 'Debe seleccionar una cisterna'),
  fecha: z.string().min(1, 'La fecha es requerida'),
  litros: z.number().min(1, 'Los litros deben ser mayor a 0'),
  proveedor: z.string().min(2, 'El proveedor es requerido'),
  numero_factura: z.string().optional(),
  costo_total: z.number().min(0, 'El costo debe ser positivo').optional().nullable(),
  observaciones: z.string().optional(),
})

type CargaFormData = z.infer<typeof cargaSchema>

export default function CargaFormPage() {
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
  } = useForm<CargaFormData>({
    resolver: zodResolver(cargaSchema),
    defaultValues: {
      fecha: getTodayLocalDate(),
      litros: 0,
      costo_total: 0,
    },
  })

  const litros = watch('litros')
  const costoTotal = watch('costo_total')
  const cisternaId = watch('cisterna_id')

  const precioPorLitro = litros > 0 ? (Number(costoTotal) || 0) / litros : 0
  const cisternaSeleccionada = cisternas.find(c => c.id === cisternaId)
  const nuevoNivel = (cisternaSeleccionada?.nivel_actual || 0) + (Number(litros) || 0)
  const excedeLimite = cisternaSeleccionada && nuevoNivel > cisternaSeleccionada.capacidad_total

  // Pre-seleccionar cisterna si viene del parámetro
  useEffect(() => {
    const cisterna = searchParams.get('cisterna')
    if (cisterna) {
      reset({ cisterna_id: cisterna })
    }
  }, [searchParams, reset])

  const createMutation = useMutation({
    mutationFn: (data: CargaFormData) => {
      const cleanData = {
        ...data,
        costo_total: data.costo_total ?? undefined,
      }
      return combustibleService.registrarCarga(cleanData)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cargas'] })
      queryClient.invalidateQueries({ queryKey: ['cisternas'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard-resumen'] })
      navigate('/combustible')
    },
  })

  const onSubmit = async (data: CargaFormData) => {
    if (excedeLimite) {
      const confirmar = window.confirm(
        `La carga excede la capacidad de la cisterna (${formatNumber(cisternaSeleccionada!.capacidad_total)} L). ¿Desea continuar?`
      )
      if (!confirmar) return
    }

    try {
      await createMutation.mutateAsync(data)
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Error al registrar la carga')
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
            <TrendingUp className="h-8 w-8 text-green-600" />
            Nueva Carga de Combustible
          </h1>
          <p className="text-gray-500 mt-1">Registra una carga de combustible a cisterna</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle>Datos de la Carga</CardTitle>
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
                          {cisterna.nombre} - Actual: {formatNumber(cisterna.nivel_actual)} L
                        </option>
                      ))}
                    </select>
                    {errors.cisterna_id && (
                      <p className="text-sm text-red-600">{errors.cisterna_id.message}</p>
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
                      placeholder="1000"
                    />
                    {errors.litros && (
                      <p className="text-sm text-red-600">{errors.litros.message}</p>
                    )}
                  </div>

                  {/* Costo Total */}
                  <div className="space-y-2">
                    <label htmlFor="costo_total" className="text-sm font-medium">
                      Costo Total
                    </label>
                    <Input
                      id="costo_total"
                      type="number"
                      step="0.01"
                      {...register('costo_total', { valueAsNumber: true })}
                      placeholder="0.00"
                    />
                    {errors.costo_total && (
                      <p className="text-sm text-red-600">{errors.costo_total.message}</p>
                    )}
                    {litros > 0 && (costoTotal ?? 0) > 0 && (
                      <p className="text-xs text-muted-foreground">
                        Precio por litro: {formatCurrency(precioPorLitro)}
                      </p>
                    )}
                  </div>

                  {/* Proveedor */}
                  <div className="space-y-2">
                    <label htmlFor="proveedor" className="text-sm font-medium">
                      Proveedor <span className="text-red-500">*</span>
                    </label>
                    <Input
                      id="proveedor"
                      {...register('proveedor')}
                      placeholder="Nombre del proveedor"
                    />
                    {errors.proveedor && (
                      <p className="text-sm text-red-600">{errors.proveedor.message}</p>
                    )}
                  </div>

                  {/* Número de factura */}
                  <div className="space-y-2">
                    <label htmlFor="numero_factura" className="text-sm font-medium">
                      Número de Factura
                    </label>
                    <Input
                      id="numero_factura"
                      {...register('numero_factura')}
                      placeholder="0001-00001234"
                    />
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
                  <Button type="submit" disabled={isLoading}>
                    <Save className="h-4 w-4 mr-2" />
                    {isLoading ? 'Guardando...' : 'Registrar Carga'}
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
              {cisternaSeleccionada ? (
                <>
                  <div className="space-y-3">
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Cisterna:</span>
                      <span className="font-medium">{cisternaSeleccionada.nombre}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Nivel Actual:</span>
                      <span className="font-medium">
                        {formatNumber(cisternaSeleccionada.nivel_actual)} L
                      </span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Carga:</span>
                      <span className="font-medium text-green-600">
                        +{formatNumber(litros || 0)} L
                      </span>
                    </div>
                    <div className="border-t pt-3">
                      <div className="flex justify-between">
                        <span className="font-semibold">Nuevo Nivel:</span>
                        <span className={`text-xl font-bold ${excedeLimite ? 'text-red-600' : 'text-green-600'}`}>
                          {formatNumber(nuevoNivel)} L
                        </span>
                      </div>
                      <div className="text-xs text-muted-foreground text-right mt-1">
                        de {formatNumber(cisternaSeleccionada.capacidad_total)} L
                      </div>
                    </div>
                  </div>

                  {excedeLimite && (
                    <div className="bg-red-50 border border-red-200 rounded-md p-3 text-sm text-red-700">
                      ⚠️ La carga excede la capacidad de la cisterna
                    </div>
                  )}

                  {(costoTotal ?? 0) > 0 && (
                    <div className="pt-3 border-t">
                      <div className="flex justify-between">
                        <span className="font-semibold">Costo Total:</span>
                        <span className="text-xl font-bold text-blue-600">
                          {formatCurrency(costoTotal || 0)}
                        </span>
                      </div>
                      {litros > 0 && (
                        <div className="text-xs text-muted-foreground text-right mt-1">
                          {formatNumber(litros)} L × {formatCurrency(precioPorLitro)} por litro
                        </div>
                      )}
                    </div>
                  )}
                </>
              ) : (
                <div className="text-center py-8 text-muted-foreground text-sm">
                  Selecciona una cisterna para ver el resumen
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
