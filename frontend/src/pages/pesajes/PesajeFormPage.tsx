import { useEffect, useState, useCallback } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useForm, Controller } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, Save, Calculator, Printer, CheckCircle, Truck, Building2, Plus, UserCheck, DollarSign, ClipboardList, Scale, Loader2 } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { pesajesService } from '@/services/pesajesService'
import { camionesService } from '@/services/camionesService'
import { empresasService } from '@/services/empresasService'
import { ordenEntregaService } from '@/services/ordenEntregaService'
import { balanzaService } from '@/services/balanzaService'
import { formatNumber, getTodayLocalDate } from '@/lib/utils'
import { Pesaje, Empresa, TipoEntrega, EmpresaCreate } from '@/types'
import { useIsAdmin } from '@/hooks/useIsAdmin'

// Lista de materiales disponibles
const MATERIALES_DISPONIBLES = [
  '10.30',
  '6.19',
  '0.20',
  '6.12',
  'relleno',
  'binder',
  '0.6',
  'piedra partida',
  'suelo arena',
  'retiro',
]

// Helper para preprocess de números
const preprocessNumber = (val: unknown) =>
  val === '' || val === undefined || val === null || Number.isNaN(val) ? 0 : Number(val)

const preprocessOptionalNumber = (val: unknown) =>
  val === '' || val === undefined || val === null || Number.isNaN(val) ? undefined : Number(val)

const pesajeSchema = z.object({
  tipo_entrega: z.enum(['propio', 'transportista']),
  // Camión propio (opcional si es transportista)
  camion_id: z.string().optional(),
  // Transportista externo
  transportista_id: z.string().optional(),
  patente_externa: z.string().optional(),
  transportista: z.string().optional(),
  // Cliente
  cliente_id: z.string().optional(),
  cliente_nombre: z.string().optional(),
  // Datos comunes
  fecha: z.string().min(1, 'La fecha es requerida'),
  acoplado: z.string().optional(),
  chofer: z.string().optional(),
  // Pesos - con preprocess para manejar NaN
  peso_bruto: z.preprocess(preprocessNumber, z.number().min(1, 'El peso bruto debe ser mayor a 0')),
  peso_tara: z.preprocess(preprocessNumber, z.number().min(1, 'El peso tara debe ser mayor a 0')),
  // Material
  material: z.string().optional(),
  // Operación
  operario: z.string().optional(),
  observaciones: z.string().optional(),
  // Importe - con preprocess para manejar NaN
  precio_unitario: z.preprocess(preprocessOptionalNumber, z.number().min(0).optional()),
  flete: z.preprocess(preprocessOptionalNumber, z.number().min(0).optional()),
  precio_fijo: z.preprocess(preprocessOptionalNumber, z.number().min(0).optional()),
  importe_total: z.preprocess(preprocessOptionalNumber, z.number().min(0).optional()),
  // Orden de entrega
  orden_entrega_id: z.string().optional(),
}).refine((data) => data.peso_bruto > data.peso_tara, {
  message: 'El peso bruto debe ser mayor al peso tara',
  path: ['peso_bruto'],
}).refine((data) => {
  if (data.tipo_entrega === 'propio') {
    return !!data.camion_id
  }
  return true
}, {
  message: 'Debe seleccionar un camión propio',
  path: ['camion_id'],
}).refine((data) => {
  if (data.tipo_entrega === 'transportista') {
    return !!data.patente_externa
  }
  return true
}, {
  message: 'Debe ingresar la patente del camión externo',
  path: ['patente_externa'],
})

type PesajeFormData = z.infer<typeof pesajeSchema>

export default function PesajeFormPage() {
  const navigate = useNavigate()
  const { id } = useParams()
  const queryClient = useQueryClient()
  const isEditing = !!id
  const isAdmin = useIsAdmin()

  const [pesoNeto, setPesoNeto] = useState(0)
  const [importeCalculado, setImporteCalculado] = useState(0)
  const [createdPesaje, setCreatedPesaje] = useState<Pesaje | null>(null)

  // Estados para autocompletado
  const [transportistaBusqueda, setTransportistaBusqueda] = useState('')
  const [clienteBusqueda, setClienteBusqueda] = useState('')
  const [transportistaSugerencias, setTransportistaSugerencias] = useState<Empresa[]>([])
  const [clienteSugerencias, setClienteSugerencias] = useState<Empresa[]>([])
  const [showTransportistaSugerencias, setShowTransportistaSugerencias] = useState(false)
  const [showClienteSugerencias, setShowClienteSugerencias] = useState(false)

  // Modal para crear nueva empresa
  const [showNuevaEmpresaModal, setShowNuevaEmpresaModal] = useState(false)
  const [nuevaEmpresaTipo, setNuevaEmpresaTipo] = useState<'cliente' | 'transportista'>('cliente')
  const [nuevaEmpresaNombre, setNuevaEmpresaNombre] = useState('')

  // Estado para la balanza
  const [leyendoBalanza, setLeyendoBalanza] = useState<'bruto' | 'tara' | null>(null)
  const [balanzaError, setBalanzaError] = useState<string | null>(null)

  const { data: pesaje } = useQuery({
    queryKey: ['pesaje', id],
    queryFn: () => pesajesService.getById(id!),
    enabled: isEditing,
  })

  const { data: camiones = [] } = useQuery({
    queryKey: ['camiones'],
    queryFn: () => camionesService.getAll(true),
  })

  const { data: ordenesPendientes = [] } = useQuery({
    queryKey: ['ordenes-pendientes'],
    queryFn: () => ordenEntregaService.getOrdenesPendientes(),
  })

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
    watch,
    setValue,
    control,
  } = useForm<PesajeFormData>({
    resolver: zodResolver(pesajeSchema),
    defaultValues: {
      tipo_entrega: 'propio',
      fecha: getTodayLocalDate(),
      peso_bruto: 0,
      peso_tara: 0,
    },
  })

  const tipoEntrega = watch('tipo_entrega')
  const pesoBruto = watch('peso_bruto')
  const pesoTara = watch('peso_tara')
  const precioUnitario = watch('precio_unitario')
  const fleteVal = watch('flete')
  const precioFijoVal = watch('precio_fijo')

  useEffect(() => {
    const bruto = Number(pesoBruto) || 0
    const tara = Number(pesoTara) || 0
    const neto = bruto > tara ? bruto - tara : 0
    setPesoNeto(neto)

    // Calcular importe automáticamente según escenario:
    // 1. Si hay precio_fijo: importe = precio_fijo
    // 2. Si hay precio_unitario: importe = (toneladas * precio_unitario) + flete
    const precioFijo = Number(precioFijoVal) || 0
    const precio = Number(precioUnitario) || 0
    const flete = Number(fleteVal) || 0

    if (precioFijo > 0) {
      setImporteCalculado(precioFijo)
      setValue('importe_total', precioFijo)
    } else if (precio > 0 && neto > 0) {
      const toneladas = neto / 1000
      const importe = toneladas * precio + flete
      setImporteCalculado(importe)
      setValue('importe_total', Math.round(importe * 100) / 100)
    } else {
      setImporteCalculado(0)
    }
  }, [pesoBruto, pesoTara, precioUnitario, fleteVal, precioFijoVal, setValue])

  useEffect(() => {
    if (pesaje) {
      reset({
        tipo_entrega: (pesaje.tipo_entrega as TipoEntrega) || 'propio',
        camion_id: pesaje.camion_id || '',
        transportista_id: pesaje.transportista_id || '',
        patente_externa: pesaje.patente_externa || '',
        transportista: pesaje.transportista || '',
        cliente_id: pesaje.cliente_id || '',
        cliente_nombre: pesaje.cliente_nombre || '',
        fecha: pesaje.fecha.split('T')[0],
        acoplado: pesaje.acoplado || '',
        chofer: pesaje.chofer || '',
        peso_bruto: pesaje.peso_bruto,
        peso_tara: pesaje.peso_tara,
        material: pesaje.material || '',
        operario: pesaje.operario || '',
        observaciones: pesaje.observaciones || '',
        precio_unitario: pesaje.precio_unitario || undefined,
        flete: pesaje.flete || undefined,
        precio_fijo: pesaje.precio_fijo || undefined,
        importe_total: pesaje.importe_total || undefined,
      })
      if (pesaje.transportista_nombre) {
        setTransportistaBusqueda(pesaje.transportista_nombre)
      }
      if (pesaje.cliente_nombre) {
        setClienteBusqueda(pesaje.cliente_nombre)
      }
    }
  }, [pesaje, reset])

  // Buscar transportistas
  const buscarTransportistas = useCallback(async (nombre: string) => {
    if (nombre.length >= 2) {
      try {
        const resultados = await empresasService.buscar(nombre, 'transportista')
        setTransportistaSugerencias(resultados)
        setShowTransportistaSugerencias(true)
      } catch {
        setTransportistaSugerencias([])
      }
    } else {
      setTransportistaSugerencias([])
      setShowTransportistaSugerencias(false)
    }
  }, [])

  // Buscar clientes
  const buscarClientes = useCallback(async (nombre: string) => {
    if (nombre.length >= 2) {
      try {
        const resultados = await empresasService.buscar(nombre, 'cliente')
        setClienteSugerencias(resultados)
        setShowClienteSugerencias(true)
      } catch {
        setClienteSugerencias([])
      }
    } else {
      setClienteSugerencias([])
      setShowClienteSugerencias(false)
    }
  }, [])

  // Debounce para búsquedas
  useEffect(() => {
    const timer = setTimeout(() => {
      if (transportistaBusqueda) {
        buscarTransportistas(transportistaBusqueda)
      }
    }, 300)
    return () => clearTimeout(timer)
  }, [transportistaBusqueda, buscarTransportistas])

  useEffect(() => {
    const timer = setTimeout(() => {
      if (clienteBusqueda) {
        buscarClientes(clienteBusqueda)
      }
    }, 300)
    return () => clearTimeout(timer)
  }, [clienteBusqueda, buscarClientes])

  const seleccionarTransportista = (empresa: Empresa) => {
    setValue('transportista_id', empresa.id)
    setValue('transportista', empresa.nombre)
    setTransportistaBusqueda(empresa.nombre)
    setShowTransportistaSugerencias(false)
  }

  const seleccionarCliente = (empresa: Empresa) => {
    setValue('cliente_id', empresa.id)
    setValue('cliente_nombre', empresa.nombre)
    setClienteBusqueda(empresa.nombre)
    setShowClienteSugerencias(false)
  }

  // Crear nueva empresa
  const createEmpresaMutation = useMutation({
    mutationFn: (data: EmpresaCreate) => empresasService.create(data),
    onSuccess: (empresa) => {
      queryClient.invalidateQueries({ queryKey: ['empresas'] })
      if (nuevaEmpresaTipo === 'transportista') {
        seleccionarTransportista(empresa)
      } else {
        seleccionarCliente(empresa)
      }
      setShowNuevaEmpresaModal(false)
      setNuevaEmpresaNombre('')
    },
  })

  const handleCrearNuevaEmpresa = async () => {
    if (!nuevaEmpresaNombre.trim()) {
      alert('Debe ingresar un nombre')
      return
    }
    try {
      await createEmpresaMutation.mutateAsync({
        nombre: nuevaEmpresaNombre.trim(),
        tipo: nuevaEmpresaTipo,
      })
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Error al crear la empresa')
    }
  }

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
      // Limpiar campos según tipo de entrega
      const cleanData: any = { ...data }

      if (data.tipo_entrega === 'propio') {
        delete cleanData.transportista_id
        delete cleanData.patente_externa
        delete cleanData.transportista
      } else {
        delete cleanData.camion_id
      }

      // Limpiar campos UUID vacíos para evitar errores de validación
      if (!cleanData.cliente_id || cleanData.cliente_id === '') {
        delete cleanData.cliente_id
      }
      if (!cleanData.transportista_id || cleanData.transportista_id === '') {
        delete cleanData.transportista_id
      }
      if (!cleanData.camion_id || cleanData.camion_id === '') {
        delete cleanData.camion_id
      }
      if (!cleanData.orden_entrega_id || cleanData.orden_entrega_id === '') {
        delete cleanData.orden_entrega_id
      }

      // Limpiar campos numéricos que son 0 o NaN (opcionales)
      if (!cleanData.precio_unitario || cleanData.precio_unitario === 0 || isNaN(cleanData.precio_unitario)) {
        delete cleanData.precio_unitario
      }
      if (!cleanData.flete || cleanData.flete === 0 || isNaN(cleanData.flete)) {
        delete cleanData.flete
      }
      if (!cleanData.precio_fijo || cleanData.precio_fijo === 0 || isNaN(cleanData.precio_fijo)) {
        delete cleanData.precio_fijo
      }
      if (!cleanData.importe_total || cleanData.importe_total === 0 || isNaN(cleanData.importe_total)) {
        delete cleanData.importe_total
      }

      if (isEditing) {
        await updateMutation.mutateAsync(cleanData)
      } else {
        await createMutation.mutateAsync(cleanData)
      }
    } catch (error: any) {
      const detail = error.response?.data?.detail
      let errorMessage = 'Error al guardar el pesaje'

      if (typeof detail === 'string') {
        errorMessage = detail
      } else if (Array.isArray(detail)) {
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

  // Leer peso de la balanza
  const leerBalanza = async (tipo: 'bruto' | 'tara') => {
    setLeyendoBalanza(tipo)
    setBalanzaError(null)

    try {
      const resultado = await balanzaService.getPeso()

      if (resultado.error) {
        setBalanzaError(resultado.error)
        return
      }

      if (!resultado.conectado) {
        setBalanzaError('Balanza no conectada. Verifique que el servidor de balanza esté ejecutándose.')
        return
      }

      if (resultado.peso <= 0) {
        setBalanzaError('El peso leído es 0. Verifique que el camión esté sobre la balanza.')
        return
      }

      // Asignar el peso al campo correspondiente
      if (tipo === 'bruto') {
        setValue('peso_bruto', resultado.peso)
      } else {
        setValue('peso_tara', resultado.peso)
      }

    } catch (error) {
      setBalanzaError('Error al conectar con la balanza')
    } finally {
      setLeyendoBalanza(null)
    }
  }

  // Pantalla de éxito después de crear el pesaje
  if (createdPesaje) {
    const patenteMostrar = createdPesaje.tipo_entrega === 'propio'
      ? createdPesaje.camion_patente
      : createdPesaje.patente_externa

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
                <span className="text-gray-500">Tipo:</span>
                <span className="font-medium">
                  {createdPesaje.tipo_entrega === 'propio' ? 'Camión Propio' : 'Transportista'}
                </span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Patente:</span>
                <span className="font-medium">{patenteMostrar || '-'}</span>
              </div>
              {createdPesaje.cliente_nombre && (
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">Cliente:</span>
                  <span className="font-medium">{createdPesaje.cliente_nombre}</span>
                </div>
              )}
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Material:</span>
                <span className="font-medium">{createdPesaje.material || '-'}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Peso Neto:</span>
                <span className="font-bold text-green-600">
                  {formatNumber(createdPesaje.peso_neto || 0)} kg ({formatNumber((createdPesaje.peso_neto || 0) / 1000, 2)} t)
                </span>
              </div>
              {/* Solo mostrar importe a administradores */}
              {isAdmin && createdPesaje.importe_total && createdPesaje.importe_total > 0 && (
                <>
                  <div className="border-t pt-2 mt-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-500">Importe Total:</span>
                      <span className="font-bold text-green-600">
                        ${formatNumber(createdPesaje.importe_total, 2)}
                      </span>
                    </div>
                  </div>
                  <div className="text-xs text-blue-600 mt-1">
                    Ingreso registrado en Finanzas
                  </div>
                </>
              )}
            </div>

            <div className="flex flex-col gap-3">
              <Button onClick={handleDownloadPDF} className="w-full bg-green-600 hover:bg-green-700">
                <Printer className="h-4 w-4 mr-2" />
                Imprimir Ticket PDF
              </Button>
              <Button
                variant="outline"
                onClick={() => navigate('/pesajes-remitos')}
                className="w-full"
              >
                Volver a Pesajes y Remitos
              </Button>
              <Button
                variant="ghost"
                onClick={() => {
                  setCreatedPesaje(null)
                  setTransportistaBusqueda('')
                  setClienteBusqueda('')
                  reset({
                    tipo_entrega: 'propio',
                    fecha: getTodayLocalDate(),
                    peso_bruto: 0,
                    peso_tara: 0,
                    camion_id: '',
                    acoplado: '',
                    chofer: '',
                    material: '',
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
        <Button variant="outline" onClick={() => navigate('/pesajes-remitos')}>
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
                {/* Sección: Tipo de Entrega */}
                <div>
                  <h3 className="text-sm font-semibold text-gray-700 mb-3 pb-2 border-b">
                    Tipo de Entrega
                  </h3>
                  <div className="flex gap-4">
                    <Controller
                      name="tipo_entrega"
                      control={control}
                      render={({ field }) => (
                        <>
                          <Button
                            type="button"
                            variant={field.value === 'propio' ? 'default' : 'outline'}
                            onClick={() => field.onChange('propio')}
                            className="flex-1"
                          >
                            <Truck className="mr-2 h-4 w-4" />
                            Camión Propio
                          </Button>
                          <Button
                            type="button"
                            variant={field.value === 'transportista' ? 'default' : 'outline'}
                            onClick={() => field.onChange('transportista')}
                            className="flex-1"
                          >
                            <Building2 className="mr-2 h-4 w-4" />
                            Transportista Externo
                          </Button>
                        </>
                      )}
                    />
                  </div>
                </div>

                {/* Sección: Datos del Camión/Transportista */}
                <div>
                  <h3 className="text-sm font-semibold text-gray-700 mb-3 pb-2 border-b">
                    {tipoEntrega === 'propio' ? 'Datos del Camión' : 'Datos del Transportista'}
                  </h3>

                  {tipoEntrega === 'propio' ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {/* Camión propio */}
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
                        <label htmlFor="acoplado" className="text-sm font-medium">
                          Acoplado
                        </label>
                        <Input
                          id="acoplado"
                          {...register('acoplado')}
                          placeholder="Patente acoplado"
                        />
                      </div>
                    </div>
                  ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {/* Transportista con autocompletado */}
                      <div className="space-y-2 relative">
                        <label className="text-sm font-medium">
                          Transportista
                        </label>
                        <div className="relative">
                          <Input
                            value={transportistaBusqueda}
                            onChange={(e) => {
                              setTransportistaBusqueda(e.target.value)
                              setValue('transportista', e.target.value)
                              setValue('transportista_id', '')
                            }}
                            onFocus={() => transportistaSugerencias.length > 0 && setShowTransportistaSugerencias(true)}
                            onBlur={() => setTimeout(() => setShowTransportistaSugerencias(false), 200)}
                            placeholder="Buscar o escribir transportista..."
                          />
                          {showTransportistaSugerencias && transportistaSugerencias.length > 0 && (
                            <div className="absolute z-10 w-full mt-1 bg-white border rounded-md shadow-lg max-h-48 overflow-y-auto">
                              {transportistaSugerencias.map((empresa) => (
                                <button
                                  key={empresa.id}
                                  type="button"
                                  className="w-full px-3 py-2 text-left hover:bg-gray-100 text-sm"
                                  onMouseDown={() => seleccionarTransportista(empresa)}
                                >
                                  {empresa.nombre}
                                </button>
                              ))}
                            </div>
                          )}
                        </div>
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          className="text-xs"
                          onClick={() => {
                            setNuevaEmpresaTipo('transportista')
                            setNuevaEmpresaNombre(transportistaBusqueda)
                            setShowNuevaEmpresaModal(true)
                          }}
                        >
                          <Plus className="h-3 w-3 mr-1" />
                          Agregar nuevo transportista
                        </Button>
                      </div>

                      {/* Patente externa */}
                      <div className="space-y-2">
                        <label htmlFor="patente_externa" className="text-sm font-medium">
                          Patente del Camión <span className="text-red-500">*</span>
                        </label>
                        <Input
                          id="patente_externa"
                          {...register('patente_externa')}
                          placeholder="ABC123"
                        />
                        {errors.patente_externa && (
                          <p className="text-sm text-red-600">{errors.patente_externa.message}</p>
                        )}
                      </div>

                      {/* Acoplado */}
                      <div className="space-y-2">
                        <label htmlFor="acoplado" className="text-sm font-medium">
                          Acoplado
                        </label>
                        <Input
                          id="acoplado"
                          {...register('acoplado')}
                          placeholder="Patente acoplado"
                        />
                      </div>
                    </div>
                  )}
                </div>

                {/* Sección: Cliente Destino */}
                <div>
                  <h3 className="text-sm font-semibold text-gray-700 mb-3 pb-2 border-b">
                    Cliente Destino
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* Cliente con autocompletado */}
                    <div className="space-y-2 relative">
                      <label className="text-sm font-medium">Cliente</label>
                      <div className="relative">
                        <Input
                          value={clienteBusqueda}
                          onChange={(e) => {
                            setClienteBusqueda(e.target.value)
                            setValue('cliente_nombre', e.target.value)
                            setValue('cliente_id', '')
                          }}
                          onFocus={() => clienteSugerencias.length > 0 && setShowClienteSugerencias(true)}
                          onBlur={() => setTimeout(() => setShowClienteSugerencias(false), 200)}
                          placeholder="Buscar o escribir cliente..."
                        />
                        {showClienteSugerencias && clienteSugerencias.length > 0 && (
                          <div className="absolute z-10 w-full mt-1 bg-white border rounded-md shadow-lg max-h-48 overflow-y-auto">
                            {clienteSugerencias.map((empresa) => (
                              <button
                                key={empresa.id}
                                type="button"
                                className="w-full px-3 py-2 text-left hover:bg-gray-100 text-sm"
                                onMouseDown={() => seleccionarCliente(empresa)}
                              >
                                {empresa.nombre}
                              </button>
                            ))}
                          </div>
                        )}
                      </div>
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        className="text-xs"
                        onClick={() => {
                          setNuevaEmpresaTipo('cliente')
                          setNuevaEmpresaNombre(clienteBusqueda)
                          setShowNuevaEmpresaModal(true)
                        }}
                      >
                        <Plus className="h-3 w-3 mr-1" />
                        Agregar nuevo cliente
                      </Button>
                    </div>

                    {/* Chofer */}
                    <div className="space-y-2">
                      <label htmlFor="chofer" className="text-sm font-medium">
                        Chofer
                      </label>
                      <Input
                        id="chofer"
                        {...register('chofer')}
                        placeholder="Nombre del chofer"
                      />
                    </div>
                  </div>
                </div>

                {/* Sección: Fecha y Material */}
                <div>
                  <h3 className="text-sm font-semibold text-gray-700 mb-3 pb-2 border-b">
                    Fecha y Material
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* Fecha */}
                    <div className="space-y-2">
                      <label htmlFor="fecha" className="text-sm font-medium">
                        Fecha <span className="text-red-500">*</span>
                      </label>
                      <Input id="fecha" type="date" {...register('fecha')} />
                      {errors.fecha && (
                        <p className="text-sm text-red-600">{errors.fecha.message}</p>
                      )}
                    </div>

                    {/* Material */}
                    <div className="space-y-2">
                      <label htmlFor="material" className="text-sm font-medium">
                        Material
                      </label>
                      <select
                        id="material"
                        {...register('material')}
                        className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                      >
                        <option value="">Seleccionar material</option>
                        {MATERIALES_DISPONIBLES.map((mat) => (
                          <option key={mat} value={mat}>
                            {mat}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>
                </div>

                {/* Sección: Orden de Entrega (opcional) */}
                {ordenesPendientes.length > 0 && (
                  <div>
                    <h3 className="text-sm font-semibold text-gray-700 mb-3 pb-2 border-b flex items-center gap-2">
                      <ClipboardList className="h-4 w-4" />
                      Orden de Entrega (Opcional)
                    </h3>
                    <p className="text-xs text-gray-500 mb-3">
                      Si este pesaje corresponde a una orden de entrega pendiente, selecciónela aquí para descontar automáticamente.
                    </p>
                    <div className="space-y-2">
                      <select
                        {...register('orden_entrega_id')}
                        className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                      >
                        <option value="">Sin orden de entrega</option>
                        {ordenesPendientes.map((orden) => (
                          <option key={orden.id} value={orden.id}>
                            #{orden.numero_orden} - {orden.cliente_nombre_completo || orden.cliente_nombre || 'Sin cliente'} - {orden.material} ({orden.cargas_entregadas}/{orden.cantidad_cargas} cargas)
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>
                )}

                {/* Sección: Pesos */}
                <div>
                  <h3 className="text-sm font-semibold text-gray-700 mb-3 pb-2 border-b flex items-center gap-2">
                    <Scale className="h-4 w-4" />
                    Pesos
                  </h3>

                  {/* Error de balanza */}
                  {balanzaError && (
                    <div className="bg-red-50 border border-red-200 rounded-md p-3 text-sm text-red-700 mb-4">
                      {balanzaError}
                    </div>
                  )}

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* Peso Bruto */}
                    <div className="space-y-2">
                      <label htmlFor="peso_bruto" className="text-sm font-medium">
                        Peso Bruto (kg) <span className="text-red-500">*</span>
                      </label>
                      <div className="flex gap-2">
                        <Input
                          id="peso_bruto"
                          type="number"
                          step="1"
                          {...register('peso_bruto', { valueAsNumber: true })}
                          placeholder="53540"
                          className="flex-1"
                        />
                        <Button
                          type="button"
                          variant="outline"
                          onClick={() => leerBalanza('bruto')}
                          disabled={leyendoBalanza !== null}
                          title="Leer peso de la balanza"
                        >
                          {leyendoBalanza === 'bruto' ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                          ) : (
                            <Scale className="h-4 w-4" />
                          )}
                        </Button>
                      </div>
                      {errors.peso_bruto && (
                        <p className="text-sm text-red-600">{errors.peso_bruto.message}</p>
                      )}
                    </div>

                    {/* Peso Tara */}
                    <div className="space-y-2">
                      <label htmlFor="peso_tara" className="text-sm font-medium">
                        Peso Tara (kg) <span className="text-red-500">*</span>
                      </label>
                      <div className="flex gap-2">
                        <Input
                          id="peso_tara"
                          type="number"
                          step="1"
                          {...register('peso_tara', { valueAsNumber: true })}
                          placeholder="16920"
                          className="flex-1"
                        />
                        <Button
                          type="button"
                          variant="outline"
                          onClick={() => leerBalanza('tara')}
                          disabled={leyendoBalanza !== null}
                          title="Leer peso de la balanza"
                        >
                          {leyendoBalanza === 'tara' ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                          ) : (
                            <Scale className="h-4 w-4" />
                          )}
                        </Button>
                      </div>
                      {errors.peso_tara && (
                        <p className="text-sm text-red-600">{errors.peso_tara.message}</p>
                      )}
                    </div>
                  </div>

                  <p className="text-xs text-gray-500 mt-2">
                    Use el botón de balanza para capturar el peso automáticamente (requiere servidor de balanza activo)
                  </p>
                </div>

                {/* Sección: Operación */}
                <div>
                  <h3 className="text-sm font-semibold text-gray-700 mb-3 pb-2 border-b">
                    Operación
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* Operario */}
                    <div className="space-y-2">
                      <label htmlFor="operario" className="text-sm font-medium">
                        Operario
                      </label>
                      <Input
                        id="operario"
                        {...register('operario')}
                        placeholder="Nombre del operario"
                      />
                    </div>
                  </div>
                </div>

                {/* Sección: Importe - Solo visible para administradores */}
                {isAdmin && (
                  <div>
                    <h3 className="text-sm font-semibold text-gray-700 mb-3 pb-2 border-b flex items-center gap-2">
                      <DollarSign className="h-4 w-4" />
                      Importe (Opcional)
                    </h3>
                    <p className="text-xs text-gray-500 mb-3">
                      Tres opciones de cobro: Precio/tn, Precio/tn + Flete, o Precio fijo por viaje.
                    </p>
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                      {/* Precio por tonelada */}
                      <div className="space-y-2">
                        <label htmlFor="precio_unitario" className="text-sm font-medium">
                          Precio por Tonelada ($)
                        </label>
                        <Input
                          id="precio_unitario"
                          type="number"
                          step="0.01"
                          {...register('precio_unitario', { valueAsNumber: true })}
                          placeholder="7500"
                          disabled={Number(precioFijoVal) > 0}
                          className={Number(precioFijoVal) > 0 ? 'bg-gray-100' : ''}
                        />
                        <p className="text-xs text-gray-500">Ej: 24tn × $7500</p>
                      </div>

                      {/* Flete */}
                      <div className="space-y-2">
                        <label htmlFor="flete" className="text-sm font-medium">
                          Flete ($)
                        </label>
                        <Input
                          id="flete"
                          type="number"
                          step="0.01"
                          {...register('flete', { valueAsNumber: true })}
                          placeholder="150"
                          disabled={Number(precioFijoVal) > 0}
                          className={Number(precioFijoVal) > 0 ? 'bg-gray-100' : ''}
                        />
                        <p className="text-xs text-gray-500">Suma al total</p>
                      </div>

                      {/* Precio fijo */}
                      <div className="space-y-2">
                        <label htmlFor="precio_fijo" className="text-sm font-medium">
                          Precio Fijo ($)
                        </label>
                        <Input
                          id="precio_fijo"
                          type="number"
                          step="0.01"
                          {...register('precio_fijo', { valueAsNumber: true })}
                          placeholder="420"
                          disabled={Number(precioUnitario) > 0}
                          className={Number(precioUnitario) > 0 ? 'bg-gray-100' : ''}
                        />
                        <p className="text-xs text-gray-500">Ignora $/tn</p>
                      </div>

                      {/* Importe total */}
                      <div className="space-y-2">
                        <label htmlFor="importe_total" className="text-sm font-medium">
                          Importe Total ($)
                        </label>
                        <Input
                          id="importe_total"
                          type="number"
                          step="0.01"
                          {...register('importe_total', { valueAsNumber: true })}
                          placeholder="Calculado"
                          className="bg-gray-50 font-semibold"
                        />
                        {importeCalculado > 0 && (
                          <p className="text-xs text-green-600 font-medium">
                            ${formatNumber(importeCalculado, 2)}
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                )}

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
                    onClick={() => navigate('/pesajes-remitos')}
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

              {/* Sección de importe calculado - Solo visible para administradores */}
              {isAdmin && importeCalculado > 0 && (
                <div className="border-t pt-4 mt-4">
                  <div className="flex items-center gap-2 mb-3">
                    <DollarSign className="h-4 w-4 text-green-600" />
                    <span className="font-semibold text-sm">Importe</span>
                  </div>
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Precio/Tonelada:</span>
                      <span className="font-medium">${formatNumber(precioUnitario || 0, 2)}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Toneladas:</span>
                      <span className="font-medium">{formatNumber(pesoNeto / 1000, 2)} t</span>
                    </div>
                    <div className="flex justify-between pt-2 border-t">
                      <span className="font-semibold">Total:</span>
                      <span className="text-xl font-bold text-green-600">
                        ${formatNumber(importeCalculado, 2)}
                      </span>
                    </div>
                  </div>
                  <div className="bg-blue-50 border border-blue-200 rounded-md p-3 text-xs text-blue-700 mt-3">
                    Este importe se registrará automáticamente como ingreso en Finanzas
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Modal para crear nueva empresa */}
      {showNuevaEmpresaModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <Card className="w-full max-w-md">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                {nuevaEmpresaTipo === 'cliente' ? (
                  <UserCheck className="h-5 w-5" />
                ) : (
                  <Truck className="h-5 w-5" />
                )}
                Agregar {nuevaEmpresaTipo === 'cliente' ? 'Cliente' : 'Transportista'}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="text-sm font-medium mb-2 block">Nombre *</label>
                <Input
                  value={nuevaEmpresaNombre}
                  onChange={(e) => setNuevaEmpresaNombre(e.target.value)}
                  placeholder={`Nombre del ${nuevaEmpresaTipo}`}
                />
              </div>
              <div className="flex gap-2 justify-end">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => {
                    setShowNuevaEmpresaModal(false)
                    setNuevaEmpresaNombre('')
                  }}
                >
                  Cancelar
                </Button>
                <Button
                  onClick={handleCrearNuevaEmpresa}
                  disabled={createEmpresaMutation.isPending}
                >
                  {createEmpresaMutation.isPending ? 'Guardando...' : 'Guardar'}
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}
