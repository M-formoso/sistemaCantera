import { useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, Save, Fuel } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { combustibleService } from '@/services/combustibleService'

const cisternaSchema = z.object({
  nombre: z.string().min(2, 'El nombre debe tener al menos 2 caracteres'),
  capacidad_total: z.number().min(1, 'La capacidad debe ser mayor a 0'),
  nivel_minimo: z.number().min(0, 'El nivel mínimo debe ser positivo'),
})

type CisternaFormData = z.infer<typeof cisternaSchema>

export default function CisternaFormPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const {
    register,
    handleSubmit,
    formState: { errors },
    watch,
  } = useForm<CisternaFormData>({
    resolver: zodResolver(cisternaSchema),
    defaultValues: {
      nombre: '',
      capacidad_total: 0,
      nivel_minimo: 0,
    },
  })

  const capacidad = watch('capacidad_total')
  const nivelMinimo = watch('nivel_minimo')

  const createMutation = useMutation({
    mutationFn: (data: CisternaFormData) => combustibleService.createCisterna(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cisternas'] })
      navigate('/combustible')
    },
  })

  const onSubmit = async (data: CisternaFormData) => {
    if (data.nivel_minimo > data.capacidad_total) {
      alert('El nivel mínimo no puede ser mayor a la capacidad total')
      return
    }

    try {
      await createMutation.mutateAsync(data)
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Error al crear la cisterna')
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
            <Fuel className="h-8 w-8 text-blue-600" />
            Nueva Cisterna
          </h1>
          <p className="text-gray-500 mt-1">Crea una nueva cisterna de combustible</p>
        </div>
      </div>

      <div className="max-w-2xl">
        <Card>
          <CardHeader>
            <CardTitle>Datos de la Cisterna</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
              {/* Nombre */}
              <div className="space-y-2">
                <label htmlFor="nombre" className="text-sm font-medium">
                  Nombre <span className="text-red-500">*</span>
                </label>
                <Input
                  id="nombre"
                  {...register('nombre')}
                  placeholder="Ej: Cisterna Principal, Cisterna Chica"
                />
                {errors.nombre && (
                  <p className="text-sm text-red-600">{errors.nombre.message}</p>
                )}
              </div>

              {/* Capacidad Total */}
              <div className="space-y-2">
                <label htmlFor="capacidad_total" className="text-sm font-medium">
                  Capacidad Total (litros) <span className="text-red-500">*</span>
                </label>
                <Input
                  id="capacidad_total"
                  type="number"
                  step="1"
                  {...register('capacidad_total', { valueAsNumber: true })}
                  placeholder="5000"
                />
                {errors.capacidad_total && (
                  <p className="text-sm text-red-600">{errors.capacidad_total.message}</p>
                )}
              </div>

              {/* Nivel Mínimo */}
              <div className="space-y-2">
                <label htmlFor="nivel_minimo" className="text-sm font-medium">
                  Nivel Mínimo de Alerta (litros) <span className="text-red-500">*</span>
                </label>
                <Input
                  id="nivel_minimo"
                  type="number"
                  step="1"
                  {...register('nivel_minimo', { valueAsNumber: true })}
                  placeholder="500"
                />
                <p className="text-xs text-muted-foreground">
                  Se mostrará una alerta cuando el nivel baje de este valor
                </p>
                {errors.nivel_minimo && (
                  <p className="text-sm text-red-600">{errors.nivel_minimo.message}</p>
                )}
                {nivelMinimo > capacidad && capacidad > 0 && (
                  <p className="text-sm text-red-600">
                    El nivel mínimo no puede ser mayor a la capacidad total
                  </p>
                )}
              </div>

              {/* Info */}
              <div className="bg-blue-50 border border-blue-200 rounded-md p-4 text-sm text-blue-700">
                <p className="font-medium mb-1">Nota:</p>
                <p>La cisterna se creará con nivel actual en 0. Deberás registrar una carga para agregar combustible.</p>
              </div>

              {/* Botones */}
              <div className="flex items-center gap-4 pt-4 border-t">
                <Button type="submit" disabled={isLoading}>
                  <Save className="h-4 w-4 mr-2" />
                  {isLoading ? 'Creando...' : 'Crear Cisterna'}
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
    </div>
  )
}
