import { useEffect, useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useForm, Controller } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  ArrowLeft, Save, Calculator, Printer, CheckCircle, Truck, Building2,
  Plus, UserCheck, DollarSign, ClipboardList, Scale, Loader2, Search,
  Clock, AlertCircle
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { pesajesService, PesajeIniciarCreate, PesajeCompletarCreate, BusquedaPatenteResult } from '@/services/pesajesService'
import { camionesService } from '@/services/camionesService'
import { empresasService } from '@/services/empresasService'
import { ordenEntregaService } from '@/services/ordenEntregaService'
import { balanzaService } from '@/services/balanzaService'
import { formatNumber } from '@/lib/utils'
import { Pesaje, Empresa, EmpresaCreate } from '@/types'

// Lista de materiales disponibles
const MATERIALES_DISPONIBLES = [
  '10.30',
  '6.19',
  '0.20',
  '6.12',
  'relleno',
  'binder',
  '0.6',
]

// Schema para búsqueda por patente
const busquedaSchema = z.object({
  patente: z.string().min(1, 'Ingrese la patente'),
})

// Schema para pesaje inicial (tara)
const pesajeTaraSchema = z.object({
  tipo_entrega: z.enum(['propio', 'transportista']),
  camion_id: z.string().optional(),
  transportista_id: z.string().optional(),
  patente_externa: z.string().optional(),
  transportista: z.string().optional(),
  cliente_id: z.string().optional(),
  cliente_nombre: z.string().optional(),
  acoplado: z.string().optional(),
  chofer: z.string().optional(),
  peso_tara: z.number().min(1, 'El peso tara debe ser mayor a 0'),
  material: z.string().optional(),
  operario: z.string().optional(),
  observaciones: z.string().optional(),
  orden_entrega_id: z.string().optional(),
  fecha: z.string().min(1, 'La fecha es requerida'),
})

// Schema para completar pesaje (bruto)
const pesajeBrutoSchema = z.object({
  peso_bruto: z.number().min(1, 'El peso bruto debe ser mayor a 0'),
  material: z.string().optional(),
  chofer: z.string().optional(),
  observaciones: z.string().optional(),
  precio_unitario: z.number().min(0).optional(),
  importe_total: z.number().min(0).optional(),
  orden_entrega_id: z.string().optional(),
})

type BusquedaFormData = z.infer<typeof busquedaSchema>
type PesajeTaraFormData = z.infer<typeof pesajeTaraSchema>
type PesajeBrutoFormData = z.infer<typeof pesajeBrutoSchema>

type ModoFormulario = 'busqueda' | 'nueva_tara' | 'completar_bruto' | 'exito'

export default function NuevoPesajePage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  // Estado del flujo
  const [modo, setModo] = useState<ModoFormulario>('busqueda')
  const [resultadoBusqueda, setResultadoBusqueda] = useState<BusquedaPatenteResult | null>(null)
  const [pesajePendiente, setPesajePendiente] = useState<Pesaje | null>(null)
  const [createdPesaje, setCreatedPesaje] = useState<Pesaje | null>(null)
  const [buscando, setBuscando] = useState(false)

  // Estados para autocompletado de cliente
  const [clienteBusqueda, setClienteBusqueda] = useState('')
  const [clienteSugerencias, setClienteSugerencias] = useState<Empresa[]>([])
  const [showClienteSugerencias, setShowClienteSugerencias] = useState(false)

  // Modal para crear nueva empresa
  const [showNuevaEmpresaModal, setShowNuevaEmpresaModal] = useState(false)
  const [nuevaEmpresaNombre, setNuevaEmpresaNombre] = useState('')

  // Estado para la balanza
  const [leyendoBalanza, setLeyendoBalanza] = useState<'bruto' | 'tara' | null>(null)
  const [balanzaError, setBalanzaError] = useState<string | null>(null)

  // Queries
  const { data: camiones = [] } = useQuery({
    queryKey: ['camiones'],
    queryFn: () => camionesService.getAll(true),
  })

  const { data: ordenesPendientes = [] } = useQuery({
    queryKey: ['ordenes-pendientes'],
    queryFn: () => ordenEntregaService.getOrdenesPendientes(),
  })

  // Forms
  const busquedaForm = useForm<BusquedaFormData>({
    resolver: zodResolver(busquedaSchema),
    defaultValues: { patente: '' },
  })

  const taraForm = useForm<PesajeTaraFormData>({
    resolver: zodResolver(pesajeTaraSchema),
    defaultValues: {
      tipo_entrega: 'propio',
      fecha: new Date().toISOString().split('T')[0],
      peso_tara: 0,
    },
  })

  const brutoForm = useForm<PesajeBrutoFormData>({
    resolver: zodResolver(pesajeBrutoSchema),
    defaultValues: {
      peso_bruto: 0,
    },
  })

  // Cálculos
  const pesoTara = taraForm.watch('peso_tara') || pesajePendiente?.peso_tara || 0
  const pesoBruto = brutoForm.watch('peso_bruto') || 0
  const precioUnitario = brutoForm.watch('precio_unitario') || 0
  const pesoNeto = pesoBruto > pesoTara ? pesoBruto - pesoTara : 0
  const importeCalculado = precioUnitario > 0 && pesoNeto > 0 ? (pesoNeto / 1000) * precioUnitario : 0

  // Actualizar importe calculado
  useEffect(() => {
    if (importeCalculado > 0) {
      brutoForm.setValue('importe_total', Math.round(importeCalculado * 100) / 100)
    }
  }, [importeCalculado, brutoForm])

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

  useEffect(() => {
    const timer = setTimeout(() => {
      if (clienteBusqueda) {
        buscarClientes(clienteBusqueda)
      }
    }, 300)
    return () => clearTimeout(timer)
  }, [clienteBusqueda, buscarClientes])

  const seleccionarCliente = (empresa: Empresa) => {
    taraForm.setValue('cliente_id', empresa.id)
    taraForm.setValue('cliente_nombre', empresa.nombre)
    setClienteBusqueda(empresa.nombre)
    setShowClienteSugerencias(false)
  }

  // Buscar por patente
  const handleBuscarPatente = async (data: BusquedaFormData) => {
    setBuscando(true)
    try {
      const resultado = await pesajesService.buscarPorPatente(data.patente)
      setResultadoBusqueda(resultado)

      if (resultado.pesaje_pendiente_id) {
        // Hay un pesaje pendiente - modo completar bruto
        setModo('completar_bruto')
        // Cargar datos del pesaje pendiente
        const pesaje = await pesajesService.getById(resultado.pesaje_pendiente_id)
        setPesajePendiente(pesaje)

        // Pre-llenar material si existe
        if (pesaje.material) {
          brutoForm.setValue('material', pesaje.material)
        }
        // Pre-llenar chofer si existe
        if (pesaje.chofer) {
          brutoForm.setValue('chofer', pesaje.chofer)
        }
      } else if (resultado.encontrado && resultado.tipo === 'propio') {
        // Camión propio de la cantera - modo nueva tara
        setModo('nueva_tara')
        taraForm.setValue('tipo_entrega', 'propio')
        taraForm.setValue('camion_id', resultado.camion_id!)

        // Auto-completar chofer habitual del camión propio
        if (resultado.chofer_habitual) {
          taraForm.setValue('chofer', resultado.chofer_habitual)
        }

        // Auto-completar cliente si existe
        if (resultado.cliente_id && resultado.cliente_nombre) {
          taraForm.setValue('cliente_id', resultado.cliente_id)
          taraForm.setValue('cliente_nombre', resultado.cliente_nombre)
          setClienteBusqueda(resultado.cliente_nombre)
        }
      } else if (resultado.encontrado && resultado.tipo === 'cliente') {
        // Camión de un cliente - modo nueva tara como transportista con datos del cliente
        setModo('nueva_tara')
        taraForm.setValue('tipo_entrega', 'transportista')
        taraForm.setValue('patente_externa', resultado.camion_patente!)

        // Auto-completar cliente (esto es lo importante!)
        if (resultado.cliente_id && resultado.cliente_nombre) {
          taraForm.setValue('cliente_id', resultado.cliente_id)
          taraForm.setValue('cliente_nombre', resultado.cliente_nombre)
          setClienteBusqueda(resultado.cliente_nombre)
        }

        // Auto-completar chofer si existe
        if (resultado.chofer_habitual) {
          taraForm.setValue('chofer', resultado.chofer_habitual)
        }

        // Auto-completar acoplado si existe
        if (resultado.acoplado) {
          taraForm.setValue('acoplado', resultado.acoplado)
        }
      } else {
        // Patente no encontrada - modo nueva tara como transportista
        setModo('nueva_tara')
        taraForm.setValue('tipo_entrega', 'transportista')
        taraForm.setValue('patente_externa', data.patente.toUpperCase())
      }
    } catch (error) {
      console.error('Error buscando patente:', error)
      // Asumir patente nueva de transportista
      setModo('nueva_tara')
      taraForm.setValue('tipo_entrega', 'transportista')
      taraForm.setValue('patente_externa', data.patente.toUpperCase())
    } finally {
      setBuscando(false)
    }
  }

  // Crear nueva empresa y asociar patente
  const createEmpresaMutation = useMutation({
    mutationFn: async (data: EmpresaCreate) => {
      // Crear la empresa
      const empresa = await empresasService.create(data)

      // Si hay patente externa, asociarla a este cliente
      const patenteExterna = taraForm.getValues('patente_externa')
      if (patenteExterna) {
        try {
          await empresasService.agregarCamion(empresa.id, {
            patente: patenteExterna.toUpperCase(),
            chofer_habitual: taraForm.getValues('chofer') || undefined,
          })
        } catch (e) {
          console.log('Error agregando camión al cliente:', e)
        }
      }

      return empresa
    },
    onSuccess: (empresa) => {
      queryClient.invalidateQueries({ queryKey: ['empresas'] })
      seleccionarCliente(empresa)
      setShowNuevaEmpresaModal(false)
      setNuevaEmpresaNombre('')
    },
  })

  // Iniciar pesaje (tara)
  const iniciarPesajeMutation = useMutation({
    mutationFn: (data: PesajeIniciarCreate) => pesajesService.iniciarPesaje(data),
    onSuccess: (pesaje) => {
      queryClient.invalidateQueries({ queryKey: ['pesajes'] })
      queryClient.invalidateQueries({ queryKey: ['pesajes-pendientes'] })
      setCreatedPesaje(pesaje)
      setModo('exito')
    },
  })

  // Completar pesaje (bruto)
  const completarPesajeMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: PesajeCompletarCreate }) =>
      pesajesService.completarPesaje(id, data),
    onSuccess: (pesaje) => {
      queryClient.invalidateQueries({ queryKey: ['pesajes'] })
      queryClient.invalidateQueries({ queryKey: ['pesajes-pendientes'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard-resumen'] })
      setCreatedPesaje(pesaje)
      setModo('exito')
    },
  })

  // Submit tara
  const handleSubmitTara = async (data: PesajeTaraFormData) => {
    try {
      const cleanData: PesajeIniciarCreate = {
        ...data,
        fecha: data.fecha,
      }

      // Limpiar campos vacíos
      if (!cleanData.cliente_id) delete cleanData.cliente_id
      if (!cleanData.transportista_id) delete cleanData.transportista_id
      if (!cleanData.camion_id) delete cleanData.camion_id
      if (!cleanData.orden_entrega_id) delete cleanData.orden_entrega_id

      await iniciarPesajeMutation.mutateAsync(cleanData)
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Error al registrar pesaje')
    }
  }

  // Submit bruto
  const handleSubmitBruto = async (data: PesajeBrutoFormData) => {
    if (!pesajePendiente) return

    try {
      const cleanData: PesajeCompletarCreate = { ...data }

      // Limpiar campos vacíos/cero
      if (!cleanData.precio_unitario) delete cleanData.precio_unitario
      if (!cleanData.importe_total) delete cleanData.importe_total
      if (!cleanData.orden_entrega_id) delete cleanData.orden_entrega_id

      await completarPesajeMutation.mutateAsync({
        id: pesajePendiente.id,
        data: cleanData,
      })
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Error al completar pesaje')
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
        setBalanzaError('Balanza no conectada')
        return
      }

      if (resultado.peso <= 0) {
        setBalanzaError('El peso leído es 0')
        return
      }

      if (tipo === 'bruto') {
        brutoForm.setValue('peso_bruto', resultado.peso)
      } else {
        taraForm.setValue('peso_tara', resultado.peso)
      }
    } catch {
      setBalanzaError('Error al conectar con la balanza')
    } finally {
      setLeyendoBalanza(null)
    }
  }

  // Descargar PDF
  const handleDownloadPDF = async () => {
    if (!createdPesaje) return
    try {
      await pesajesService.downloadTicketPDF(createdPesaje.id, createdPesaje.numero_pesaje)
    } catch {
      alert('Error al descargar el ticket PDF')
    }
  }

  // Nuevo pesaje
  const handleNuevoPesaje = () => {
    setModo('busqueda')
    setResultadoBusqueda(null)
    setPesajePendiente(null)
    setCreatedPesaje(null)
    setClienteBusqueda('')
    busquedaForm.reset()
    taraForm.reset({
      tipo_entrega: 'propio',
      fecha: new Date().toISOString().split('T')[0],
      peso_tara: 0,
    })
    brutoForm.reset({ peso_bruto: 0 })
  }

  const isLoading = iniciarPesajeMutation.isPending || completarPesajeMutation.isPending

  // ===================== PANTALLA DE ÉXITO =====================
  if (modo === 'exito' && createdPesaje) {
    const patenteMostrar = createdPesaje.tipo_entrega === 'propio'
      ? createdPesaje.camion_patente
      : createdPesaje.patente_externa
    const esCompletado = createdPesaje.estado === 'completado'

    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <Card className="max-w-md w-full">
          <CardContent className="pt-6 text-center space-y-6">
            <div className={`mx-auto w-16 h-16 rounded-full flex items-center justify-center ${esCompletado ? 'bg-green-100' : 'bg-yellow-100'}`}>
              {esCompletado ? (
                <CheckCircle className="h-10 w-10 text-green-600" />
              ) : (
                <Clock className="h-10 w-10 text-yellow-600" />
              )}
            </div>

            <div>
              <h2 className="text-2xl font-bold text-gray-900">
                {esCompletado ? 'Pesaje Completado' : 'Tara Registrada'}
              </h2>
              <p className="text-gray-500 mt-2">
                Ticket #{createdPesaje.numero_pesaje}
              </p>
            </div>

            <div className="bg-gray-50 rounded-lg p-4 space-y-2 text-left">
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
              {createdPesaje.material && (
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">Material:</span>
                  <span className="font-medium">{createdPesaje.material}</span>
                </div>
              )}
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Peso Tara:</span>
                <span className="font-medium">{formatNumber(createdPesaje.peso_tara || 0)} kg</span>
              </div>
              {esCompletado && (
                <>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500">Peso Bruto:</span>
                    <span className="font-medium">{formatNumber(createdPesaje.peso_bruto || 0)} kg</span>
                  </div>
                  <div className="flex justify-between text-sm border-t pt-2 mt-2">
                    <span className="text-gray-500">Peso Neto:</span>
                    <span className="font-bold text-green-600">
                      {formatNumber(createdPesaje.peso_neto || 0)} kg ({formatNumber((createdPesaje.peso_neto || 0) / 1000, 2)} t)
                    </span>
                  </div>
                  {createdPesaje.importe_total && createdPesaje.importe_total > 0 && (
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-500">Importe Total:</span>
                      <span className="font-bold text-green-600">
                        ${formatNumber(createdPesaje.importe_total, 2)}
                      </span>
                    </div>
                  )}
                </>
              )}
            </div>

            {!esCompletado && (
              <div className="bg-yellow-50 border border-yellow-200 rounded-md p-3 text-sm text-yellow-700">
                El camión debe volver cargado para completar el pesaje
              </div>
            )}

            <div className="flex flex-col gap-3">
              {esCompletado && (
                <Button onClick={handleDownloadPDF} className="w-full bg-green-600 hover:bg-green-700">
                  <Printer className="h-4 w-4 mr-2" />
                  Imprimir Ticket PDF
                </Button>
              )}
              <Button
                variant="outline"
                onClick={() => navigate('/pesajes-remitos')}
                className="w-full"
              >
                Volver a Pesajes
              </Button>
              <Button
                variant="ghost"
                onClick={handleNuevoPesaje}
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

  // ===================== PANTALLA DE BÚSQUEDA =====================
  if (modo === 'busqueda') {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Button variant="outline" onClick={() => navigate('/pesajes-remitos')}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            Volver
          </Button>
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Nuevo Pesaje</h1>
            <p className="text-gray-500 mt-1">Ingrese la patente del camión para comenzar</p>
          </div>
        </div>

        <div className="max-w-xl mx-auto">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Search className="h-5 w-5" />
                Buscar por Patente
              </CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={busquedaForm.handleSubmit(handleBuscarPatente)} className="space-y-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Patente del Camión</label>
                  <Input
                    {...busquedaForm.register('patente')}
                    placeholder="Ej: ABC123"
                    className="text-2xl text-center uppercase font-mono h-16"
                    autoFocus
                  />
                  {busquedaForm.formState.errors.patente && (
                    <p className="text-sm text-red-600">{busquedaForm.formState.errors.patente.message}</p>
                  )}
                </div>

                <Button type="submit" className="w-full h-12" disabled={buscando}>
                  {buscando ? (
                    <Loader2 className="h-5 w-5 animate-spin mr-2" />
                  ) : (
                    <Search className="h-5 w-5 mr-2" />
                  )}
                  {buscando ? 'Buscando...' : 'Buscar'}
                </Button>
              </form>

              <div className="mt-6 pt-6 border-t">
                <p className="text-sm text-gray-500 text-center">
                  Al ingresar la patente, el sistema verificará si el camión tiene un pesaje pendiente
                  (solo tara) o si es un nuevo ingreso.
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    )
  }

  // ===================== FORMULARIO DE TARA =====================
  if (modo === 'nueva_tara') {
    const tipoEntrega = taraForm.watch('tipo_entrega')
    const pesoTaraActual = taraForm.watch('peso_tara') || 0

    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Button variant="outline" onClick={handleNuevoPesaje}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            Nueva Búsqueda
          </Button>
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Registrar Tara</h1>
            <p className="text-gray-500 mt-1">
              Pesaje inicial - Camión vacío
              {resultadoBusqueda?.camion_patente && (
                <span className="ml-2 font-semibold text-blue-600">
                  {resultadoBusqueda.camion_patente}
                </span>
              )}
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <Card>
              <CardHeader>
                <CardTitle>Datos del Pesaje Inicial</CardTitle>
              </CardHeader>
              <CardContent>
                <form onSubmit={taraForm.handleSubmit(handleSubmitTara)} className="space-y-6">
                  {/* Tipo de entrega */}
                  <div>
                    <h3 className="text-sm font-semibold text-gray-700 mb-3 pb-2 border-b">
                      Tipo de Entrega
                    </h3>
                    <div className="flex gap-4">
                      <Controller
                        name="tipo_entrega"
                        control={taraForm.control}
                        render={({ field }) => (
                          <>
                            <Button
                              type="button"
                              variant={field.value === 'propio' ? 'default' : 'outline'}
                              onClick={() => field.onChange('propio')}
                              className="flex-1"
                              disabled={resultadoBusqueda?.tipo === 'propio'}
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
                              Transportista
                            </Button>
                          </>
                        )}
                      />
                    </div>
                  </div>

                  {/* Datos del camión */}
                  <div>
                    <h3 className="text-sm font-semibold text-gray-700 mb-3 pb-2 border-b">
                      {tipoEntrega === 'propio' ? 'Datos del Camión' : 'Datos del Transportista'}
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {tipoEntrega === 'propio' ? (
                        <div className="space-y-2">
                          <label className="text-sm font-medium">Camión *</label>
                          <select
                            {...taraForm.register('camion_id')}
                            className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                          >
                            <option value="">Seleccionar camión</option>
                            {camiones.map((c) => (
                              <option key={c.id} value={c.id}>
                                {c.patente} - {c.marca} {c.modelo}
                              </option>
                            ))}
                          </select>
                        </div>
                      ) : (
                        <>
                          <div className="space-y-2">
                            <label className="text-sm font-medium">Patente *</label>
                            <Input
                              {...taraForm.register('patente_externa')}
                              placeholder="ABC123"
                              className="uppercase"
                            />
                          </div>
                          <div className="space-y-2">
                            <label className="text-sm font-medium">Transportista</label>
                            <Input
                              {...taraForm.register('transportista')}
                              placeholder="Nombre del transportista"
                            />
                          </div>
                        </>
                      )}
                      <div className="space-y-2">
                        <label className="text-sm font-medium">Acoplado</label>
                        <Input
                          {...taraForm.register('acoplado')}
                          placeholder="Patente acoplado"
                        />
                      </div>
                      <div className="space-y-2">
                        <label className="text-sm font-medium">Chofer</label>
                        <Input
                          {...taraForm.register('chofer')}
                          placeholder="Nombre del chofer"
                        />
                      </div>
                    </div>
                  </div>

                  {/* Cliente */}
                  <div>
                    <h3 className="text-sm font-semibold text-gray-700 mb-3 pb-2 border-b">
                      Cliente Destino
                    </h3>
                    <div className="space-y-2 relative">
                      <label className="text-sm font-medium">Cliente</label>
                      <Input
                        value={clienteBusqueda}
                        onChange={(e) => {
                          setClienteBusqueda(e.target.value)
                          taraForm.setValue('cliente_nombre', e.target.value)
                          taraForm.setValue('cliente_id', '')
                        }}
                        onFocus={() => clienteSugerencias.length > 0 && setShowClienteSugerencias(true)}
                        onBlur={() => setTimeout(() => setShowClienteSugerencias(false), 200)}
                        placeholder="Buscar cliente..."
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
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        className="text-xs"
                        onClick={() => {
                          setNuevaEmpresaNombre(clienteBusqueda)
                          setShowNuevaEmpresaModal(true)
                        }}
                      >
                        <Plus className="h-3 w-3 mr-1" />
                        Agregar nuevo cliente
                      </Button>
                    </div>
                  </div>

                  {/* Fecha y Material */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <label className="text-sm font-medium">Fecha *</label>
                      <Input type="date" {...taraForm.register('fecha')} />
                    </div>
                    <div className="space-y-2">
                      <label className="text-sm font-medium">Material</label>
                      <select
                        {...taraForm.register('material')}
                        className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                      >
                        <option value="">Seleccionar material</option>
                        {MATERIALES_DISPONIBLES.map((m) => (
                          <option key={m} value={m}>{m}</option>
                        ))}
                      </select>
                    </div>
                  </div>

                  {/* Peso Tara */}
                  <div>
                    <h3 className="text-sm font-semibold text-gray-700 mb-3 pb-2 border-b flex items-center gap-2">
                      <Scale className="h-4 w-4" />
                      Peso Tara (Camión Vacío)
                    </h3>
                    {balanzaError && (
                      <div className="bg-red-50 border border-red-200 rounded-md p-3 text-sm text-red-700 mb-4">
                        {balanzaError}
                      </div>
                    )}
                    <div className="flex gap-2">
                      <Input
                        type="number"
                        step="1"
                        {...taraForm.register('peso_tara', { valueAsNumber: true })}
                        placeholder="Peso en kg"
                        className="flex-1 text-xl"
                      />
                      <Button
                        type="button"
                        variant="outline"
                        onClick={() => leerBalanza('tara')}
                        disabled={leyendoBalanza !== null}
                        className="px-6"
                      >
                        {leyendoBalanza === 'tara' ? (
                          <Loader2 className="h-5 w-5 animate-spin" />
                        ) : (
                          <Scale className="h-5 w-5" />
                        )}
                      </Button>
                    </div>
                    {taraForm.formState.errors.peso_tara && (
                      <p className="text-sm text-red-600 mt-1">{taraForm.formState.errors.peso_tara.message}</p>
                    )}
                  </div>

                  {/* Observaciones */}
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Observaciones</label>
                    <textarea
                      {...taraForm.register('observaciones')}
                      rows={2}
                      placeholder="Notas adicionales..."
                      className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                    />
                  </div>

                  {/* Botones */}
                  <div className="flex items-center gap-4 pt-4 border-t">
                    <Button type="submit" disabled={isLoading}>
                      <Save className="h-4 w-4 mr-2" />
                      {isLoading ? 'Guardando...' : 'Registrar Tara'}
                    </Button>
                    <Button type="button" variant="outline" onClick={handleNuevoPesaje}>
                      Cancelar
                    </Button>
                  </div>
                </form>
              </CardContent>
            </Card>
          </div>

          {/* Panel lateral */}
          <div>
            <Card className="sticky top-6">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Scale className="h-5 w-5" />
                  Peso Tara
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="text-center">
                  <span className="text-4xl font-bold text-blue-600">
                    {formatNumber(pesoTaraActual)} kg
                  </span>
                </div>
                <div className="bg-blue-50 border border-blue-200 rounded-md p-3 text-sm text-blue-700">
                  Peso del camión vacío. El camión debe volver cargado para completar el pesaje.
                </div>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Modal crear empresa */}
        {showNuevaEmpresaModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <Card className="w-full max-w-md">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <UserCheck className="h-5 w-5" />
                  Agregar Cliente
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <label className="text-sm font-medium mb-2 block">Nombre *</label>
                  <Input
                    value={nuevaEmpresaNombre}
                    onChange={(e) => setNuevaEmpresaNombre(e.target.value)}
                    placeholder="Nombre del cliente"
                  />
                </div>
                <div className="flex gap-2 justify-end">
                  <Button variant="outline" onClick={() => setShowNuevaEmpresaModal(false)}>
                    Cancelar
                  </Button>
                  <Button
                    onClick={() => createEmpresaMutation.mutate({ nombre: nuevaEmpresaNombre, tipo: 'cliente' })}
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

  // ===================== FORMULARIO DE BRUTO (COMPLETAR) =====================
  if (modo === 'completar_bruto' && pesajePendiente) {
    const patenteMostrar = pesajePendiente.tipo_entrega === 'propio'
      ? pesajePendiente.camion_patente
      : pesajePendiente.patente_externa

    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Button variant="outline" onClick={handleNuevoPesaje}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            Nueva Búsqueda
          </Button>
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Completar Pesaje</h1>
            <p className="text-gray-500 mt-1">
              Pesaje final - Camión cargado
              <span className="ml-2 font-semibold text-blue-600">{patenteMostrar}</span>
            </p>
          </div>
        </div>

        {/* Info del pesaje pendiente */}
        <Card className="bg-yellow-50 border-yellow-200">
          <CardContent className="py-4">
            <div className="flex items-center gap-4">
              <Clock className="h-8 w-8 text-yellow-600" />
              <div>
                <p className="font-semibold text-yellow-800">
                  Pesaje #{pesajePendiente.numero_pesaje} - Esperando peso bruto
                </p>
                <p className="text-sm text-yellow-700">
                  Tara registrada: {formatNumber(pesajePendiente.peso_tara || 0)} kg
                  {pesajePendiente.cliente_nombre && ` | Cliente: ${pesajePendiente.cliente_nombre}`}
                  {pesajePendiente.material && ` | Material: ${pesajePendiente.material}`}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <Card>
              <CardHeader>
                <CardTitle>Datos del Pesaje Final</CardTitle>
              </CardHeader>
              <CardContent>
                <form onSubmit={brutoForm.handleSubmit(handleSubmitBruto)} className="space-y-6">
                  {/* Peso Bruto */}
                  <div>
                    <h3 className="text-sm font-semibold text-gray-700 mb-3 pb-2 border-b flex items-center gap-2">
                      <Scale className="h-4 w-4" />
                      Peso Bruto (Camión Cargado)
                    </h3>
                    {balanzaError && (
                      <div className="bg-red-50 border border-red-200 rounded-md p-3 text-sm text-red-700 mb-4">
                        {balanzaError}
                      </div>
                    )}
                    <div className="flex gap-2">
                      <Input
                        type="number"
                        step="1"
                        {...brutoForm.register('peso_bruto', { valueAsNumber: true })}
                        placeholder="Peso en kg"
                        className="flex-1 text-xl"
                        autoFocus
                      />
                      <Button
                        type="button"
                        variant="outline"
                        onClick={() => leerBalanza('bruto')}
                        disabled={leyendoBalanza !== null}
                        className="px-6"
                      >
                        {leyendoBalanza === 'bruto' ? (
                          <Loader2 className="h-5 w-5 animate-spin" />
                        ) : (
                          <Scale className="h-5 w-5" />
                        )}
                      </Button>
                    </div>
                    {brutoForm.formState.errors.peso_bruto && (
                      <p className="text-sm text-red-600 mt-1">{brutoForm.formState.errors.peso_bruto.message}</p>
                    )}
                  </div>

                  {/* Material (si no estaba) */}
                  {!pesajePendiente.material && (
                    <div className="space-y-2">
                      <label className="text-sm font-medium">Material</label>
                      <select
                        {...brutoForm.register('material')}
                        className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                      >
                        <option value="">Seleccionar material</option>
                        {MATERIALES_DISPONIBLES.map((m) => (
                          <option key={m} value={m}>{m}</option>
                        ))}
                      </select>
                    </div>
                  )}

                  {/* Orden de entrega */}
                  {ordenesPendientes.length > 0 && (
                    <div>
                      <h3 className="text-sm font-semibold text-gray-700 mb-3 pb-2 border-b flex items-center gap-2">
                        <ClipboardList className="h-4 w-4" />
                        Orden de Entrega (Opcional)
                      </h3>
                      <select
                        {...brutoForm.register('orden_entrega_id')}
                        className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                      >
                        <option value="">Sin orden de entrega</option>
                        {ordenesPendientes.map((orden) => (
                          <option key={orden.id} value={orden.id}>
                            #{orden.numero_orden} - {orden.cliente_nombre_completo || orden.cliente_nombre} - {orden.material}
                          </option>
                        ))}
                      </select>
                    </div>
                  )}

                  {/* Importe */}
                  <div>
                    <h3 className="text-sm font-semibold text-gray-700 mb-3 pb-2 border-b flex items-center gap-2">
                      <DollarSign className="h-4 w-4" />
                      Importe (Opcional)
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <label className="text-sm font-medium">Precio por Tonelada ($)</label>
                        <Input
                          type="number"
                          step="0.01"
                          {...brutoForm.register('precio_unitario', { valueAsNumber: true })}
                          placeholder="5000"
                        />
                      </div>
                      <div className="space-y-2">
                        <label className="text-sm font-medium">Importe Total ($)</label>
                        <Input
                          type="number"
                          step="0.01"
                          {...brutoForm.register('importe_total', { valueAsNumber: true })}
                          placeholder="Calculado automáticamente"
                          className="bg-gray-50"
                        />
                      </div>
                    </div>
                  </div>

                  {/* Observaciones */}
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Observaciones</label>
                    <textarea
                      {...brutoForm.register('observaciones')}
                      rows={2}
                      placeholder="Notas adicionales..."
                      className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                    />
                  </div>

                  {/* Botones */}
                  <div className="flex items-center gap-4 pt-4 border-t">
                    <Button type="submit" disabled={isLoading} className="bg-green-600 hover:bg-green-700">
                      <CheckCircle className="h-4 w-4 mr-2" />
                      {isLoading ? 'Completando...' : 'Completar Pesaje'}
                    </Button>
                    <Button type="button" variant="outline" onClick={handleNuevoPesaje}>
                      Cancelar
                    </Button>
                  </div>
                </form>
              </CardContent>
            </Card>
          </div>

          {/* Panel de cálculo */}
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
                    <span className="font-medium">{formatNumber(pesoBruto)} kg</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Peso Tara:</span>
                    <span className="font-medium">{formatNumber(pesajePendiente.peso_tara || 0)} kg</span>
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

                {pesoNeto <= 0 && pesoBruto > 0 && (
                  <div className="bg-orange-50 border border-orange-200 rounded-md p-3 text-sm text-orange-700">
                    <AlertCircle className="h-4 w-4 inline mr-1" />
                    El peso bruto debe ser mayor al peso tara
                  </div>
                )}

                {importeCalculado > 0 && (
                  <div className="border-t pt-4 mt-4">
                    <div className="flex items-center gap-2 mb-3">
                      <DollarSign className="h-4 w-4 text-green-600" />
                      <span className="font-semibold text-sm">Importe</span>
                    </div>
                    <div className="flex justify-between pt-2 border-t">
                      <span className="font-semibold">Total:</span>
                      <span className="text-xl font-bold text-green-600">
                        ${formatNumber(importeCalculado, 2)}
                      </span>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    )
  }

  return null
}
