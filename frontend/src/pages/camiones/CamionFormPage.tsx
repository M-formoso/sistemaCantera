import { useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, Save } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { camionesService } from '@/services/camionesService'

const camionSchema = z.object({
  patente: z.string().min(6, 'La patente debe tener al menos 6 caracteres').max(10),
  marca: z.string().min(2, 'La marca es requerida'),
  modelo: z.string().min(2, 'El modelo es requerido'),
  año: z.number().min(1990, 'Año mínimo 1990').max(new Date().getFullYear() + 1),
  kilometraje_actual: z.number().min(0, 'El kilometraje debe ser positivo'),
  estado: z.enum(['operativo', 'en_servicio', 'fuera_servicio']),
  observaciones: z.string().optional(),
  intervalo_servicio_km: z.number().min(1000, 'Mínimo 1000 km').optional().nullable(),
  proximo_servicio_km: z.number().min(0).optional().nullable(),
})

type CamionFormData = z.infer<typeof camionSchema>

export default function CamionFormPage() {
  const navigate = useNavigate()
  const { id } = useParams()
  const queryClient = useQueryClient()
  const isEditing = !!id

  const { data: camion } = useQuery({
    queryKey: ['camion', id],
    queryFn: () => camionesService.getById(id!),
    enabled: isEditing,
  })

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<CamionFormData>({
    resolver: zodResolver(camionSchema),
    defaultValues: {
      estado: 'operativo',
      kilometraje_actual: 0,
      intervalo_servicio_km: 10000,
    },
  })

  useEffect(() => {
    if (camion) {
      reset({
        patente: camion.patente,
        marca: camion.marca,
        modelo: camion.modelo,
        año: camion.año,
        kilometraje_actual: camion.kilometraje_actual,
        estado: camion.estado,
        observaciones: camion.observaciones || '',
        intervalo_servicio_km: camion.intervalo_servicio_km || 10000,
        proximo_servicio_km: camion.proximo_servicio_km,
      })
    }
  }, [camion, reset])

  const createMutation = useMutation({
    mutationFn: (data: CamionFormData) => camionesService.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['camiones'] })
      navigate('/camiones')
    },
  })

  const updateMutation = useMutation({
    mutationFn: (data: CamionFormData) => camionesService.update(id!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['camiones'] })
      queryClient.invalidateQueries({ queryKey: ['camion', id] })
      navigate('/camiones')
    },
  })

  const onSubmit = async (data: CamionFormData) => {
    try {
      if (isEditing) {
        await updateMutation.mutateAsync(data)
      } else {
        await createMutation.mutateAsync(data)
      }
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Error al guardar el camión')
    }
  }

  const isLoading = createMutation.isPending || updateMutation.isPending

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="outline" onClick={() => navigate('/camiones')}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Volver
        </Button>
        <div>
          <h1 className="text-3xl font-bold text-gray-900">
            {isEditing ? 'Editar Camión' : 'Nuevo Camión'}
          </h1>
          <p className="text-gray-500 mt-1">
            {isEditing ? 'Modifica los datos del camión' : 'Registra un nuevo camión en la flota'}
          </p>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Datos del Camión</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Patente */}
              <div className="space-y-2">
                <label htmlFor="patente" className="text-sm font-medium">
                  Patente <span className="text-red-500">*</span>
                </label>
                <Input
                  id="patente"
                  {...register('patente')}
                  placeholder="ABC123"
                  disabled={isEditing}
                />
                {errors.patente && (
                  <p className="text-sm text-red-600">{errors.patente.message}</p>
                )}
              </div>

              {/* Marca */}
              <div className="space-y-2">
                <label htmlFor="marca" className="text-sm font-medium">
                  Marca <span className="text-red-500">*</span>
                </label>
                <Input
                  id="marca"
                  {...register('marca')}
                  placeholder="Mercedes-Benz, Scania, etc."
                />
                {errors.marca && (
                  <p className="text-sm text-red-600">{errors.marca.message}</p>
                )}
              </div>

              {/* Modelo */}
              <div className="space-y-2">
                <label htmlFor="modelo" className="text-sm font-medium">
                  Modelo <span className="text-red-500">*</span>
                </label>
                <Input
                  id="modelo"
                  {...register('modelo')}
                  placeholder="Actros 2651"
                />
                {errors.modelo && (
                  <p className="text-sm text-red-600">{errors.modelo.message}</p>
                )}
              </div>

              {/* Año */}
              <div className="space-y-2">
                <label htmlFor="año" className="text-sm font-medium">
                  Año <span className="text-red-500">*</span>
                </label>
                <Input
                  id="año"
                  type="number"
                  {...register('año', { valueAsNumber: true })}
                  placeholder="2020"
                />
                {errors.año && (
                  <p className="text-sm text-red-600">{errors.año.message}</p>
                )}
              </div>

              {/* Kilometraje */}
              <div className="space-y-2">
                <label htmlFor="kilometraje_actual" className="text-sm font-medium">
                  Kilometraje Actual <span className="text-red-500">*</span>
                </label>
                <Input
                  id="kilometraje_actual"
                  type="number"
                  {...register('kilometraje_actual', { valueAsNumber: true })}
                  placeholder="50000"
                />
                {errors.kilometraje_actual && (
                  <p className="text-sm text-red-600">{errors.kilometraje_actual.message}</p>
                )}
              </div>

              {/* Estado */}
              <div className="space-y-2">
                <label htmlFor="estado" className="text-sm font-medium">
                  Estado <span className="text-red-500">*</span>
                </label>
                <select
                  id="estado"
                  {...register('estado')}
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                >
                  <option value="operativo">Operativo</option>
                  <option value="en_servicio">En servicio</option>
                  <option value="fuera_servicio">Fuera de servicio</option>
                </select>
                {errors.estado && (
                  <p className="text-sm text-red-600">{errors.estado.message}</p>
                )}
              </div>

              {/* Intervalo de Servicio */}
              <div className="space-y-2">
                <label htmlFor="intervalo_servicio_km" className="text-sm font-medium">
                  Intervalo de Servicio (km)
                </label>
                <Input
                  id="intervalo_servicio_km"
                  type="number"
                  {...register('intervalo_servicio_km', { valueAsNumber: true })}
                  placeholder="10000"
                />
                <p className="text-xs text-muted-foreground">Cada cuántos km se debe hacer servicio</p>
                {errors.intervalo_servicio_km && (
                  <p className="text-sm text-red-600">{errors.intervalo_servicio_km.message}</p>
                )}
              </div>

              {/* Próximo Servicio */}
              <div className="space-y-2">
                <label htmlFor="proximo_servicio_km" className="text-sm font-medium">
                  Próximo Servicio (km)
                </label>
                <Input
                  id="proximo_servicio_km"
                  type="number"
                  {...register('proximo_servicio_km', { valueAsNumber: true })}
                  placeholder="60000"
                />
                <p className="text-xs text-muted-foreground">Se calcula automáticamente al registrar servicios</p>
                {errors.proximo_servicio_km && (
                  <p className="text-sm text-red-600">{errors.proximo_servicio_km.message}</p>
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
                rows={4}
                placeholder="Notas adicionales sobre el camión..."
                className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
              />
              {errors.observaciones && (
                <p className="text-sm text-red-600">{errors.observaciones.message}</p>
              )}
            </div>

            {/* Botones */}
            <div className="flex items-center gap-4 pt-4 border-t">
              <Button type="submit" disabled={isLoading}>
                <Save className="h-4 w-4 mr-2" />
                {isLoading ? 'Guardando...' : isEditing ? 'Actualizar' : 'Crear Camión'}
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={() => navigate('/camiones')}
                disabled={isLoading}
              >
                Cancelar
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
