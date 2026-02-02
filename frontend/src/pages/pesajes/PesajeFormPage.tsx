import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, Save, Calculator } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { pesajesService } from '@/services/pesajesService'
import { camionesService } from '@/services/camionesService'
import { formatNumber } from '@/lib/utils'

const pesajeSchema = z.object({
  camion_id: z.string().min(1, 'Debe seleccionar un camión'),
  fecha: z.string().min(1, 'La fecha es requerida'),
  peso_bruto: z.number().min(1, 'El peso bruto debe ser mayor a 0'),
  peso_tara: z.number().min(1, 'El peso tara debe ser mayor a 0'),
  material: z.string().min(2, 'El material es requerido'),
  cliente_destino: z.string().min(2, 'El cliente/destino es requerido'),
  observaciones: z.string().optional(),
}).refine((data) => data.peso_bruto > data.peso_tara, {
  message: 'El peso bruto debe ser mayor al peso tara',
  path: ['peso_bruto'],
})

type PesajeFormData = z.infer<typeof pesajeSchema>

export default function PesajeFormPage() {
  const navigate = useNavigate()
  const { id } = useParams()
  const queryClient = useQueryClient()
  const isEditing = !!id

  const [pesoNeto, setPesoNeto] = useState(0)

  const { data: pesaje } = useQuery({
    queryKey: ['pesaje', id],
    queryFn: () => pesajesService.getById(id!),
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
  } = useForm<PesajeFormData>({
    resolver: zodResolver(pesajeSchema),
    defaultValues: {
      fecha: new Date().toISOString().split('T')[0],
      peso_bruto: 0,
      peso_tara: 0,
    },
  })

  // Observar cambios en peso bruto y tara para calcular peso neto
  const pesoBruto = watch('peso_bruto')
  const pesoTara = watch('peso_tara')

  useEffect(() => {
    const bruto = Number(pesoBruto) || 0
    const tara = Number(pesoTara) || 0
    const neto = bruto > tara ? bruto - tara : 0
    setPesoNeto(neto)
  }, [pesoBruto, pesoTara])

  useEffect(() => {
    if (pesaje) {
      reset({
        camion_id: pesaje.camion_id,
        fecha: pesaje.fecha.split('T')[0],
        peso_bruto: pesaje.peso_bruto,
        peso_tara: pesaje.peso_tara,
        material: pesaje.material,
        cliente_destino: pesaje.cliente_destino,
        observaciones: pesaje.observaciones || '',
      })
    }
  }, [pesaje, reset])

  const createMutation = useMutation({
    mutationFn: (data: PesajeFormData) => pesajesService.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pesajes'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard-resumen'] })
      navigate('/pesajes')
    },
  })

  const updateMutation = useMutation({
    mutationFn: (data: PesajeFormData) => pesajesService.update(id!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pesajes'] })
      queryClient.invalidateQueries({ queryKey: ['pesaje', id] })
      queryClient.invalidateQueries({ queryKey: ['dashboard-resumen'] })
      navigate('/pesajes')
    },
  })

  const onSubmit = async (data: PesajeFormData) => {
    try {
      if (isEditing) {
        await updateMutation.mutateAsync(data)
      } else {
        await createMutation.mutateAsync(data)
      }
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Error al guardar el pesaje')
    }
  }

  const isLoading = createMutation.isPending || updateMutation.isPending

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="outline" onClick={() => navigate('/pesajes')}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Volver
        </Button>
        <div>
          <h1 className="text-3xl font-bold text-gray-900">
            {isEditing ? 'Editar Pesaje' : 'Nuevo Pesaje'}
          </h1>
          <p className="text-gray-500 mt-1">
            {isEditing ? 'Modifica los datos del pesaje' : 'Registra un nuevo pesaje de camión'}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle>Datos del Pesaje</CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
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

                  {/* Peso Bruto */}
                  <div className="space-y-2">
                    <label htmlFor="peso_bruto" className="text-sm font-medium">
                      Peso Bruto (kg) <span className="text-red-500">*</span>
                    </label>
                    <Input
                      id="peso_bruto"
                      type="number"
                      step="1"
                      {...register('peso_bruto', { valueAsNumber: true })}
                      placeholder="25000"
                    />
                    {errors.peso_bruto && (
                      <p className="text-sm text-red-600">{errors.peso_bruto.message}</p>
                    )}
                  </div>

                  {/* Peso Tara */}
                  <div className="space-y-2">
                    <label htmlFor="peso_tara" className="text-sm font-medium">
                      Peso Tara (kg) <span className="text-red-500">*</span>
                    </label>
                    <Input
                      id="peso_tara"
                      type="number"
                      step="1"
                      {...register('peso_tara', { valueAsNumber: true })}
                      placeholder="10000"
                    />
                    {errors.peso_tara && (
                      <p className="text-sm text-red-600">{errors.peso_tara.message}</p>
                    )}
                  </div>

                  {/* Material */}
                  <div className="space-y-2">
                    <label htmlFor="material" className="text-sm font-medium">
                      Material <span className="text-red-500">*</span>
                    </label>
                    <select
                      id="material"
                      {...register('material')}
                      className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                    >
                      <option value="">Seleccionar material</option>
                      <option value="piedra">Piedra</option>
                      <option value="arena">Arena</option>
                      <option value="ripio">Ripio</option>
                      <option value="tierra">Tierra</option>
                      <option value="escombros">Escombros</option>
                      <option value="otros">Otros</option>
                    </select>
                    {errors.material && (
                      <p className="text-sm text-red-600">{errors.material.message}</p>
                    )}
                  </div>

                  {/* Cliente/Destino */}
                  <div className="space-y-2">
                    <label htmlFor="cliente_destino" className="text-sm font-medium">
                      Cliente/Destino <span className="text-red-500">*</span>
                    </label>
                    <Input
                      id="cliente_destino"
                      {...register('cliente_destino')}
                      placeholder="Nombre del cliente o destino"
                    />
                    {errors.cliente_destino && (
                      <p className="text-sm text-red-600">{errors.cliente_destino.message}</p>
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
                    placeholder="Notas adicionales sobre el pesaje..."
                    className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                  />
                </div>

                {/* Botones */}
                <div className="flex items-center gap-4 pt-4 border-t">
                  <Button type="submit" disabled={isLoading}>
                    <Save className="h-4 w-4 mr-2" />
                    {isLoading ? 'Guardando...' : isEditing ? 'Actualizar' : 'Registrar Pesaje'}
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => navigate('/pesajes')}
                    disabled={isLoading}
                  >
                    Cancelar
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </div>

        {/* Panel de cálculo de peso neto */}
        <div>
          <Card className="sticky top-6">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Calculator className="h-5 w-5" />
                Cálculo de Peso Neto
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Peso Bruto:</span>
                  <span className="font-medium">{formatNumber(pesoBruto || 0)} kg</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Peso Tara:</span>
                  <span className="font-medium">{formatNumber(pesoTara || 0)} kg</span>
                </div>
                <div className="border-t pt-2 mt-2">
                  <div className="flex justify-between">
                    <span className="font-semibold">Peso Neto:</span>
                    <span className="text-2xl font-bold text-green-600">
                      {formatNumber(pesoNeto)} kg
                    </span>
                  </div>
                  <div className="text-center mt-2">
                    <span className="text-xl font-bold text-green-700">
                      {formatNumber(pesoNeto / 1000, 2)} t
                    </span>
                  </div>
                </div>
              </div>

              {pesoNeto <= 0 && (pesoBruto > 0 || pesoTara > 0) && (
                <div className="bg-orange-50 border border-orange-200 rounded-md p-3 text-sm text-orange-700">
                  El peso bruto debe ser mayor al peso tara
                </div>
              )}

              {pesoNeto > 0 && (
                <div className="bg-green-50 border border-green-200 rounded-md p-3 text-sm text-green-700">
                  Cálculo automático: Peso Neto = Peso Bruto - Peso Tara
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
