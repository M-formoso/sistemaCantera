import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, Save, Calculator, Printer, CheckCircle } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { pesajesService } from '@/services/pesajesService'
import { camionesService } from '@/services/camionesService'
import { formatNumber } from '@/lib/utils'
import { Pesaje } from '@/types'

const pesajeSchema = z.object({
  camion_id: z.string().min(1, 'Debe seleccionar un camión'),
  fecha: z.string().min(1, 'La fecha es requerida'),
  // Datos del transporte
  acoplado: z.string().optional(),
  transportista: z.string().optional(),
  remitente: z.string().default('LA RUFINA'),
  chofer: z.string().optional(),
  // Datos del producto
  producto: z.string().optional(),
  numero_guia: z.string().optional(),
  // Pesos
  peso_bruto: z.number().min(1, 'El peso bruto debe ser mayor a 0'),
  peso_tara: z.number().min(1, 'El peso tara debe ser mayor a 0'),
  // Destino
  material: z.string().optional(),
  cliente_destino: z.string().optional(),
  // Operación
  operario: z.string().optional(),
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
  const [createdPesaje, setCreatedPesaje] = useState<Pesaje | null>(null)

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
      remitente: 'LA RUFINA',
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
        acoplado: pesaje.acoplado || '',
        transportista: pesaje.transportista || '',
        remitente: pesaje.remitente || 'LA RUFINA',
        chofer: pesaje.chofer || '',
        producto: pesaje.producto || '',
        numero_guia: pesaje.numero_guia || '',
        peso_bruto: pesaje.peso_bruto,
        peso_tara: pesaje.peso_tara,
        material: pesaje.material || '',
        cliente_destino: pesaje.cliente_destino || '',
        operario: pesaje.operario || '',
        observaciones: pesaje.observaciones || '',
      })
    }
  }, [pesaje, reset])

  const createMutation = useMutation({
    mutationFn: (data: PesajeFormData) => pesajesService.create(data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['pesajes'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard-resumen'] })
      setCreatedPesaje(data)
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
      const detail = error.response?.data?.detail
      let errorMessage = 'Error al guardar el pesaje'

      if (typeof detail === 'string') {
        errorMessage = detail
      } else if (Array.isArray(detail)) {
        // Errores de validación de Pydantic
        errorMessage = detail.map((e: any) => e.msg || e.message || JSON.stringify(e)).join('\n')
      } else if (typeof detail === 'object' && detail !== null) {
        errorMessage = detail.msg || detail.message || JSON.stringify(detail)
      }

      alert(errorMessage)
    }
  }

  const isLoading = createMutation.isPending || updateMutation.isPending

  const handleDownloadPDF = async () => {
    if (!createdPesaje) return
    try {
      await pesajesService.downloadTicketPDF(createdPesaje.id, createdPesaje.numero_pesaje)
    } catch (error) {
      alert('Error al descargar el ticket PDF')
    }
  }

  // Pantalla de éxito después de crear el pesaje
  if (createdPesaje) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <Card className="max-w-md w-full">
          <CardContent className="pt-6 text-center space-y-6">
            <div className="mx-auto w-16 h-16 bg-green-100 rounded-full flex items-center justify-center">
              <CheckCircle className="h-10 w-10 text-green-600" />
            </div>

            <div>
              <h2 className="text-2xl font-bold text-gray-900">Pesaje Registrado</h2>
              <p className="text-gray-500 mt-2">
                Ticket #{createdPesaje.numero_pesaje}
              </p>
            </div>

            <div className="bg-gray-50 rounded-lg p-4 space-y-2 text-left">
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Camión:</span>
                <span className="font-medium">{createdPesaje.camion_patente}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Material:</span>
                <span className="font-medium">{createdPesaje.material || '-'}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Peso Neto:</span>
                <span className="font-bold text-green-600">
                  {formatNumber(createdPesaje.peso_neto)} kg ({formatNumber(createdPesaje.peso_neto / 1000, 2)} t)
                </span>
              </div>
            </div>

            <div className="flex flex-col gap-3">
              <Button onClick={handleDownloadPDF} className="w-full bg-green-600 hover:bg-green-700">
                <Printer className="h-4 w-4 mr-2" />
                Imprimir Ticket PDF
              </Button>
              <Button
                variant="outline"
                onClick={() => navigate('/pesajes')}
                className="w-full"
              >
                Volver a Pesajes
              </Button>
              <Button
                variant="ghost"
                onClick={() => {
                  setCreatedPesaje(null)
                  reset({
                    fecha: new Date().toISOString().split('T')[0],
                    peso_bruto: 0,
                    peso_tara: 0,
                    remitente: 'LA RUFINA',
                    camion_id: '',
                    acoplado: '',
                    transportista: '',
                    chofer: '',
                    producto: '',
                    numero_guia: '',
                    material: '',
                    cliente_destino: '',
                    operario: '',
                    observaciones: '',
                  })
                }}
                className="w-full"
              >
                Registrar Nuevo Pesaje
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

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
                {/* Sección: Datos Básicos */}
                <div>
                  <h3 className="text-sm font-semibold text-gray-700 mb-3 pb-2 border-b">Datos Básicos</h3>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
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

                    {/* Acoplado */}
                    <div className="space-y-2">
                      <label htmlFor="acoplado" className="text-sm font-medium">Acoplado</label>
                      <Input
                        id="acoplado"
                        {...register('acoplado')}
                        placeholder="Patente acoplado"
                      />
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
                  </div>
                </div>

                {/* Sección: Datos del Transporte */}
                <div>
                  <h3 className="text-sm font-semibold text-gray-700 mb-3 pb-2 border-b">Datos del Transporte</h3>
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    {/* Transportista */}
                    <div className="space-y-2">
                      <label htmlFor="transportista" className="text-sm font-medium">Transportista</label>
                      <Input
                        id="transportista"
                        {...register('transportista')}
                        placeholder="Nombre transportista"
                      />
                    </div>

                    {/* Remitente */}
                    <div className="space-y-2">
                      <label htmlFor="remitente" className="text-sm font-medium">Remitente</label>
                      <Input
                        id="remitente"
                        {...register('remitente')}
                        placeholder="LA RUFINA"
                      />
                    </div>

                    {/* Chofer */}
                    <div className="space-y-2">
                      <label htmlFor="chofer" className="text-sm font-medium">Chofer</label>
                      <Input
                        id="chofer"
                        {...register('chofer')}
                        placeholder="Nombre del chofer"
                      />
                    </div>

                    {/* Destinatario */}
                    <div className="space-y-2">
                      <label htmlFor="cliente_destino" className="text-sm font-medium">Destinatario</label>
                      <Input
                        id="cliente_destino"
                        {...register('cliente_destino')}
                        placeholder="Nombre del destinatario"
                      />
                    </div>
                  </div>
                </div>

                {/* Sección: Producto */}
                <div>
                  <h3 className="text-sm font-semibold text-gray-700 mb-3 pb-2 border-b">Producto</h3>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {/* Producto/Material */}
                    <div className="space-y-2">
                      <label htmlFor="producto" className="text-sm font-medium">Código Producto</label>
                      <Input
                        id="producto"
                        {...register('producto')}
                        placeholder="Ej: 020"
                      />
                    </div>

                    {/* Material */}
                    <div className="space-y-2">
                      <label htmlFor="material" className="text-sm font-medium">Material</label>
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
                    </div>

                    {/* Número de Guía */}
                    <div className="space-y-2">
                      <label htmlFor="numero_guia" className="text-sm font-medium">Nro. Guía</label>
                      <Input
                        id="numero_guia"
                        {...register('numero_guia')}
                        placeholder="Número de guía"
                      />
                    </div>
                  </div>
                </div>

                {/* Sección: Pesos */}
                <div>
                  <h3 className="text-sm font-semibold text-gray-700 mb-3 pb-2 border-b">Pesos</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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
                        placeholder="53540"
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
                        placeholder="16920"
                      />
                      {errors.peso_tara && (
                        <p className="text-sm text-red-600">{errors.peso_tara.message}</p>
                      )}
                    </div>
                  </div>
                </div>

                {/* Sección: Operación */}
                <div>
                  <h3 className="text-sm font-semibold text-gray-700 mb-3 pb-2 border-b">Operación</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* Operario */}
                    <div className="space-y-2">
                      <label htmlFor="operario" className="text-sm font-medium">Operario</label>
                      <Input
                        id="operario"
                        {...register('operario')}
                        placeholder="Nombre del operario"
                      />
                    </div>
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
