// ==================== AUTH ====================

export interface LoginCredentials {
  email: string
  password: string
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface PermisosModulos {
  permiso_dashboard: boolean
  permiso_camiones: boolean
  permiso_empresas: boolean
  permiso_repuestos: boolean
  permiso_pesajes: boolean
  permiso_combustible: boolean
  permiso_finanzas: boolean
  permiso_usuarios: boolean
  permiso_reportes: boolean
}

export interface User extends PermisosModulos {
  id: string
  email: string
  nombre: string
  rol: 'administrador' | 'operador' | 'solo_lectura'
  activo: boolean
  created_at: string
  updated_at: string
  ultimo_acceso?: string
}

export interface UsuarioCreate {
  email: string
  nombre: string
  rol: 'administrador' | 'operador' | 'solo_lectura'
  password: string
  // Permisos por módulo
  permiso_dashboard?: boolean
  permiso_camiones?: boolean
  permiso_empresas?: boolean
  permiso_repuestos?: boolean
  permiso_pesajes?: boolean
  permiso_combustible?: boolean
  permiso_finanzas?: boolean
  permiso_usuarios?: boolean
  permiso_reportes?: boolean
}

export interface UsuarioUpdate {
  email?: string
  nombre?: string
  rol?: 'administrador' | 'operador' | 'solo_lectura'
  activo?: boolean
  // Permisos por módulo
  permiso_dashboard?: boolean
  permiso_camiones?: boolean
  permiso_empresas?: boolean
  permiso_repuestos?: boolean
  permiso_pesajes?: boolean
  permiso_combustible?: boolean
  permiso_finanzas?: boolean
  permiso_usuarios?: boolean
  permiso_reportes?: boolean
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  skip: number
  limit: number
}

// ==================== CAMION/MÁQUINA ====================

export type CategoriaEquipo = 'camion' | 'maquina'
export type TipoCamion = 'volcador' | 'acoplado' | 'mixer' | 'otro'
export type TipoMaquina = 'pala_cargadora' | 'retroexcavadora' | 'excavadora' | 'motoniveladora' | 'compactadora' | 'trituradora' | 'generador' | 'bomba' | 'otro'
export type EstadoEquipo = 'operativo' | 'en_servicio' | 'fuera_servicio'

export interface Camion {
  id: string
  categoria: CategoriaEquipo
  patente?: string
  nombre?: string
  codigo_interno?: string
  marca?: string
  modelo?: string
  año?: number
  numero_serie?: string
  tipo?: TipoCamion
  tipo_maquina?: string
  estado: EstadoEquipo
  kilometraje_actual: number
  horometro_actual: number
  horas_promedio_diarias?: number
  chofer_habitual?: string
  foto?: string
  observaciones?: string
  activo: boolean
  created_at: string
  updated_at: string
  // Campos de servicio
  ultimo_servicio?: string
  ultimo_servicio_km?: number
  ultimo_servicio_horas?: number
  proximo_servicio_km?: number
  proximo_servicio_horas?: number
  proximo_servicio_fecha?: string
  intervalo_servicio_km?: number
  intervalo_servicio_horas?: number
  // Documentación
  tarjeta_verde_url?: string
  tarjeta_verde_vencimiento?: string
  seguro_url?: string
  seguro_compania?: string
  seguro_poliza?: string
  seguro_vencimiento?: string
  vtv_url?: string
  vtv_vencimiento?: string
  cedula_url?: string
  // Campos calculados
  km_para_proximo_servicio?: number
  horas_para_proximo_servicio?: number
  requiere_servicio?: boolean
  identificador?: string
}

export interface CamionCreate {
  categoria?: CategoriaEquipo
  patente?: string
  nombre?: string
  codigo_interno?: string
  marca?: string
  modelo?: string
  año?: number
  numero_serie?: string
  tipo?: TipoCamion
  tipo_maquina?: string
  estado?: EstadoEquipo
  kilometraje_actual?: number
  horometro_actual?: number
  horas_promedio_diarias?: number
  chofer_habitual?: string
  foto?: string
  observaciones?: string
  proximo_servicio_km?: number
  proximo_servicio_horas?: number
  proximo_servicio_fecha?: string
  intervalo_servicio_km?: number
  intervalo_servicio_horas?: number
  // Documentación
  tarjeta_verde_url?: string
  tarjeta_verde_vencimiento?: string
  seguro_url?: string
  seguro_compania?: string
  seguro_poliza?: string
  seguro_vencimiento?: string
  vtv_url?: string
  vtv_vencimiento?: string
  cedula_url?: string
}

export interface DocumentoEquipo {
  id: string
  equipo_id: string
  tipo: string
  nombre: string
  descripcion?: string
  archivo_url: string
  archivo_nombre?: string
  archivo_tipo?: string
  archivo_tamaño?: number
  fecha_vencimiento?: string
  notas?: string
  created_at: string
  updated_at: string
}

// ==================== REPUESTO ====================

export interface Repuesto {
  id: string
  codigo: string
  nombre: string
  descripcion?: string
  categoria: string
  stock_actual: number
  stock_minimo: number
  precio_unitario: number
  ubicacion?: string
  activo: boolean
  camion_id?: string
  camion_patente?: string
  // Nuevos campos para relación N:N
  asignado_a_equipo?: boolean
  equipos_ids?: string[]
  created_at: string
  updated_at: string
}

export interface RepuestoCreate {
  codigo: string
  nombre: string
  descripcion?: string
  categoria: string
  stock_actual: number
  stock_minimo: number
  precio_unitario: number
  ubicacion?: string
  camion_id?: string
}

export interface MovimientoStock {
  id: string
  repuesto_id?: string
  tipo: 'ingreso' | 'egreso' | 'ajuste'
  cantidad: number
  stock_anterior?: number
  stock_nuevo?: number
  motivo?: string
  observaciones?: string
  referencia_tipo?: string
  usuario_id: string
  usuario_nombre: string
  created_at: string
}

// ==================== SERVICIO ====================

export interface Servicio {
  id: string
  camion_id: string
  camion_patente?: string
  fecha: string
  tipo: 'preventivo' | 'correctivo' | 'emergencia'
  descripcion: string
  kilometraje_servicio?: number
  mecanico?: string
  costo_mano_obra: number
  costo_total: number
  estado: 'programado' | 'en_proceso' | 'completado'
  observaciones?: string
  repuestos_utilizados?: ServicioRepuesto[]
  created_by: string
  created_at: string
  updated_at: string
}

export interface ServicioRepuesto {
  id: string
  repuesto_id: string
  cantidad: number
  precio_unitario?: number
  subtotal?: number
  repuesto_nombre?: string
  repuesto_codigo?: string
}

export interface RepuestoAsignado {
  repuesto_id: string
  cantidad: number
}

export interface ServicioCreate {
  camion_id: string
  fecha: string
  tipo: 'preventivo' | 'correctivo' | 'emergencia'
  descripcion: string
  kilometraje_servicio?: number | null
  mecanico?: string | null
  costo_mano_obra: number
  observaciones?: string
  repuestos: RepuestoAsignado[]
}

// ==================== EMPRESA (CLIENTES/TRANSPORTISTAS) ====================

export type TipoEmpresa = 'cliente' | 'transportista'

export interface Empresa {
  id: string
  nombre: string
  tipo: TipoEmpresa
  cuit?: string
  direccion?: string
  telefono?: string
  email?: string
  contacto?: string
  activo: boolean
  lista_precio_id?: string
  lista_precio_nombre?: string
  created_at: string
  updated_at: string
}

export interface EmpresaCreate {
  nombre: string
  tipo: TipoEmpresa
  cuit?: string
  direccion?: string
  telefono?: string
  email?: string
  contacto?: string
}

// ==================== PESAJE ====================

export type TipoEntrega = 'propio' | 'transportista'

export type EstadoPesaje = 'pendiente' | 'completado' | 'cancelado' | 'expirado'

export interface Pesaje {
  id: string
  numero_pesaje: number
  fecha: string
  estado: EstadoPesaje
  fecha_completado?: string
  tipo_entrega: TipoEntrega
  // Camión propio
  camion_id?: string
  camion_patente?: string
  // Transportista externo
  transportista_id?: string
  transportista_nombre?: string
  patente_externa?: string
  transportista?: string
  // Cliente
  cliente_id?: string
  cliente_nombre?: string
  // Datos del transporte
  acoplado?: string
  chofer?: string
  // Pesos
  peso_tara?: number
  peso_bruto?: number
  peso_neto?: number
  // Material
  material?: string
  // Operación
  operario?: string
  observaciones?: string
  // Importe
  precio_unitario?: number
  flete?: number
  precio_fijo?: number
  importe_total?: number
  movimiento_financiero_id?: string
  remito_generado: boolean
  created_by: string
  created_at: string
  updated_at: string
  // Campos de cancelación
  motivo_cancelacion?: string
  fecha_cancelacion?: string
  cancelado_por?: string
  cancelado_por_nombre?: string
}

export interface PesajeCreate {
  fecha: string
  tipo_entrega: TipoEntrega
  // Camión propio (requerido si tipo_entrega = "propio")
  camion_id?: string
  // Transportista externo (requerido si tipo_entrega = "transportista")
  transportista_id?: string
  patente_externa?: string
  transportista?: string
  // Cliente
  cliente_id?: string
  cliente_nombre?: string
  // Datos del transporte
  acoplado?: string
  chofer?: string
  // Pesos
  peso_tara: number
  peso_bruto: number
  // Material
  material?: string
  // Operación
  operario?: string
  observaciones?: string
  // Importe
  precio_unitario?: number
  flete?: number
  precio_fijo?: number
  importe_total?: number
}

// ==================== REMITO ====================

export interface Remito {
  id: string
  numero_remito: string
  pesaje_id: string
  pesaje_numero?: number
  fecha_emision: string
  camion_patente?: string
  material?: string
  cliente_destino?: string
  peso_neto?: number
  observaciones?: string
  pdf_generado: boolean
  created_by: string
  created_at: string
  updated_at: string
}

// ==================== COMBUSTIBLE ====================

export interface CisternaCombustible {
  id: string
  nombre: string
  capacidad_total: number
  nivel_actual: number
  nivel_minimo: number
  porcentaje_actual?: number
  esta_bajo?: boolean
  created_at: string
  updated_at: string
}

export interface CargaCisterna {
  id: string
  cisterna_id: string
  cisterna_nombre?: string
  fecha: string
  litros: number
  proveedor: string
  numero_remito?: string
  precio_por_litro?: number
  observaciones?: string
  created_by: string
  created_at: string
  updated_at: string
}

export interface SuministroCombustible {
  id: string
  cisterna_id: string
  cisterna_nombre?: string
  camion_id: string
  camion_patente?: string
  camion_nombre?: string
  camion_codigo_interno?: string
  fecha: string
  litros: number
  kilometraje_actual?: number
  horometro?: number
  chofer?: string
  observaciones?: string
  created_by: string
  usuario_nombre?: string
  created_at: string
  updated_at: string
}

export interface TransferenciaCisterna {
  id: string
  cisterna_origen_id: string
  cisterna_destino_id: string
  litros: number
  fecha: string
  observaciones?: string
  created_by: string
  cisterna_origen_nombre?: string
  cisterna_destino_nombre?: string
  usuario_nombre?: string
  created_at: string
  updated_at: string
}

// ==================== DASHBOARD ====================

export interface CamionRequiereServicio {
  id: string
  patente: string
  km_actual: number
  proximo_servicio_km: number
  km_restantes: number
  ultimo_servicio?: string
}

export interface DashboardResumen {
  pesajes: {
    cantidad: number
    toneladas: number
  }
  combustible: {
    nivel_actual: number
    capacidad_total: number
    porcentaje: number
    esta_bajo: boolean
  }
  camiones: {
    operativos: number
    en_servicio: number
    fuera_servicio: number
    total: number
  }
  alertas: {
    repuestos_bajo_stock: number
    servicios_proximos: number
    nivel_combustible_bajo: boolean
    camiones_requieren_servicio: number
  }
  servicios_proximos: ServicioProximo[]
  ultimos_pesajes: UltimoPesaje[]
  camiones_requieren_servicio: CamionRequiereServicio[]
}

export interface ServicioProximo {
  id: string
  camion_patente: string
  fecha: string
  tipo: string
  descripcion: string
}

export interface UltimoPesaje {
  id: string
  numero_pesaje: number
  fecha: string
  camion_patente: string
  material: string
  peso_neto: number
  cliente_destino: string
}

export interface EstadisticasMes {
  total_pesajes_mes: number
  total_toneladas_mes: number
  total_combustible_mes: number
  total_servicios_mes: number
  costo_total_servicios: number
}

// ==================== FINANZAS ====================

export type TipoMovimiento = 'ingreso' | 'egreso'
export type EstadoMovimiento = 'completado' | 'pendiente' | 'anulado'

export interface CategoriaFinanzas {
  id: string
  nombre: string
  tipo: TipoMovimiento
  descripcion?: string
  color?: string
  icono?: string
  activo: boolean
  created_at: string
  updated_at: string
}

export interface CategoriaFinanzasCreate {
  nombre: string
  tipo: TipoMovimiento
  descripcion?: string
  color?: string
  icono?: string
}

export interface MovimientoFinanciero {
  id: string
  tipo: TipoMovimiento
  categoria_id?: string
  fecha: string
  monto: number
  descripcion: string
  detalle?: string
  camion_id?: string
  empresa_id?: string
  numero_comprobante?: string
  tipo_comprobante?: string
  comprobante_url?: string
  metodo_pago?: string
  referencia_pago?: string
  banco?: string
  estado: EstadoMovimiento
  created_by: string
  notas?: string
  created_at: string
  updated_at: string
  // Datos relacionados
  categoria_nombre?: string
  camion_identificador?: string
  empresa_nombre?: string
  creador_nombre?: string
}

export interface MovimientoFinancieroCreate {
  tipo: TipoMovimiento
  categoria_id?: string
  fecha: string
  monto: number
  descripcion: string
  detalle?: string
  camion_id?: string
  empresa_id?: string
  numero_comprobante?: string
  tipo_comprobante?: string
  comprobante_url?: string
  metodo_pago?: string
  referencia_pago?: string
  banco?: string
  estado?: EstadoMovimiento
  notas?: string
}

export interface CuentaBancaria {
  id: string
  nombre: string
  banco: string
  tipo_cuenta?: string
  numero_cuenta?: string
  cbu?: string
  alias?: string
  titular?: string
  cuit_titular?: string
  saldo_inicial: number
  saldo_actual: number
  moneda: string
  activo: boolean
  notas?: string
  created_at: string
  updated_at: string
}

export interface ResumenFinanciero {
  total_ingresos: number
  total_egresos: number
  balance: number
  cantidad_ingresos: number
  cantidad_egresos: number
}

export interface ResumenPorCategoria {
  categoria_id: string
  categoria_nombre: string
  tipo: TipoMovimiento
  total: number
  cantidad: number
  color?: string
}

// ==================== TRABAJO/REPARACIÓN ====================

export interface Trabajo {
  id: string
  camion_id: string
  fecha: string
  descripcion: string
  responsable?: string
  costo_mano_obra: number
  costo_total: number
  observaciones?: string
  created_by: string
  created_at: string
  updated_at: string
  camion_identificador?: string
  usuario_nombre?: string
  repuestos: TrabajoRepuesto[]
}

export interface TrabajoRepuesto {
  id: string
  repuesto_id: string
  nombre: string
  codigo?: string
  cantidad: number
  precio_unitario?: number
  subtotal?: number
}

export interface TrabajoCreate {
  camion_id: string
  fecha: string
  descripcion: string
  responsable?: string
  costo_mano_obra: number
  observaciones?: string
  repuestos: { repuesto_id: string; cantidad: number }[]
}
