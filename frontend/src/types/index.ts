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

export interface User {
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
}

export interface UsuarioUpdate {
  email?: string
  nombre?: string
  rol?: 'administrador' | 'operador' | 'solo_lectura'
  activo?: boolean
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  skip: number
  limit: number
}

// ==================== CAMION ====================

export interface Camion {
  id: string
  patente: string
  marca: string
  modelo: string
  año: number
  kilometraje_actual: number
  estado: 'operativo' | 'en_servicio' | 'fuera_servicio'
  observaciones?: string
  activo: boolean
  created_at: string
  updated_at: string
  // Campos de servicio
  ultimo_servicio?: string
  ultimo_servicio_km?: number
  proximo_servicio_km?: number
  proximo_servicio_fecha?: string
  intervalo_servicio_km?: number
  // Campos calculados
  km_para_proximo_servicio?: number
  requiere_servicio?: boolean
}

export interface CamionCreate {
  patente: string
  marca: string
  modelo: string
  año: number
  kilometraje_actual: number
  estado: 'operativo' | 'en_servicio' | 'fuera_servicio'
  observaciones?: string
  proximo_servicio_km?: number
  proximo_servicio_fecha?: string
  intervalo_servicio_km?: number
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

export interface Pesaje {
  id: string
  numero_pesaje: number
  fecha: string
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
  peso_tara: number
  peso_bruto: number
  peso_neto: number
  // Material
  material?: string
  // Operación
  operario?: string
  observaciones?: string
  remito_generado: boolean
  created_by: string
  created_at: string
  updated_at: string
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
  camion_patente: string
  fecha: string
  litros: number
  kilometraje_actual?: number
  observaciones?: string
  created_by: string
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
