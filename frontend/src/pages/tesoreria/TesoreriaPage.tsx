/**
 * Página principal del módulo de Tesorería
 */
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Wallet,
  CreditCard,
  Building2,
  Receipt,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  Plus,
  Search,
  Check,
  X,
  ArrowRightLeft,
  RefreshCw,
  PiggyBank,
  Banknote
} from 'lucide-react'
import { format } from 'date-fns'

import tesoreriaService from '@/services/tesoreriaService'
import { empresasService } from '@/services/empresasService'
import type {
  ChequeCreate, ChequeList,
  MovimientoTesoreriaCreate,
  CajaEfectivo, CajaEfectivoCreate,
  CuentaBancariaTesoreria, CuentaBancariaCreate,
  GastoCreate, GastoList,
  ResumenTesoreria
} from '@/types/tesoreria'
import {
  TIPOS_CHEQUE, ORIGENES_CHEQUE, ESTADOS_CHEQUE, METODOS_PAGO,
  BANCOS_ARGENTINA, CATEGORIAS_GASTO,
  getEstadoChequeColor, getEstadoChequeLabel, formatMonto, getChequeVencimientoStatus
} from '@/types/tesoreria'
import type { Empresa } from '@/types'

// ==================== COMPONENTES AUXILIARES ====================

function StatCard({
  title,
  value,
  subtitle,
  icon: Icon,
  color = 'blue',
  trend
}: {
  title: string
  value: string | number
  subtitle?: string
  icon: React.ComponentType<{ className?: string }>
  color?: 'blue' | 'green' | 'red' | 'yellow' | 'purple'
  trend?: 'up' | 'down'
}) {
  const colorClasses = {
    blue: 'bg-blue-50 text-blue-600',
    green: 'bg-green-50 text-green-600',
    red: 'bg-red-50 text-red-600',
    yellow: 'bg-yellow-50 text-yellow-600',
    purple: 'bg-purple-50 text-purple-600',
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4 shadow-sm">
      <div className="flex items-center justify-between">
        <div className={`p-2 rounded-lg ${colorClasses[color]}`}>
          <Icon className="w-5 h-5" />
        </div>
        {trend && (
          <span className={trend === 'up' ? 'text-green-500' : 'text-red-500'}>
            {trend === 'up' ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
          </span>
        )}
      </div>
      <div className="mt-3">
        <p className="text-2xl font-semibold text-gray-900">
          {typeof value === 'number' ? formatMonto(value) : value}
        </p>
        <p className="text-sm text-gray-500 mt-1">{title}</p>
        {subtitle && <p className="text-xs text-gray-400">{subtitle}</p>}
      </div>
    </div>
  )
}

function Badge({ children, color = 'gray' }: { children: React.ReactNode; color?: string }) {
  const colorClasses: Record<string, string> = {
    blue: 'bg-blue-100 text-blue-800',
    green: 'bg-green-100 text-green-800',
    red: 'bg-red-100 text-red-800',
    yellow: 'bg-yellow-100 text-yellow-800',
    purple: 'bg-purple-100 text-purple-800',
    gray: 'bg-gray-100 text-gray-800',
  }

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${colorClasses[color] || colorClasses.gray}`}>
      {children}
    </span>
  )
}

// ==================== COMPONENTE PRINCIPAL ====================

export default function TesoreriaPage() {
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState<'resumen' | 'cheques' | 'movimientos' | 'cajas' | 'bancos' | 'gastos'>('resumen')

  // Estados para filtros
  const [chequeFiltroEstado, setChequeFiltroEstado] = useState<string>('')
  const [chequeBuscar, setChequeBuscar] = useState('')
  const [movimientoFiltroTipo, setMovimientoFiltroTipo] = useState<string>('')
  const [gastoFiltroCategoria, setGastoFiltroCategoria] = useState<string>('')

  // Estados para modales
  const [showChequeModal, setShowChequeModal] = useState(false)
  const [showMovimientoModal, setShowMovimientoModal] = useState(false)
  const [showCajaModal, setShowCajaModal] = useState(false)
  const [showCuentaModal, setShowCuentaModal] = useState(false)
  const [showGastoModal, setShowGastoModal] = useState(false)
  const [showAccionChequeModal, setShowAccionChequeModal] = useState(false)
  const [accionCheque, setAccionCheque] = useState<'depositar' | 'cobrar' | 'rechazar' | 'entregar' | null>(null)
  const [chequeSeleccionado, setChequeSeleccionado] = useState<ChequeList | null>(null)

  // Formularios
  const [chequeForm, setChequeForm] = useState<ChequeCreate>({
    numero: '',
    tipo: 'fisico',
    origen: 'recibido_cliente',
    monto: 0,
    fecha_vencimiento: format(new Date(), 'yyyy-MM-dd'),
  })

  const [movimientoForm, setMovimientoForm] = useState<MovimientoTesoreriaCreate>({
    tipo: 'ingreso_efectivo',
    concepto: '',
    monto: 0,
    es_ingreso: true,
    fecha_movimiento: format(new Date(), 'yyyy-MM-dd'),
    metodo_pago: 'efectivo',
  })

  const [cajaForm, setCajaForm] = useState<CajaEfectivoCreate>({
    nombre: '',
    saldo_inicial: 0,
  })

  const [cuentaForm, setCuentaForm] = useState<CuentaBancariaCreate>({
    nombre: '',
    banco: '',
    saldo_inicial: 0,
  })

  const [gastoForm, setGastoForm] = useState<GastoCreate>({
    fecha: format(new Date(), 'yyyy-MM-dd'),
    concepto: '',
    monto: 0,
    metodo_pago: 'efectivo',
  })

  const [accionForm, setAccionForm] = useState({
    cuenta_destino_id: '',
    fecha: format(new Date(), 'yyyy-MM-dd'),
    motivo_rechazo: '',
    concepto: '',
    notas: '',
  })

  // ==================== QUERIES ====================

  const { data: resumen, isLoading: loadingResumen } = useQuery({
    queryKey: ['tesoreria-resumen'],
    queryFn: () => tesoreriaService.resumen.getResumen(),
  })

  const { data: chequesData, isLoading: loadingCheques } = useQuery({
    queryKey: ['tesoreria-cheques', chequeFiltroEstado, chequeBuscar],
    queryFn: () => tesoreriaService.cheques.getCheques({
      estado: chequeFiltroEstado || undefined,
      buscar: chequeBuscar || undefined,
      limit: 50,
    }),
  })

  const { data: movimientosData, isLoading: loadingMovimientos } = useQuery({
    queryKey: ['tesoreria-movimientos', movimientoFiltroTipo],
    queryFn: () => tesoreriaService.movimientos.getMovimientos({
      tipo: movimientoFiltroTipo || undefined,
      limit: 50,
    }),
  })

  const { data: cajas } = useQuery({
    queryKey: ['tesoreria-cajas'],
    queryFn: () => tesoreriaService.cajas.getCajas(),
  })

  const { data: cuentasBancarias } = useQuery({
    queryKey: ['tesoreria-cuentas'],
    queryFn: () => tesoreriaService.cuentasBancarias.getCuentas(),
  })

  const { data: gastosData, isLoading: loadingGastos } = useQuery({
    queryKey: ['tesoreria-gastos', gastoFiltroCategoria],
    queryFn: () => tesoreriaService.gastos.getGastos({
      categoria: gastoFiltroCategoria || undefined,
      limit: 50,
    }),
  })

  const { data: empresas } = useQuery({
    queryKey: ['empresas'],
    queryFn: () => empresasService.getAll('cliente'),
  })

  // ==================== MUTATIONS ====================

  const crearChequeMutation = useMutation({
    mutationFn: tesoreriaService.cheques.crearCheque,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tesoreria-cheques'] })
      queryClient.invalidateQueries({ queryKey: ['tesoreria-resumen'] })
      setShowChequeModal(false)
      resetChequeForm()
    },
  })

  const depositarChequeMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) =>
      tesoreriaService.cheques.depositarCheque(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tesoreria-cheques'] })
      queryClient.invalidateQueries({ queryKey: ['tesoreria-resumen'] })
      setShowAccionChequeModal(false)
      resetAccionForm()
    },
  })

  const cobrarChequeMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) =>
      tesoreriaService.cheques.cobrarCheque(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tesoreria-cheques'] })
      queryClient.invalidateQueries({ queryKey: ['tesoreria-resumen'] })
      setShowAccionChequeModal(false)
      resetAccionForm()
    },
  })

  const rechazarChequeMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) =>
      tesoreriaService.cheques.rechazarCheque(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tesoreria-cheques'] })
      queryClient.invalidateQueries({ queryKey: ['tesoreria-resumen'] })
      setShowAccionChequeModal(false)
      resetAccionForm()
    },
  })

  const entregarChequeMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) =>
      tesoreriaService.cheques.entregarCheque(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tesoreria-cheques'] })
      queryClient.invalidateQueries({ queryKey: ['tesoreria-resumen'] })
      setShowAccionChequeModal(false)
      resetAccionForm()
    },
  })

  const crearMovimientoMutation = useMutation({
    mutationFn: tesoreriaService.movimientos.crearMovimiento,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tesoreria-movimientos'] })
      queryClient.invalidateQueries({ queryKey: ['tesoreria-resumen'] })
      setShowMovimientoModal(false)
      resetMovimientoForm()
    },
  })

  const crearCajaMutation = useMutation({
    mutationFn: tesoreriaService.cajas.crearCaja,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tesoreria-cajas'] })
      queryClient.invalidateQueries({ queryKey: ['tesoreria-resumen'] })
      setShowCajaModal(false)
      resetCajaForm()
    },
  })

  const crearCuentaMutation = useMutation({
    mutationFn: tesoreriaService.cuentasBancarias.crearCuenta,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tesoreria-cuentas'] })
      queryClient.invalidateQueries({ queryKey: ['tesoreria-resumen'] })
      setShowCuentaModal(false)
      resetCuentaForm()
    },
  })

  const crearGastoMutation = useMutation({
    mutationFn: tesoreriaService.gastos.crearGasto,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tesoreria-gastos'] })
      queryClient.invalidateQueries({ queryKey: ['tesoreria-resumen'] })
      setShowGastoModal(false)
      resetGastoForm()
    },
  })

  // ==================== HELPERS ====================

  function resetChequeForm() {
    setChequeForm({
      numero: '',
      tipo: 'fisico',
      origen: 'recibido_cliente',
      monto: 0,
      fecha_vencimiento: format(new Date(), 'yyyy-MM-dd'),
    })
  }

  function resetMovimientoForm() {
    setMovimientoForm({
      tipo: 'ingreso_efectivo',
      concepto: '',
      monto: 0,
      es_ingreso: true,
      fecha_movimiento: format(new Date(), 'yyyy-MM-dd'),
      metodo_pago: 'efectivo',
    })
  }

  function resetCajaForm() {
    setCajaForm({ nombre: '', saldo_inicial: 0 })
  }

  function resetCuentaForm() {
    setCuentaForm({ nombre: '', banco: '', saldo_inicial: 0 })
  }

  function resetGastoForm() {
    setGastoForm({
      fecha: format(new Date(), 'yyyy-MM-dd'),
      concepto: '',
      monto: 0,
      metodo_pago: 'efectivo',
    })
  }

  function resetAccionForm() {
    setAccionForm({
      cuenta_destino_id: '',
      fecha: format(new Date(), 'yyyy-MM-dd'),
      motivo_rechazo: '',
      concepto: '',
      notas: '',
    })
    setChequeSeleccionado(null)
    setAccionCheque(null)
  }

  function handleAccionCheque(cheque: ChequeList, accion: 'depositar' | 'cobrar' | 'rechazar' | 'entregar') {
    setChequeSeleccionado(cheque)
    setAccionCheque(accion)
    setShowAccionChequeModal(true)
  }

  function submitAccionCheque() {
    if (!chequeSeleccionado || !accionCheque) return

    switch (accionCheque) {
      case 'depositar':
        depositarChequeMutation.mutate({
          id: chequeSeleccionado.id,
          data: {
            cuenta_destino_id: accionForm.cuenta_destino_id,
            fecha_deposito: accionForm.fecha,
            notas: accionForm.notas,
          }
        })
        break
      case 'cobrar':
        cobrarChequeMutation.mutate({
          id: chequeSeleccionado.id,
          data: {
            fecha_cobro: accionForm.fecha,
            notas: accionForm.notas,
          }
        })
        break
      case 'rechazar':
        rechazarChequeMutation.mutate({
          id: chequeSeleccionado.id,
          data: {
            motivo_rechazo: accionForm.motivo_rechazo,
            fecha_rechazo: accionForm.fecha,
          }
        })
        break
      case 'entregar':
        entregarChequeMutation.mutate({
          id: chequeSeleccionado.id,
          data: {
            concepto: accionForm.concepto,
            fecha_entrega: accionForm.fecha,
            notas: accionForm.notas,
          }
        })
        break
    }
  }

  // ==================== TABS ====================

  const tabs = [
    { id: 'resumen', label: 'Resumen', icon: Wallet },
    { id: 'cheques', label: 'Cheques', icon: CreditCard },
    { id: 'movimientos', label: 'Movimientos', icon: ArrowRightLeft },
    { id: 'cajas', label: 'Cajas', icon: PiggyBank },
    { id: 'bancos', label: 'Bancos', icon: Building2 },
    { id: 'gastos', label: 'Gastos', icon: Receipt },
  ] as const

  // ==================== RENDER ====================

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Tesorería</h1>
          <p className="text-gray-500">Gestión de cheques, efectivo, bancos y gastos</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => queryClient.invalidateQueries({ queryKey: ['tesoreria'] })}
            className="p-2 text-gray-600 hover:bg-gray-100 rounded-lg"
            title="Actualizar"
          >
            <RefreshCw className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex space-x-8">
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`
                flex items-center gap-2 py-4 px-1 border-b-2 font-medium text-sm transition-colors
                ${activeTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }
              `}
            >
              <tab.icon className="w-4 h-4" />
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'resumen' && (
        <TabResumen resumen={resumen} isLoading={loadingResumen} />
      )}

      {activeTab === 'cheques' && (
        <TabCheques
          cheques={chequesData?.items || []}
          isLoading={loadingCheques}
          filtroEstado={chequeFiltroEstado}
          setFiltroEstado={setChequeFiltroEstado}
          buscar={chequeBuscar}
          setBuscar={setChequeBuscar}
          onNuevo={() => setShowChequeModal(true)}
          onAccion={handleAccionCheque}
        />
      )}

      {activeTab === 'movimientos' && (
        <TabMovimientos
          movimientos={movimientosData?.items || []}
          isLoading={loadingMovimientos}
          filtroTipo={movimientoFiltroTipo}
          setFiltroTipo={setMovimientoFiltroTipo}
          onNuevo={() => setShowMovimientoModal(true)}
        />
      )}

      {activeTab === 'cajas' && (
        <TabCajas
          cajas={cajas || []}
          onNuevo={() => setShowCajaModal(true)}
        />
      )}

      {activeTab === 'bancos' && (
        <TabBancos
          cuentas={cuentasBancarias || []}
          onNuevo={() => setShowCuentaModal(true)}
        />
      )}

      {activeTab === 'gastos' && (
        <TabGastos
          gastos={gastosData?.items || []}
          isLoading={loadingGastos}
          filtroCategoria={gastoFiltroCategoria}
          setFiltroCategoria={setGastoFiltroCategoria}
          onNuevo={() => setShowGastoModal(true)}
        />
      )}

      {/* Modal Nuevo Cheque */}
      {showChequeModal && (
        <Modal title="Registrar Cheque" onClose={() => setShowChequeModal(false)}>
          <form
            onSubmit={(e) => {
              e.preventDefault()
              crearChequeMutation.mutate(chequeForm)
            }}
            className="space-y-4"
          >
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Número</label>
                <input
                  type="text"
                  value={chequeForm.numero}
                  onChange={(e) => setChequeForm({ ...chequeForm, numero: e.target.value })}
                  className="w-full border rounded-lg px-3 py-2"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Monto</label>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  value={chequeForm.monto}
                  onChange={(e) => setChequeForm({ ...chequeForm, monto: parseFloat(e.target.value) || 0 })}
                  className="w-full border rounded-lg px-3 py-2"
                  required
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Tipo</label>
                <select
                  value={chequeForm.tipo}
                  onChange={(e) => setChequeForm({ ...chequeForm, tipo: e.target.value as any })}
                  className="w-full border rounded-lg px-3 py-2"
                >
                  {TIPOS_CHEQUE.map(t => (
                    <option key={t.value} value={t.value}>{t.label}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Origen</label>
                <select
                  value={chequeForm.origen}
                  onChange={(e) => setChequeForm({ ...chequeForm, origen: e.target.value as any })}
                  className="w-full border rounded-lg px-3 py-2"
                >
                  {ORIGENES_CHEQUE.map(o => (
                    <option key={o.value} value={o.value}>{o.label}</option>
                  ))}
                </select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Fecha Vencimiento</label>
                <input
                  type="date"
                  value={chequeForm.fecha_vencimiento}
                  onChange={(e) => setChequeForm({ ...chequeForm, fecha_vencimiento: e.target.value })}
                  className="w-full border rounded-lg px-3 py-2"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Banco Origen</label>
                <select
                  value={chequeForm.banco_origen || ''}
                  onChange={(e) => setChequeForm({ ...chequeForm, banco_origen: e.target.value })}
                  className="w-full border rounded-lg px-3 py-2"
                >
                  <option value="">Seleccionar...</option>
                  {BANCOS_ARGENTINA.map(b => (
                    <option key={b.value} value={b.label}>{b.label}</option>
                  ))}
                </select>
              </div>
            </div>

            {chequeForm.origen === 'recibido_cliente' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Cliente</label>
                <select
                  value={chequeForm.empresa_id || ''}
                  onChange={(e) => setChequeForm({ ...chequeForm, empresa_id: e.target.value })}
                  className="w-full border rounded-lg px-3 py-2"
                  required
                >
                  <option value="">Seleccionar cliente...</option>
                  {(empresas as Empresa[] | undefined)?.map(emp => (
                    <option key={emp.id} value={emp.id}>{emp.nombre}</option>
                  ))}
                </select>
              </div>
            )}

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Librador</label>
                <input
                  type="text"
                  value={chequeForm.librador || ''}
                  onChange={(e) => setChequeForm({ ...chequeForm, librador: e.target.value })}
                  className="w-full border rounded-lg px-3 py-2"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">CUIT Librador</label>
                <input
                  type="text"
                  value={chequeForm.cuit_librador || ''}
                  onChange={(e) => setChequeForm({ ...chequeForm, cuit_librador: e.target.value })}
                  className="w-full border rounded-lg px-3 py-2"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Notas</label>
              <textarea
                value={chequeForm.notas || ''}
                onChange={(e) => setChequeForm({ ...chequeForm, notas: e.target.value })}
                className="w-full border rounded-lg px-3 py-2"
                rows={2}
              />
            </div>

            <div className="flex justify-end gap-3 pt-4">
              <button
                type="button"
                onClick={() => setShowChequeModal(false)}
                className="px-4 py-2 border rounded-lg hover:bg-gray-50"
              >
                Cancelar
              </button>
              <button
                type="submit"
                disabled={crearChequeMutation.isPending}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                {crearChequeMutation.isPending ? 'Guardando...' : 'Guardar'}
              </button>
            </div>
          </form>
        </Modal>
      )}

      {/* Modal Acción Cheque */}
      {showAccionChequeModal && chequeSeleccionado && accionCheque && (
        <Modal
          title={
            accionCheque === 'depositar' ? 'Depositar Cheque' :
            accionCheque === 'cobrar' ? 'Confirmar Cobro' :
            accionCheque === 'rechazar' ? 'Rechazar Cheque' :
            'Entregar Cheque'
          }
          onClose={() => setShowAccionChequeModal(false)}
        >
          <div className="mb-4 p-4 bg-gray-50 rounded-lg">
            <p className="text-sm text-gray-600">Cheque #{chequeSeleccionado.numero}</p>
            <p className="text-lg font-semibold">{formatMonto(chequeSeleccionado.monto)}</p>
            {chequeSeleccionado.empresa_nombre && (
              <p className="text-sm text-gray-500">{chequeSeleccionado.empresa_nombre}</p>
            )}
          </div>

          <form
            onSubmit={(e) => {
              e.preventDefault()
              submitAccionCheque()
            }}
            className="space-y-4"
          >
            {accionCheque === 'depositar' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Cuenta Destino</label>
                <select
                  value={accionForm.cuenta_destino_id}
                  onChange={(e) => setAccionForm({ ...accionForm, cuenta_destino_id: e.target.value })}
                  className="w-full border rounded-lg px-3 py-2"
                  required
                >
                  <option value="">Seleccionar cuenta...</option>
                  {cuentasBancarias?.map(cuenta => (
                    <option key={cuenta.id} value={cuenta.id}>
                      {cuenta.banco} - {cuenta.nombre}
                    </option>
                  ))}
                </select>
              </div>
            )}

            {accionCheque === 'rechazar' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Motivo de Rechazo</label>
                <textarea
                  value={accionForm.motivo_rechazo}
                  onChange={(e) => setAccionForm({ ...accionForm, motivo_rechazo: e.target.value })}
                  className="w-full border rounded-lg px-3 py-2"
                  rows={3}
                  required
                />
              </div>
            )}

            {accionCheque === 'entregar' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Concepto de Entrega</label>
                <input
                  type="text"
                  value={accionForm.concepto}
                  onChange={(e) => setAccionForm({ ...accionForm, concepto: e.target.value })}
                  className="w-full border rounded-lg px-3 py-2"
                  placeholder="Ej: Pago a proveedor XYZ"
                  required
                />
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Fecha</label>
              <input
                type="date"
                value={accionForm.fecha}
                onChange={(e) => setAccionForm({ ...accionForm, fecha: e.target.value })}
                className="w-full border rounded-lg px-3 py-2"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Notas (opcional)</label>
              <textarea
                value={accionForm.notas}
                onChange={(e) => setAccionForm({ ...accionForm, notas: e.target.value })}
                className="w-full border rounded-lg px-3 py-2"
                rows={2}
              />
            </div>

            <div className="flex justify-end gap-3 pt-4">
              <button
                type="button"
                onClick={() => setShowAccionChequeModal(false)}
                className="px-4 py-2 border rounded-lg hover:bg-gray-50"
              >
                Cancelar
              </button>
              <button
                type="submit"
                disabled={
                  depositarChequeMutation.isPending ||
                  cobrarChequeMutation.isPending ||
                  rechazarChequeMutation.isPending ||
                  entregarChequeMutation.isPending
                }
                className={`px-4 py-2 text-white rounded-lg disabled:opacity-50 ${
                  accionCheque === 'rechazar' ? 'bg-red-600 hover:bg-red-700' : 'bg-blue-600 hover:bg-blue-700'
                }`}
              >
                Confirmar
              </button>
            </div>
          </form>
        </Modal>
      )}

      {/* Modal Nuevo Movimiento */}
      {showMovimientoModal && (
        <Modal title="Registrar Movimiento" onClose={() => setShowMovimientoModal(false)}>
          <form
            onSubmit={(e) => {
              e.preventDefault()
              crearMovimientoMutation.mutate(movimientoForm)
            }}
            className="space-y-4"
          >
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Tipo</label>
                <select
                  value={movimientoForm.es_ingreso ? 'ingreso' : 'egreso'}
                  onChange={(e) => {
                    const esIngreso = e.target.value === 'ingreso'
                    setMovimientoForm({
                      ...movimientoForm,
                      es_ingreso: esIngreso,
                      tipo: `${e.target.value}_${movimientoForm.metodo_pago}`
                    })
                  }}
                  className="w-full border rounded-lg px-3 py-2"
                >
                  <option value="ingreso">Ingreso</option>
                  <option value="egreso">Egreso</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Método de Pago</label>
                <select
                  value={movimientoForm.metodo_pago}
                  onChange={(e) => {
                    const metodo = e.target.value
                    setMovimientoForm({
                      ...movimientoForm,
                      metodo_pago: metodo as any,
                      tipo: `${movimientoForm.es_ingreso ? 'ingreso' : 'egreso'}_${metodo}`
                    })
                  }}
                  className="w-full border rounded-lg px-3 py-2"
                >
                  {METODOS_PAGO.map(m => (
                    <option key={m.value} value={m.value}>{m.label}</option>
                  ))}
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Concepto</label>
              <input
                type="text"
                value={movimientoForm.concepto}
                onChange={(e) => setMovimientoForm({ ...movimientoForm, concepto: e.target.value })}
                className="w-full border rounded-lg px-3 py-2"
                required
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Monto</label>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  value={movimientoForm.monto}
                  onChange={(e) => setMovimientoForm({ ...movimientoForm, monto: parseFloat(e.target.value) || 0 })}
                  className="w-full border rounded-lg px-3 py-2"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Fecha</label>
                <input
                  type="date"
                  value={movimientoForm.fecha_movimiento}
                  onChange={(e) => setMovimientoForm({ ...movimientoForm, fecha_movimiento: e.target.value })}
                  className="w-full border rounded-lg px-3 py-2"
                  required
                />
              </div>
            </div>

            {movimientoForm.metodo_pago === 'transferencia' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Cuenta</label>
                <select
                  value={movimientoForm.cuenta_destino_id || ''}
                  onChange={(e) => setMovimientoForm({ ...movimientoForm, cuenta_destino_id: e.target.value })}
                  className="w-full border rounded-lg px-3 py-2"
                >
                  <option value="">Seleccionar cuenta...</option>
                  {cuentasBancarias?.map(cuenta => (
                    <option key={cuenta.id} value={cuenta.id}>
                      {cuenta.banco} - {cuenta.nombre}
                    </option>
                  ))}
                </select>
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Descripción (opcional)</label>
              <textarea
                value={movimientoForm.descripcion || ''}
                onChange={(e) => setMovimientoForm({ ...movimientoForm, descripcion: e.target.value })}
                className="w-full border rounded-lg px-3 py-2"
                rows={2}
              />
            </div>

            <div className="flex justify-end gap-3 pt-4">
              <button
                type="button"
                onClick={() => setShowMovimientoModal(false)}
                className="px-4 py-2 border rounded-lg hover:bg-gray-50"
              >
                Cancelar
              </button>
              <button
                type="submit"
                disabled={crearMovimientoMutation.isPending}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                {crearMovimientoMutation.isPending ? 'Guardando...' : 'Guardar'}
              </button>
            </div>
          </form>
        </Modal>
      )}

      {/* Modal Nueva Caja */}
      {showCajaModal && (
        <Modal title="Nueva Caja de Efectivo" onClose={() => setShowCajaModal(false)}>
          <form
            onSubmit={(e) => {
              e.preventDefault()
              crearCajaMutation.mutate(cajaForm)
            }}
            className="space-y-4"
          >
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Nombre</label>
              <input
                type="text"
                value={cajaForm.nombre}
                onChange={(e) => setCajaForm({ ...cajaForm, nombre: e.target.value })}
                className="w-full border rounded-lg px-3 py-2"
                placeholder="Ej: Caja Principal"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Saldo Inicial</label>
              <input
                type="number"
                step="0.01"
                min="0"
                value={cajaForm.saldo_inicial || 0}
                onChange={(e) => setCajaForm({ ...cajaForm, saldo_inicial: parseFloat(e.target.value) || 0 })}
                className="w-full border rounded-lg px-3 py-2"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Descripción (opcional)</label>
              <textarea
                value={cajaForm.descripcion || ''}
                onChange={(e) => setCajaForm({ ...cajaForm, descripcion: e.target.value })}
                className="w-full border rounded-lg px-3 py-2"
                rows={2}
              />
            </div>

            <div className="flex justify-end gap-3 pt-4">
              <button
                type="button"
                onClick={() => setShowCajaModal(false)}
                className="px-4 py-2 border rounded-lg hover:bg-gray-50"
              >
                Cancelar
              </button>
              <button
                type="submit"
                disabled={crearCajaMutation.isPending}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                {crearCajaMutation.isPending ? 'Guardando...' : 'Guardar'}
              </button>
            </div>
          </form>
        </Modal>
      )}

      {/* Modal Nueva Cuenta Bancaria */}
      {showCuentaModal && (
        <Modal title="Nueva Cuenta Bancaria" onClose={() => setShowCuentaModal(false)}>
          <form
            onSubmit={(e) => {
              e.preventDefault()
              crearCuentaMutation.mutate(cuentaForm)
            }}
            className="space-y-4"
          >
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Nombre</label>
                <input
                  type="text"
                  value={cuentaForm.nombre}
                  onChange={(e) => setCuentaForm({ ...cuentaForm, nombre: e.target.value })}
                  className="w-full border rounded-lg px-3 py-2"
                  placeholder="Ej: Cuenta Principal"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Banco</label>
                <select
                  value={cuentaForm.banco}
                  onChange={(e) => setCuentaForm({ ...cuentaForm, banco: e.target.value })}
                  className="w-full border rounded-lg px-3 py-2"
                  required
                >
                  <option value="">Seleccionar...</option>
                  {BANCOS_ARGENTINA.map(b => (
                    <option key={b.value} value={b.label}>{b.label}</option>
                  ))}
                </select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Tipo de Cuenta</label>
                <select
                  value={cuentaForm.tipo_cuenta || ''}
                  onChange={(e) => setCuentaForm({ ...cuentaForm, tipo_cuenta: e.target.value })}
                  className="w-full border rounded-lg px-3 py-2"
                >
                  <option value="">Seleccionar...</option>
                  <option value="cuenta_corriente">Cuenta Corriente</option>
                  <option value="caja_ahorro">Caja de Ahorro</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Número de Cuenta</label>
                <input
                  type="text"
                  value={cuentaForm.numero_cuenta || ''}
                  onChange={(e) => setCuentaForm({ ...cuentaForm, numero_cuenta: e.target.value })}
                  className="w-full border rounded-lg px-3 py-2"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">CBU</label>
                <input
                  type="text"
                  value={cuentaForm.cbu || ''}
                  onChange={(e) => setCuentaForm({ ...cuentaForm, cbu: e.target.value })}
                  className="w-full border rounded-lg px-3 py-2"
                  maxLength={22}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Alias</label>
                <input
                  type="text"
                  value={cuentaForm.alias || ''}
                  onChange={(e) => setCuentaForm({ ...cuentaForm, alias: e.target.value })}
                  className="w-full border rounded-lg px-3 py-2"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Saldo Inicial</label>
              <input
                type="number"
                step="0.01"
                value={cuentaForm.saldo_inicial || 0}
                onChange={(e) => setCuentaForm({ ...cuentaForm, saldo_inicial: parseFloat(e.target.value) || 0 })}
                className="w-full border rounded-lg px-3 py-2"
              />
            </div>

            <div className="flex justify-end gap-3 pt-4">
              <button
                type="button"
                onClick={() => setShowCuentaModal(false)}
                className="px-4 py-2 border rounded-lg hover:bg-gray-50"
              >
                Cancelar
              </button>
              <button
                type="submit"
                disabled={crearCuentaMutation.isPending}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                {crearCuentaMutation.isPending ? 'Guardando...' : 'Guardar'}
              </button>
            </div>
          </form>
        </Modal>
      )}

      {/* Modal Nuevo Gasto */}
      {showGastoModal && (
        <Modal title="Registrar Gasto" onClose={() => setShowGastoModal(false)}>
          <form
            onSubmit={(e) => {
              e.preventDefault()
              crearGastoMutation.mutate(gastoForm)
            }}
            className="space-y-4"
          >
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Fecha</label>
                <input
                  type="date"
                  value={gastoForm.fecha}
                  onChange={(e) => setGastoForm({ ...gastoForm, fecha: e.target.value })}
                  className="w-full border rounded-lg px-3 py-2"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Categoría</label>
                <select
                  value={gastoForm.categoria || ''}
                  onChange={(e) => setGastoForm({ ...gastoForm, categoria: e.target.value as any })}
                  className="w-full border rounded-lg px-3 py-2"
                >
                  <option value="">Seleccionar...</option>
                  {CATEGORIAS_GASTO.map(c => (
                    <option key={c.value} value={c.value}>{c.label}</option>
                  ))}
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Concepto</label>
              <input
                type="text"
                value={gastoForm.concepto}
                onChange={(e) => setGastoForm({ ...gastoForm, concepto: e.target.value })}
                className="w-full border rounded-lg px-3 py-2"
                required
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Monto</label>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  value={gastoForm.monto}
                  onChange={(e) => setGastoForm({ ...gastoForm, monto: parseFloat(e.target.value) || 0 })}
                  className="w-full border rounded-lg px-3 py-2"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Método de Pago</label>
                <select
                  value={gastoForm.metodo_pago}
                  onChange={(e) => setGastoForm({ ...gastoForm, metodo_pago: e.target.value as any })}
                  className="w-full border rounded-lg px-3 py-2"
                >
                  {METODOS_PAGO.map(m => (
                    <option key={m.value} value={m.value}>{m.label}</option>
                  ))}
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Proveedor (opcional)</label>
              <input
                type="text"
                value={gastoForm.proveedor_nombre || ''}
                onChange={(e) => setGastoForm({ ...gastoForm, proveedor_nombre: e.target.value })}
                className="w-full border rounded-lg px-3 py-2"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Descripción (opcional)</label>
              <textarea
                value={gastoForm.descripcion || ''}
                onChange={(e) => setGastoForm({ ...gastoForm, descripcion: e.target.value })}
                className="w-full border rounded-lg px-3 py-2"
                rows={2}
              />
            </div>

            <div className="flex justify-end gap-3 pt-4">
              <button
                type="button"
                onClick={() => setShowGastoModal(false)}
                className="px-4 py-2 border rounded-lg hover:bg-gray-50"
              >
                Cancelar
              </button>
              <button
                type="submit"
                disabled={crearGastoMutation.isPending}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                {crearGastoMutation.isPending ? 'Guardando...' : 'Guardar'}
              </button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  )
}

// ==================== COMPONENTES DE TABS ====================

function TabResumen({ resumen, isLoading }: { resumen?: ResumenTesoreria; isLoading: boolean }) {
  if (isLoading) {
    return <div className="text-center py-8">Cargando resumen...</div>
  }

  if (!resumen) {
    return <div className="text-center py-8 text-gray-500">No hay datos disponibles</div>
  }

  return (
    <div className="space-y-6">
      {/* Alertas */}
      {(resumen.cheques_vencidos > 0 || resumen.cheques_proximos_vencer > 0) && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <div className="flex items-center gap-2 text-yellow-800">
            <AlertTriangle className="w-5 h-5" />
            <span className="font-medium">Atención</span>
          </div>
          <div className="mt-2 space-y-1 text-sm text-yellow-700">
            {resumen.cheques_vencidos > 0 && (
              <p>{resumen.cheques_vencidos} cheque(s) vencido(s) por {formatMonto(resumen.total_vencidos)}</p>
            )}
            {resumen.cheques_proximos_vencer > 0 && (
              <p>{resumen.cheques_proximos_vencer} cheque(s) próximo(s) a vencer por {formatMonto(resumen.total_proximos_vencer)}</p>
            )}
          </div>
        </div>
      )}

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Disponible"
          value={resumen.total_disponible}
          icon={Wallet}
          color="blue"
        />
        <StatCard
          title="Cheques en Cartera"
          value={resumen.total_cheques_cartera}
          subtitle={`${resumen.cheques_en_cartera} cheques`}
          icon={CreditCard}
          color="purple"
        />
        <StatCard
          title="Saldo en Cajas"
          value={resumen.saldo_cajas}
          icon={Banknote}
          color="green"
        />
        <StatCard
          title="Saldo en Bancos"
          value={resumen.saldo_bancos}
          icon={Building2}
          color="blue"
        />
      </div>

      {/* Ingresos y Egresos del período */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-green-600" />
            Ingresos del Período
          </h3>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-gray-600">Efectivo</span>
              <span className="font-medium">{formatMonto(resumen.total_ingresos_efectivo)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Transferencias</span>
              <span className="font-medium">{formatMonto(resumen.total_ingresos_transferencia)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Cheques</span>
              <span className="font-medium">{formatMonto(resumen.total_ingresos_cheque)}</span>
            </div>
            <div className="border-t pt-3 flex justify-between">
              <span className="font-semibold">Total</span>
              <span className="font-semibold text-green-600">{formatMonto(resumen.total_ingresos)}</span>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <TrendingDown className="w-5 h-5 text-red-600" />
            Egresos del Período
          </h3>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-gray-600">Efectivo</span>
              <span className="font-medium">{formatMonto(resumen.total_egresos_efectivo)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Transferencias</span>
              <span className="font-medium">{formatMonto(resumen.total_egresos_transferencia)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Cheques</span>
              <span className="font-medium">{formatMonto(resumen.total_egresos_cheque)}</span>
            </div>
            <div className="border-t pt-3 flex justify-between">
              <span className="font-semibold">Total</span>
              <span className="font-semibold text-red-600">{formatMonto(resumen.total_egresos)}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Saldo del período */}
      <div className="bg-white rounded-lg border p-6">
        <div className="flex items-center justify-between">
          <span className="text-lg font-semibold text-gray-900">Saldo del Período</span>
          <span className={`text-2xl font-bold ${resumen.saldo_periodo >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            {formatMonto(resumen.saldo_periodo)}
          </span>
        </div>
      </div>
    </div>
  )
}

function TabCheques({
  cheques,
  isLoading,
  filtroEstado,
  setFiltroEstado,
  buscar,
  setBuscar,
  onNuevo,
  onAccion
}: {
  cheques: ChequeList[]
  isLoading: boolean
  filtroEstado: string
  setFiltroEstado: (v: string) => void
  buscar: string
  setBuscar: (v: string) => void
  onNuevo: () => void
  onAccion: (cheque: ChequeList, accion: 'depositar' | 'cobrar' | 'rechazar' | 'entregar') => void
}) {
  return (
    <div className="space-y-4">
      {/* Toolbar */}
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-4 flex-1">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Buscar cheque..."
              value={buscar}
              onChange={(e) => setBuscar(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border rounded-lg"
            />
          </div>
          <select
            value={filtroEstado}
            onChange={(e) => setFiltroEstado(e.target.value)}
            className="border rounded-lg px-3 py-2"
          >
            <option value="">Todos los estados</option>
            {ESTADOS_CHEQUE.map(e => (
              <option key={e.value} value={e.value}>{e.label}</option>
            ))}
          </select>
        </div>
        <button
          onClick={onNuevo}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          <Plus className="w-4 h-4" />
          Nuevo Cheque
        </button>
      </div>

      {/* Tabla */}
      <div className="bg-white rounded-lg border overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50 border-b">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Número</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Tipo</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Cliente</th>
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Monto</th>
              <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Vencimiento</th>
              <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Estado</th>
              <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Acciones</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {isLoading ? (
              <tr>
                <td colSpan={7} className="px-4 py-8 text-center text-gray-500">
                  Cargando...
                </td>
              </tr>
            ) : cheques.length === 0 ? (
              <tr>
                <td colSpan={7} className="px-4 py-8 text-center text-gray-500">
                  No hay cheques registrados
                </td>
              </tr>
            ) : (
              cheques.map(cheque => {
                const vencStatus = getChequeVencimientoStatus(cheque.dias_para_vencimiento)
                return (
                  <tr key={cheque.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3">
                      <span className="font-mono font-medium">{cheque.numero}</span>
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-sm text-gray-600">
                        {TIPOS_CHEQUE.find(t => t.value === cheque.tipo)?.label || cheque.tipo}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <div>
                        <p className="text-sm font-medium">{cheque.empresa_nombre || '-'}</p>
                        {cheque.librador && (
                          <p className="text-xs text-gray-500">{cheque.librador}</p>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <span className="font-semibold">{formatMonto(cheque.monto)}</span>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <div>
                        <p className="text-sm">{format(new Date(cheque.fecha_vencimiento), 'dd/MM/yyyy')}</p>
                        <Badge color={vencStatus.color}>{vencStatus.label}</Badge>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <Badge color={getEstadoChequeColor(cheque.estado)}>
                        {getEstadoChequeLabel(cheque.estado)}
                      </Badge>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center justify-center gap-1">
                        {cheque.estado === 'en_cartera' && (
                          <>
                            <button
                              onClick={() => onAccion(cheque, 'depositar')}
                              className="p-1.5 text-blue-600 hover:bg-blue-50 rounded"
                              title="Depositar"
                            >
                              <Building2 className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => onAccion(cheque, 'cobrar')}
                              className="p-1.5 text-green-600 hover:bg-green-50 rounded"
                              title="Cobrar"
                            >
                              <Check className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => onAccion(cheque, 'entregar')}
                              className="p-1.5 text-purple-600 hover:bg-purple-50 rounded"
                              title="Entregar"
                            >
                              <ArrowRightLeft className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => onAccion(cheque, 'rechazar')}
                              className="p-1.5 text-red-600 hover:bg-red-50 rounded"
                              title="Rechazar"
                            >
                              <X className="w-4 h-4" />
                            </button>
                          </>
                        )}
                        {cheque.estado === 'depositado' && (
                          <>
                            <button
                              onClick={() => onAccion(cheque, 'cobrar')}
                              className="p-1.5 text-green-600 hover:bg-green-50 rounded"
                              title="Confirmar Cobro"
                            >
                              <Check className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => onAccion(cheque, 'rechazar')}
                              className="p-1.5 text-red-600 hover:bg-red-50 rounded"
                              title="Rechazar"
                            >
                              <X className="w-4 h-4" />
                            </button>
                          </>
                        )}
                      </div>
                    </td>
                  </tr>
                )
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function TabMovimientos({
  movimientos,
  isLoading,
  filtroTipo,
  setFiltroTipo,
  onNuevo
}: {
  movimientos: any[]
  isLoading: boolean
  filtroTipo: string
  setFiltroTipo: (v: string) => void
  onNuevo: () => void
}) {
  return (
    <div className="space-y-4">
      {/* Toolbar */}
      <div className="flex items-center justify-between gap-4">
        <select
          value={filtroTipo}
          onChange={(e) => setFiltroTipo(e.target.value)}
          className="border rounded-lg px-3 py-2"
        >
          <option value="">Todos los tipos</option>
          <option value="ingreso_efectivo">Ingreso Efectivo</option>
          <option value="ingreso_transferencia">Ingreso Transferencia</option>
          <option value="egreso_efectivo">Egreso Efectivo</option>
          <option value="egreso_transferencia">Egreso Transferencia</option>
        </select>
        <button
          onClick={onNuevo}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          <Plus className="w-4 h-4" />
          Nuevo Movimiento
        </button>
      </div>

      {/* Tabla */}
      <div className="bg-white rounded-lg border overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50 border-b">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Fecha</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Concepto</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Tipo</th>
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Monto</th>
              <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Estado</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {isLoading ? (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-gray-500">
                  Cargando...
                </td>
              </tr>
            ) : movimientos.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-gray-500">
                  No hay movimientos registrados
                </td>
              </tr>
            ) : (
              movimientos.map(mov => (
                <tr key={mov.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-sm">
                    {format(new Date(mov.fecha_movimiento), 'dd/MM/yyyy')}
                  </td>
                  <td className="px-4 py-3">
                    <p className="font-medium">{mov.concepto}</p>
                    {mov.empresa_nombre && (
                      <p className="text-xs text-gray-500">{mov.empresa_nombre}</p>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <Badge color={mov.es_ingreso ? 'green' : 'red'}>
                      {mov.es_ingreso ? 'Ingreso' : 'Egreso'}
                    </Badge>
                    <span className="ml-2 text-xs text-gray-500 capitalize">
                      {mov.metodo_pago}
                    </span>
                  </td>
                  <td className={`px-4 py-3 text-right font-semibold ${mov.es_ingreso ? 'text-green-600' : 'text-red-600'}`}>
                    {mov.es_ingreso ? '+' : '-'}{formatMonto(mov.monto)}
                  </td>
                  <td className="px-4 py-3 text-center">
                    {mov.anulado ? (
                      <Badge color="red">Anulado</Badge>
                    ) : (
                      <Badge color="green">Activo</Badge>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function TabCajas({
  cajas,
  onNuevo
}: {
  cajas: CajaEfectivo[]
  onNuevo: () => void
}) {
  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <button
          onClick={onNuevo}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          <Plus className="w-4 h-4" />
          Nueva Caja
        </button>
      </div>

      {cajas.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          No hay cajas de efectivo registradas
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {cajas.map(caja => (
            <div key={caja.id} className="bg-white rounded-lg border p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-green-50 text-green-600 rounded-lg">
                    <Banknote className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="font-semibold">{caja.nombre}</h3>
                    {caja.es_principal && (
                      <Badge color="blue">Principal</Badge>
                    )}
                  </div>
                </div>
              </div>
              <div className="text-2xl font-bold text-gray-900">
                {formatMonto(caja.saldo_actual)}
              </div>
              {caja.descripcion && (
                <p className="text-sm text-gray-500 mt-2">{caja.descripcion}</p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function TabBancos({
  cuentas,
  onNuevo
}: {
  cuentas: CuentaBancariaTesoreria[]
  onNuevo: () => void
}) {
  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <button
          onClick={onNuevo}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          <Plus className="w-4 h-4" />
          Nueva Cuenta
        </button>
      </div>

      {cuentas.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          No hay cuentas bancarias registradas
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {cuentas.map(cuenta => (
            <div key={cuenta.id} className="bg-white rounded-lg border p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="p-2 bg-blue-50 text-blue-600 rounded-lg">
                  <Building2 className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-semibold">{cuenta.nombre}</h3>
                  <p className="text-sm text-gray-500">{cuenta.banco}</p>
                </div>
              </div>
              <div className="text-2xl font-bold text-gray-900 mb-2">
                {formatMonto(cuenta.saldo_actual)}
              </div>
              <div className="text-sm text-gray-500 space-y-1">
                {cuenta.tipo_cuenta && <p>Tipo: {cuenta.tipo_cuenta}</p>}
                {cuenta.cbu && <p className="font-mono text-xs">CBU: {cuenta.cbu}</p>}
                {cuenta.alias && <p>Alias: {cuenta.alias}</p>}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function TabGastos({
  gastos,
  isLoading,
  filtroCategoria,
  setFiltroCategoria,
  onNuevo
}: {
  gastos: GastoList[]
  isLoading: boolean
  filtroCategoria: string
  setFiltroCategoria: (v: string) => void
  onNuevo: () => void
}) {
  return (
    <div className="space-y-4">
      {/* Toolbar */}
      <div className="flex items-center justify-between gap-4">
        <select
          value={filtroCategoria}
          onChange={(e) => setFiltroCategoria(e.target.value)}
          className="border rounded-lg px-3 py-2"
        >
          <option value="">Todas las categorías</option>
          {CATEGORIAS_GASTO.map(c => (
            <option key={c.value} value={c.value}>{c.label}</option>
          ))}
        </select>
        <button
          onClick={onNuevo}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          <Plus className="w-4 h-4" />
          Nuevo Gasto
        </button>
      </div>

      {/* Tabla */}
      <div className="bg-white rounded-lg border overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50 border-b">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Fecha</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Concepto</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Categoría</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Proveedor</th>
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Monto</th>
              <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Estado</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {isLoading ? (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-gray-500">
                  Cargando...
                </td>
              </tr>
            ) : gastos.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-gray-500">
                  No hay gastos registrados
                </td>
              </tr>
            ) : (
              gastos.map(gasto => (
                <tr key={gasto.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-sm">
                    {format(new Date(gasto.fecha), 'dd/MM/yyyy')}
                  </td>
                  <td className="px-4 py-3 font-medium">{gasto.concepto}</td>
                  <td className="px-4 py-3">
                    <span className="text-sm text-gray-600 capitalize">
                      {CATEGORIAS_GASTO.find(c => c.value === gasto.categoria)?.label || gasto.categoria || '-'}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600">
                    {gasto.empresa_nombre || gasto.proveedor_nombre || '-'}
                  </td>
                  <td className="px-4 py-3 text-right font-semibold text-red-600">
                    -{formatMonto(gasto.monto)}
                  </td>
                  <td className="px-4 py-3 text-center">
                    {gasto.anulado ? (
                      <Badge color="red">Anulado</Badge>
                    ) : (
                      <Badge color="green">Activo</Badge>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}

// ==================== MODAL COMPONENT ====================

function Modal({
  title,
  children,
  onClose
}: {
  title: string
  children: React.ReactNode
  onClose: () => void
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />
      <div className="relative bg-white rounded-lg shadow-xl w-full max-w-lg max-h-[90vh] overflow-auto m-4">
        <div className="flex items-center justify-between p-4 border-b">
          <h2 className="text-lg font-semibold">{title}</h2>
          <button onClick={onClose} className="p-1 hover:bg-gray-100 rounded">
            <X className="w-5 h-5" />
          </button>
        </div>
        <div className="p-4">
          {children}
        </div>
      </div>
    </div>
  )
}
