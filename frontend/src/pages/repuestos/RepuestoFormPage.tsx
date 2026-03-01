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
import { repuestosService } from '@/services/repuestosService'
import { camionesService } from '@/services/camionesService'
import { Camion } from '@/types'

const repuestoSchema = z.object({
  codigo: z.string().min(2, 'El código debe tener al menos 2 caracteres'),
  nombre: z.string().min(3, 'El nombre debe tener al menos 3 caracteres'),
  descripcion: z.string().optional(),
  categoria: z.string().min(2, 'La categoría es requerida'),
  precio_unitario: z.number().min(0, 'El precio debe ser positivo'),
  stock_actual: z.number().min(0, 'El stock debe ser positivo'),
  stock_minimo: z.number().min(0, 'El stock mínimo debe ser positivo'),
  ubicacion: z.string().optional(),
  camion_id: z.string().optional(),
})

type RepuestoFormData = z.infer<typeof repuestoSchema>

export default function RepuestoFormPage() {
  const navigate = useNavigate()
  const { id } = useParams()
  const queryClient = useQueryClient()
  const isEditing = !!id

  const { data: repuesto } = useQuery({
    queryKey: ['repuesto', id],
    queryFn: () => repuestosService.getById(id!),
    enabled: isEditing,
  })

  // Cargar todos los equipos (camiones y máquinas)
  const { data: equipos = [] } = useQuery({
    queryKey: ['equipos-todos'],
    queryFn: () => camionesService.getAll(),
  })

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<RepuestoFormData>({
    resolver: zodResolver(repuestoSchema),
    defaultValues: {
      stock_actual: 0,
      stock_minimo: 5,
      precio_unitario: 0,
    },
  })

  useEffect(() => {
    if (repuesto) {
      reset({
        codigo: repuesto.codigo,
        nombre: repuesto.nombre,
        descripcion: repuesto.descripcion || '',
        categoria: repuesto.categoria,
        precio_unitario: repuesto.precio_unitario,
        stock_actual: repuesto.stock_actual,
        stock_minimo: repuesto.stock_minimo,
        ubicacion: repuesto.ubicacion || '',
        camion_id: repuesto.camion_id || '',
      })
    }
  }, [repuesto, reset])

  // Separar camiones y máquinas
  const camiones = equipos.filter((e: Camion) => e.categoria === 'camion' && e.activo)
  const maquinas = equipos.filter((e: Camion) => e.categoria === 'maquina' && e.activo)

  const createMutation = useMutation({
    mutationFn: (data: RepuestoFormData) => repuestosService.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['repuestos'] })
      navigate('/repuestos')
    },
  })

  const updateMutation = useMutation({
    mutationFn: (data: RepuestoFormData) => repuestosService.update(id!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['repuestos'] })
      queryClient.invalidateQueries({ queryKey: ['repuesto', id] })
      navigate('/repuestos')
    },
  })

  const onSubmit = async (data: RepuestoFormData) => {
    try {
      // Convertir camion_id vacío a undefined
      const submitData = {
        ...data,
        camion_id: data.camion_id || undefined,
      }
      if (isEditing) {
        await updateMutation.mutateAsync(submitData)
      } else {
        await createMutation.mutateAsync(submitData)
      }
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Error al guardar el repuesto')
    }
  }

  const isLoading = createMutation.isPending || updateMutation.isPending

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="outline" onClick={() => navigate('/repuestos')}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Volver
        </Button>
        <div>
          <h1 className="text-3xl font-bold text-gray-900">
            {isEditing ? 'Editar Repuesto' : 'Nuevo Repuesto'}
          </h1>
          <p className="text-gray-500 mt-1">
            {isEditing ? 'Modifica los datos del repuesto' : 'Registra un nuevo repuesto en el inventario'}
          </p>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Datos del Repuesto</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Código */}
              <div className="space-y-2">
                <label htmlFor="codigo" className="text-sm font-medium">
                  Código <span className="text-red-500">*</span>
                </label>
                <Input
                  id="codigo"
                  {...register('codigo')}
                  placeholder="REP-001"
                  disabled={isEditing}
                />
                {errors.codigo && (
                  <p className="text-sm text-red-600">{errors.codigo.message}</p>
                )}
              </div>

              {/* Nombre */}
              <div className="space-y-2">
                <label htmlFor="nombre" className="text-sm font-medium">
                  Nombre <span className="text-red-500">*</span>
                </label>
                <Input
                  id="nombre"
                  {...register('nombre')}
                  placeholder="Filtro de aceite"
                />
                {errors.nombre && (
                  <p className="text-sm text-red-600">{errors.nombre.message}</p>
                )}
              </div>

              {/* Categoría */}
              <div className="space-y-2">
                <label htmlFor="categoria" className="text-sm font-medium">
                  Categoría <span className="text-red-500">*</span>
                </label>
                <select
                  id="categoria"
                  {...register('categoria')}
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                >
                  <option value="">Seleccionar categoría</option>
                  <option value="motor">Motor</option>
                  <option value="transmision">Transmisión</option>
                  <option value="frenos">Frenos</option>
                  <option value="suspension">Suspensión</option>
                  <option value="electrico">Eléctrico</option>
                  <option value="neumaticos">Neumáticos</option>
                  <option value="filtros">Filtros</option>
                  <option value="lubricantes">Lubricantes</option>
                  <option value="otros">Otros</option>
                </select>
                {errors.categoria && (
                  <p className="text-sm text-red-600">{errors.categoria.message}</p>
                )}
              </div>

              {/* Precio Unitario */}
              <div className="space-y-2">
                <label htmlFor="precio_unitario" className="text-sm font-medium">
                  Precio Unitario <span className="text-red-500">*</span>
                </label>
                <Input
                  id="precio_unitario"
                  type="number"
                  step="0.01"
                  {...register('precio_unitario', { valueAsNumber: true })}
                  placeholder="0.00"
                />
                {errors.precio_unitario && (
                  <p className="text-sm text-red-600">{errors.precio_unitario.message}</p>
                )}
              </div>

              {/* Stock Actual */}
              <div className="space-y-2">
                <label htmlFor="stock_actual" className="text-sm font-medium">
                  Stock Actual <span className="text-red-500">*</span>
                </label>
                <Input
                  id="stock_actual"
                  type="number"
                  {...register('stock_actual', { valueAsNumber: true })}
                  placeholder="0"
                />
                {errors.stock_actual && (
                  <p className="text-sm text-red-600">{errors.stock_actual.message}</p>
                )}
              </div>

              {/* Stock Mínimo */}
              <div className="space-y-2">
                <label htmlFor="stock_minimo" className="text-sm font-medium">
                  Stock Mínimo <span className="text-red-500">*</span>
                </label>
                <Input
                  id="stock_minimo"
                  type="number"
                  {...register('stock_minimo', { valueAsNumber: true })}
                  placeholder="5"
                />
                {errors.stock_minimo && (
                  <p className="text-sm text-red-600">{errors.stock_minimo.message}</p>
                )}
              </div>

              {/* Ubicación */}
              <div className="space-y-2">
                <label htmlFor="ubicacion" className="text-sm font-medium">
                  Ubicación
                </label>
                <Input
                  id="ubicacion"
                  {...register('ubicacion')}
                  placeholder="Estante A - Nivel 2"
                />
                {errors.ubicacion && (
                  <p className="text-sm text-red-600">{errors.ubicacion.message}</p>
                )}
              </div>

              {/* Asignación a Equipo */}
              <div className="space-y-2">
                <label htmlFor="camion_id" className="text-sm font-medium">
                  Asignar a Equipo (opcional)
                </label>
                <select
                  id="camion_id"
                  {...register('camion_id')}
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                >
                  <option value="">Sin asignar (uso general)</option>
                  {camiones.length > 0 && (
                    <optgroup label="🚛 Camiones">
                      {camiones.map((camion: Camion) => (
                        <option key={camion.id} value={camion.id}>
                          {camion.patente || camion.codigo_interno} - {camion.marca} {camion.modelo}
                        </option>
                      ))}
                    </optgroup>
                  )}
                  {maquinas.length > 0 && (
                    <optgroup label="⚙️ Máquinas">
                      {maquinas.map((maquina: Camion) => (
                        <option key={maquina.id} value={maquina.id}>
                          {maquina.nombre || maquina.codigo_interno} - {maquina.marca} {maquina.modelo}
                        </option>
                      ))}
                    </optgroup>
                  )}
                </select>
                <p className="text-xs text-muted-foreground">
                  Si asigna el repuesto a un equipo, solo aparecerá disponible para ese equipo al registrar servicios.
                </p>
              </div>
            </div>

            {/* Descripción */}
            <div className="space-y-2">
              <label htmlFor="descripcion" className="text-sm font-medium">
                Descripción
              </label>
              <textarea
                id="descripcion"
                {...register('descripcion')}
                rows={4}
                placeholder="Descripción detallada del repuesto..."
                className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
              />
              {errors.descripcion && (
                <p className="text-sm text-red-600">{errors.descripcion.message}</p>
              )}
            </div>

            {/* Botones */}
            <div className="flex items-center gap-4 pt-4 border-t">
              <Button type="submit" disabled={isLoading}>
                <Save className="h-4 w-4 mr-2" />
                {isLoading ? 'Guardando...' : isEditing ? 'Actualizar' : 'Crear Repuesto'}
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={() => navigate('/repuestos')}
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
