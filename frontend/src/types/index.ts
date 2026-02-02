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
}

// ==================== CAMION ====================

export interface Camion {
  id: string
  patente: string
  marca: string
  modelo: string
  año: number
  kilometraje: number
  estado: 'operativo' | 'en_servicio' | 'fuera_de_servicio'
  observaciones?: string
  ultimo_servicio?: string
  activo: boolean
  created_at: string
  updated_at: string
}

export interface CamionCreate {
  patente: string
  marca: string
  modelo: string
  año: number
  kilometraje: number
  estado: 'operativo' | 'en_servicio' | 'fuera_de_servicio'
  observaciones?: string
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
  repuesto_id: string
  tipo: 'entrada' | 'salida' | 'ajuste'
  cantidad: number
  stock_anterior: number
  stock_nuevo: number
  motivo?: string
  observaciones?: string
  created_by: string
  created_at: string
}

// ==================== SERVICIO ====================

export interface Servicio {
  id: string
  camion_id: string
  camion_patente: string
  fecha: string
  tipo: 'preventivo' | 'correctivo' | 'reparacion'
  descripcion: string
  kilometraje_actual?: number
  proximo_servicio_km?: number
  costo_mano_obra: number
  costo_total: number
  observaciones?: string
  repuestos?: ServicioRepuesto[]
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
  tipo: 'preventivo' | 'correctivo' | 'reparacion'
  descripcion: string
  kilometraje_actual?: number | null
  proximo_servicio_km?: number | null
  costo_mano_obra: number
  observaciones?: string
  repuestos: RepuestoAsignado[]
}

// ==================== PESAJE ====================

export interface Pesaje {
  id: string
  numero_pesaje: number
  fecha: string
  camion_id: string
  camion_patente: string
  peso_tara: number
  peso_bruto: number
  peso_neto: number
  material: string
  cliente_destino: string
  observaciones?: string
  remito_generado: boolean
  created_by: string
  created_at: string
  updated_at: string
}

export interface PesajeCreate {
  camion_id: string
  fecha: string
  peso_tara: number
  peso_bruto: number
  material: string
  cliente_destino: string
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
  activo: boolean
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
  created_at: string
  updated_at: string
}

// ==================== DASHBOARD ====================

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
  }
  servicios_proximos: ServicioProximo[]
  ultimos_pesajes: UltimoPesaje[]
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
