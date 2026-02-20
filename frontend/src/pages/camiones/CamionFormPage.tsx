import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, Save, Truck, Cog, FileText, Shield } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { camionesService } from '@/services/camionesService'

const camionSchema = z.object({
  categoria: z.enum(['camion', 'maquina']),
  patente: z.string().optional(),
  nombre: z.string().optional(),
  codigo_interno: z.string().optional(),
  marca: z.string().optional(),
  modelo: z.string().optional(),
  año: z.number().min(1950).max(new Date().getFullYear() + 1).optional().nullable(),
  numero_serie: z.string().optional(),
  tipo: z.enum(['volcador', 'acoplado', 'mixer', 'otro']).optional(),
  tipo_maquina: z.string().optional(),
  estado: z.enum(['operativo', 'en_servicio', 'fuera_servicio']),
  kilometraje_actual: z.number().min(0).optional(),
  horometro_actual: z.number().min(0).optional(),
  horas_promedio_diarias: z.number().min(0).optional(),
  chofer_habitual: z.string().optional(),
  observaciones: z.string().optional(),
  intervalo_servicio_km: z.number().min(100).optional().nullable(),
  intervalo_servicio_horas: z.number().min(10).optional().nullable(),
  proximo_servicio_km: z.number().min(0).optional().nullable(),
  proximo_servicio_horas: z.number().min(0).optional().nullable(),
  // Documentación
  tarjeta_verde_url: z.string().optional(),
  tarjeta_verde_vencimiento: z.string().optional(),
  seguro_url: z.string().optional(),
  seguro_compania: z.string().optional(),
  seguro_poliza: z.string().optional(),
  seguro_vencimiento: z.string().optional(),
  vtv_url: z.string().optional(),
  vtv_vencimiento: z.string().optional(),
  cedula_url: z.string().optional(),
})

type CamionFormData = z.infer<typeof camionSchema>

const TIPOS_MAQUINA = [
  { value: 'pala_cargadora', label: 'Pala Cargadora' },
  { value: 'retroexcavadora', label: 'Retroexcavadora' },
  { value: 'excavadora', label: 'Excavadora' },
  { value: 'motoniveladora', label: 'Motoniveladora' },
  { value: 'compactadora', label: 'Compactadora' },
  { value: 'trituradora', label: 'Trituradora' },
  { value: 'generador', label: 'Generador' },
  { value: 'bomba', label: 'Bomba' },
  { value: 'otro', label: 'Otro' },
]

export default function CamionFormPage() {
  const navigate = useNavigate()
  const { id } = useParams()
  const queryClient = useQueryClient()
  const isEditing = !!id
  const [activeTab, setActiveTab] = useState<'general' | 'servicio' | 'documentos'>('general')

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
    watch,
    setValue,
  } = useForm<CamionFormData>({
    resolver: zodResolver(camionSchema),
    defaultValues: {
      categoria: 'camion',
      estado: 'operativo',
      kilometraje_actual: 0,
      horometro_actual: 0,
      horas_promedio_diarias: 0,
      intervalo_servicio_km: 10000,
      intervalo_servicio_horas: 250,
    },
  })

  const categoria = watch('categoria')

  useEffect(() => {
    if (camion) {
      reset({
        categoria: (camion.categoria as 'camion' | 'maquina') || 'camion',
        patente: camion.patente || '',
        nombre: camion.nombre || '',
        codigo_interno: camion.codigo_interno || '',
        marca: camion.marca || '',
        modelo: camion.modelo || '',
        año: camion.año || undefined,
        numero_serie: camion.numero_serie || '',
        tipo: camion.tipo || 'volcador',
        tipo_maquina: camion.tipo_maquina || '',
        estado: camion.estado,
        kilometraje_actual: camion.kilometraje_actual || 0,
        horometro_actual: camion.horometro_actual || 0,
        horas_promedio_diarias: camion.horas_promedio_diarias || 0,
        chofer_habitual: camion.chofer_habitual || '',
        observaciones: camion.observaciones || '',
        intervalo_servicio_km: camion.intervalo_servicio_km || 10000,
        intervalo_servicio_horas: camion.intervalo_servicio_horas || 250,
        proximo_servicio_km: camion.proximo_servicio_km || undefined,
        proximo_servicio_horas: camion.proximo_servicio_horas || undefined,
        tarjeta_verde_url: camion.tarjeta_verde_url || '',
        tarjeta_verde_vencimiento: camion.tarjeta_verde_vencimiento || '',
        seguro_url: camion.seguro_url || '',
        seguro_compania: camion.seguro_compania || '',
        seguro_poliza: camion.seguro_poliza || '',
        seguro_vencimiento: camion.seguro_vencimiento || '',
        vtv_url: camion.vtv_url || '',
        vtv_vencimiento: camion.vtv_vencimiento || '',
        cedula_url: camion.cedula_url || '',
      })
    }
  }, [camion, reset])

  const createMutation = useMutation({
    mutationFn: (data: CamionFormData) => {
      const cleanData: Record<string, unknown> = { ...data }
      // Limpiar campos vacíos
      Object.keys(cleanData).forEach(key => {
        if (cleanData[key] === '' || cleanData[key] === null) {
          delete cleanData[key]
        }
      })
      return camionesService.create(cleanData)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['camiones'] })
      navigate('/camiones')
    },
  })

  const updateMutation = useMutation({
    mutationFn: (data: CamionFormData) => {
      const cleanData: Record<string, unknown> = { ...data }
      Object.keys(cleanData).forEach(key => {
        if (cleanData[key] === '' || cleanData[key] === null) {
          delete cleanData[key]
        }
      })
      return camionesService.update(id!, cleanData)
    },
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
    } catch (error: unknown) {
      const err = error as { response?: { data?: { detail?: string } } }
      alert(err.response?.data?.detail || 'Error al guardar')
    }
  }

  const isLoading = createMutation.isPending || updateMutation.isPending

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center gap-3 sm:gap-4">
        <Button variant="outline" onClick={() => navigate('/camiones')} className="w-fit">
          <ArrowLeft className="h-4 w-4 mr-2" />
          Volver
        </Button>
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">
            {isEditing ? 'Editar Equipo' : 'Nuevo Equipo'}
          </h1>
          <p className="text-gray-500 mt-1 text-sm sm:text-base">
            {isEditing ? 'Modifica los datos del equipo' : 'Registra un nuevo camión o máquina'}
          </p>
        </div>
      </div>

      {/* Selector de Categoría */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Tipo de Equipo</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4">
            <Button
              type="button"
              variant={categoria === 'camion' ? 'default' : 'outline'}
              className="flex-1"
              onClick={() => setValue('categoria', 'camion')}
            >
              <Truck className="h-4 w-4 mr-2" />
              Camión
            </Button>
            <Button
              type="button"
              variant={categoria === 'maquina' ? 'default' : 'outline'}
              className="flex-1"
              onClick={() => setValue('categoria', 'maquina')}
            >
              <Cog className="h-4 w-4 mr-2" />
              Máquina
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Tabs */}
      <div className="flex border-b">
        <button
          type="button"
          className={`px-4 py-2 font-medium text-sm border-b-2 ${activeTab === 'general' ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700'}`}
          onClick={() => setActiveTab('general')}
        >
          Datos Generales
        </button>
        <button
          type="button"
          className={`px-4 py-2 font-medium text-sm border-b-2 ${activeTab === 'servicio' ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700'}`}
          onClick={() => setActiveTab('servicio')}
        >
          Servicio/Mantenimiento
        </button>
        <button
          type="button"
          className={`px-4 py-2 font-medium text-sm border-b-2 ${activeTab === 'documentos' ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700'}`}
          onClick={() => setActiveTab('documentos')}
        >
          Documentación
        </button>
      </div>

      <form onSubmit={handleSubmit(onSubmit)}>
        {/* Tab: Datos Generales */}
        {activeTab === 'general' && (
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                {categoria === 'camion' ? <Truck className="h-5 w-5" /> : <Cog className="h-5 w-5" />}
                Datos del {categoria === 'camion' ? 'Camión' : 'Máquina'}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Identificación */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {categoria === 'camion' ? (
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Patente *</label>
                    <Input {...register('patente')} placeholder="ABC123" />
                    {errors.patente && <p className="text-sm text-red-600">{errors.patente.message}</p>}
                  </div>
                ) : (
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Nombre *</label>
                    <Input {...register('nombre')} placeholder="Pala CAT 950" />
                    {errors.nombre && <p className="text-sm text-red-600">{errors.nombre.message}</p>}
                  </div>
                )}
                <div className="space-y-2">
                  <label className="text-sm font-medium">Código Interno</label>
                  <Input {...register('codigo_interno')} placeholder="EQ-001" />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">N° Serie/Chasis</label>
                  <Input {...register('numero_serie')} placeholder="VIN o N° Serie" />
                </div>
              </div>

              {/* Marca, Modelo, Año */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Marca</label>
                  <Input {...register('marca')} placeholder={categoria === 'camion' ? 'Mercedes-Benz' : 'Caterpillar'} />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Modelo</label>
                  <Input {...register('modelo')} placeholder={categoria === 'camion' ? 'Actros 2651' : '950H'} />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Año</label>
                  <Input type="number" {...register('año', { valueAsNumber: true })} placeholder="2020" />
                </div>
              </div>

              {/* Tipo específico */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {categoria === 'camion' ? (
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Tipo de Camión</label>
                    <select {...register('tipo')} className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm">
                      <option value="volcador">Volcador</option>
                      <option value="acoplado">Acoplado</option>
                      <option value="mixer">Mixer</option>
                      <option value="otro">Otro</option>
                    </select>
                  </div>
                ) : (
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Tipo de Máquina</label>
                    <select {...register('tipo_maquina')} className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm">
                      <option value="">Seleccionar...</option>
                      {TIPOS_MAQUINA.map(t => (
                        <option key={t.value} value={t.value}>{t.label}</option>
                      ))}
                    </select>
                  </div>
                )}
                <div className="space-y-2">
                  <label className="text-sm font-medium">Estado</label>
                  <select {...register('estado')} className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm">
                    <option value="operativo">Operativo</option>
                    <option value="en_servicio">En Servicio</option>
                    <option value="fuera_servicio">Fuera de Servicio</option>
                  </select>
                </div>
              </div>

              {/* Métricas */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {categoria === 'camion' ? (
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Kilometraje Actual</label>
                    <Input type="number" {...register('kilometraje_actual', { valueAsNumber: true })} placeholder="50000" />
                  </div>
                ) : (
                  <>
                    <div className="space-y-2">
                      <label className="text-sm font-medium">Horómetro Actual (horas)</label>
                      <Input type="number" step="0.1" {...register('horometro_actual', { valueAsNumber: true })} placeholder="1500" />
                    </div>
                    <div className="space-y-2">
                      <label className="text-sm font-medium">Horas Promedio/Día</label>
                      <Input type="number" step="0.1" {...register('horas_promedio_diarias', { valueAsNumber: true })} placeholder="8" />
                    </div>
                  </>
                )}
                <div className="space-y-2">
                  <label className="text-sm font-medium">Operador Habitual</label>
                  <Input {...register('chofer_habitual')} placeholder="Nombre del operador" />
                </div>
              </div>

              {/* Observaciones */}
              <div className="space-y-2">
                <label className="text-sm font-medium">Observaciones</label>
                <textarea
                  {...register('observaciones')}
                  rows={3}
                  placeholder="Notas adicionales..."
                  className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                />
              </div>
            </CardContent>
          </Card>
        )}

        {/* Tab: Servicio/Mantenimiento */}
        {activeTab === 'servicio' && (
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <Cog className="h-5 w-5" />
                Configuración de Servicio
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {categoria === 'camion' ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Intervalo de Servicio (km)</label>
                    <Input type="number" {...register('intervalo_servicio_km', { valueAsNumber: true })} placeholder="10000" />
                    <p className="text-xs text-gray-500">Cada cuántos km se debe hacer servicio</p>
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Próximo Servicio (km)</label>
                    <Input type="number" {...register('proximo_servicio_km', { valueAsNumber: true })} placeholder="60000" />
                    <p className="text-xs text-gray-500">Se actualiza al registrar servicios</p>
                  </div>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Intervalo de Servicio (horas)</label>
                    <Input type="number" {...register('intervalo_servicio_horas', { valueAsNumber: true })} placeholder="250" />
                    <p className="text-xs text-gray-500">Cada cuántas horas se debe hacer servicio</p>
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Próximo Servicio (horas)</label>
                    <Input type="number" step="0.1" {...register('proximo_servicio_horas', { valueAsNumber: true })} placeholder="1750" />
                    <p className="text-xs text-gray-500">Se actualiza al registrar servicios</p>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* Tab: Documentación */}
        {activeTab === 'documentos' && (
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <FileText className="h-5 w-5" />
                Documentación del Equipo
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Tarjeta Verde */}
              <div className="p-4 border rounded-lg space-y-4">
                <h3 className="font-medium flex items-center gap-2">
                  <Shield className="h-4 w-4 text-green-600" />
                  Tarjeta Verde
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <label className="text-sm font-medium">URL del Documento</label>
                    <Input {...register('tarjeta_verde_url')} placeholder="https://..." />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Fecha de Vencimiento</label>
                    <Input type="date" {...register('tarjeta_verde_vencimiento')} />
                  </div>
                </div>
              </div>

              {/* Seguro */}
              <div className="p-4 border rounded-lg space-y-4">
                <h3 className="font-medium flex items-center gap-2">
                  <Shield className="h-4 w-4 text-blue-600" />
                  Seguro
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Compañía</label>
                    <Input {...register('seguro_compania')} placeholder="La Caja, Federación Patronal, etc." />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium">N° de Póliza</label>
                    <Input {...register('seguro_poliza')} placeholder="123456789" />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium">URL del Documento</label>
                    <Input {...register('seguro_url')} placeholder="https://..." />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Fecha de Vencimiento</label>
                    <Input type="date" {...register('seguro_vencimiento')} />
                  </div>
                </div>
              </div>

              {/* VTV */}
              {categoria === 'camion' && (
                <div className="p-4 border rounded-lg space-y-4">
                  <h3 className="font-medium flex items-center gap-2">
                    <Shield className="h-4 w-4 text-orange-600" />
                    VTV (Verificación Técnica Vehicular)
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <label className="text-sm font-medium">URL del Documento</label>
                      <Input {...register('vtv_url')} placeholder="https://..." />
                    </div>
                    <div className="space-y-2">
                      <label className="text-sm font-medium">Fecha de Vencimiento</label>
                      <Input type="date" {...register('vtv_vencimiento')} />
                    </div>
                  </div>
                </div>
              )}

              {/* Cédula */}
              {categoria === 'camion' && (
                <div className="p-4 border rounded-lg space-y-4">
                  <h3 className="font-medium flex items-center gap-2">
                    <FileText className="h-4 w-4 text-purple-600" />
                    Cédula Verde/Azul
                  </h3>
                  <div className="space-y-2">
                    <label className="text-sm font-medium">URL del Documento</label>
                    <Input {...register('cedula_url')} placeholder="https://..." />
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* Botones */}
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 sm:gap-4 pt-4">
          <Button type="submit" disabled={isLoading} className="w-full sm:w-auto">
            <Save className="h-4 w-4 mr-2" />
            {isLoading ? 'Guardando...' : isEditing ? 'Actualizar' : 'Crear Equipo'}
          </Button>
          <Button
            type="button"
            variant="outline"
            onClick={() => navigate('/camiones')}
            disabled={isLoading}
            className="w-full sm:w-auto"
          >
            Cancelar
          </Button>
        </div>
      </form>
    </div>
  )
}
