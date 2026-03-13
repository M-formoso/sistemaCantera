import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, Save, Check } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { repuestosService } from '@/services/repuestosService'
import { camionesService } from '@/services/camionesService'
import { Camion } from '@/types'

// Helper para preprocess de números (evita NaN)
const preprocessNumber = (val: unknown) =>
  val === '' || val === undefined || val === null || Number.isNaN(val) ? 0 : Number(val)

const repuestoSchema = z.object({
  codigo: z.string().min(2, 'El código debe tener al menos 2 caracteres'),
  nombre: z.string().min(3, 'El nombre debe tener al menos 3 caracteres'),
  descripcion: z.string().optional(),
  categoria: z.string().min(2, 'La categoría es requerida'),
  precio_unitario: z.preprocess(preprocessNumber, z.number().min(0, 'El precio debe ser positivo')),
  stock_actual: z.preprocess(preprocessNumber, z.number().min(0, 'El stock debe ser positivo')),
  stock_minimo: z.preprocess(preprocessNumber, z.number().min(0, 'El stock mínimo debe ser positivo')),
  ubicacion: z.string().optional(),
})

type RepuestoFormData = z.infer<typeof repuestoSchema>

export default function RepuestoFormPage() {
  const navigate = useNavigate()
  const { id } = useParams()
  const queryClient = useQueryClient()
  const isEditing = !!id

  // Estado para equipos seleccionados (N:N)
  const [equiposSeleccionados, setEquiposSeleccionados] = useState<string[]>([])

  const { data: repuesto } = useQuery({
    queryKey: ['repuesto', id],
    queryFn: () => repuestosService.getById(id!),
    enabled: isEditing,
  })

  // Cargar equipos asignados al repuesto (si está editando)
  const { data: equiposAsignados = [] } = useQuery({
    queryKey: ['repuesto-equipos', id],
    queryFn: () => repuestosService.getEquiposAsignados(id!),
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

  // Cargar datos del repuesto en edición
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
      })
    }
  }, [repuesto, reset])

  // Cargar equipos asignados cuando se carguen
  useEffect(() => {
    if (equiposAsignados.length > 0) {
      setEquiposSeleccionados(equiposAsignados.map(e => e.id))
    }
  }, [equiposAsignados])

  // Separar camiones y máquinas
  const camiones = equipos.filter((e: Camion) => e.categoria === 'camion' && e.activo)
  const maquinas = equipos.filter((e: Camion) => e.categoria === 'maquina' && e.activo)

  // Toggle selección de equipo
  const toggleEquipo = (equipoId: string) => {
    setEquiposSeleccionados(prev =>
      prev.includes(equipoId)
        ? prev.filter(id => id !== equipoId)
        : [...prev, equipoId]
    )
  }

  const createMutation = useMutation({
    mutationFn: (data: RepuestoFormData) => repuestosService.create(data),
    onSuccess: async (newRepuesto) => {
      // Si hay equipos seleccionados, asignarlos al nuevo repuesto
      if (equiposSeleccionados.length > 0 && newRepuesto.id) {
        await repuestosService.updateEquiposAsignados(newRepuesto.id, equiposSeleccionados)
      }
      queryClient.invalidateQueries({ queryKey: ['repuestos'] })
      navigate('/repuestos')
    },
  })

  const updateMutation = useMutation({
    mutationFn: (data: RepuestoFormData) => repuestosService.update(id!, data),
    onSuccess: async () => {
      // Actualizar equipos asignados
      await repuestosService.updateEquiposAsignados(id!, equiposSeleccionados)
      queryClient.invalidateQueries({ queryKey: ['repuestos'] })
      queryClient.invalidateQueries({ queryKey: ['repuesto', id] })
      queryClient.invalidateQueries({ queryKey: ['repuesto-equipos', id] })
      navigate('/repuestos')
    },
  })

  const onSubmit = async (data: RepuestoFormData) => {
    try {
      if (isEditing) {
        await updateMutation.mutateAsync(data)
      } else {
        await createMutation.mutateAsync(data)
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

            </div>

            {/* Asignación a Equipos (N:N) */}
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium">
                  Equipos Compatibles
                </label>
                <p className="text-xs text-muted-foreground mt-1">
                  Selecciona todos los equipos donde se puede usar este repuesto.
                  Si no seleccionas ninguno, será de uso general.
                </p>
              </div>

              {/* Camiones */}
              {camiones.length > 0 && (
                <div className="space-y-2">
                  <h4 className="text-sm font-medium text-gray-700">Camiones</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
                    {camiones.map((camion: Camion) => (
                      <div
                        key={camion.id}
                        onClick={() => toggleEquipo(camion.id)}
                        className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${
                          equiposSeleccionados.includes(camion.id)
                            ? 'bg-blue-50 border-blue-300'
                            : 'bg-white border-gray-200 hover:border-gray-300'
                        }`}
                      >
                        <div
                          className={`w-5 h-5 rounded border-2 flex items-center justify-center transition-colors ${
                            equiposSeleccionados.includes(camion.id)
                              ? 'bg-blue-600 border-blue-600'
                              : 'border-gray-300'
                          }`}
                        >
                          {equiposSeleccionados.includes(camion.id) && (
                            <Check className="w-3 h-3 text-white" />
                          )}
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium truncate">
                            {camion.patente || camion.codigo_interno}
                          </p>
                          <p className="text-xs text-muted-foreground truncate">
                            {camion.marca} {camion.modelo}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Máquinas */}
              {maquinas.length > 0 && (
                <div className="space-y-2">
                  <h4 className="text-sm font-medium text-gray-700">Máquinas</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
                    {maquinas.map((maquina: Camion) => (
                      <div
                        key={maquina.id}
                        onClick={() => toggleEquipo(maquina.id)}
                        className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${
                          equiposSeleccionados.includes(maquina.id)
                            ? 'bg-green-50 border-green-300'
                            : 'bg-white border-gray-200 hover:border-gray-300'
                        }`}
                      >
                        <div
                          className={`w-5 h-5 rounded border-2 flex items-center justify-center transition-colors ${
                            equiposSeleccionados.includes(maquina.id)
                              ? 'bg-green-600 border-green-600'
                              : 'border-gray-300'
                          }`}
                        >
                          {equiposSeleccionados.includes(maquina.id) && (
                            <Check className="w-3 h-3 text-white" />
                          )}
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium truncate">
                            {maquina.nombre || maquina.codigo_interno}
                          </p>
                          <p className="text-xs text-muted-foreground truncate">
                            {maquina.marca} {maquina.modelo}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {equiposSeleccionados.length > 0 && (
                <div className="flex items-center gap-2 text-sm text-blue-600">
                  <Check className="w-4 h-4" />
                  <span>{equiposSeleccionados.length} equipo(s) seleccionado(s)</span>
                  <button
                    type="button"
                    onClick={() => setEquiposSeleccionados([])}
                    className="text-red-600 hover:text-red-700 ml-2"
                  >
                    Limpiar selección
                  </button>
                </div>
              )}
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
