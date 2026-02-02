# Skill: Database Design

## Objetivo
Diseñar y crear modelos de base de datos siguiendo las mejores prácticas para el proyecto.

## Convenciones de Diseño

### 1. Campos Estándar
Todos los modelos deben incluir:
```python
id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
activo = Column(Boolean, default=True, nullable=False)
created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
```

### 2. Tipos de Datos Comunes
```python
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Numeric, Text, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB

# Textos
nombre = Column(String(255), nullable=False)
descripcion = Column(Text, nullable=True)

# Números
cantidad = Column(Numeric(10, 2), nullable=False)  # Para decimales
precio = Column(Numeric(10, 2), nullable=False)
kilometraje = Column(Integer, nullable=True)

# Enums
estado = Column(SQLEnum('operativo', 'en_servicio', 'fuera_servicio', name='estado_camion'), nullable=False)

# JSON
documentos = Column(JSONB, nullable=True)  # Para arrays de URLs, metadata, etc

# Fechas
fecha = Column(DateTime, nullable=False)
```

### 3. Relaciones

**One-to-Many:**
```python
# Lado "Many" (Pesaje tiene un Camion)
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

class Pesaje(Base):
    __tablename__ = "pesajes"

    camion_id = Column(UUID(as_uuid=True), ForeignKey("camiones.id"), nullable=False)
    camion = relationship("Camion", back_populates="pesajes")

# Lado "One" (Camion tiene muchos Pesajes)
class Camion(Base):
    __tablename__ = "camiones"

    pesajes = relationship("Pesaje", back_populates="camion")
```

**Many-to-Many:**
```python
# Tabla de asociación
class ServicioRepuesto(Base):
    __tablename__ = "servicios_repuestos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    servicio_id = Column(UUID(as_uuid=True), ForeignKey("servicios.id"), nullable=False)
    repuesto_id = Column(UUID(as_uuid=True), ForeignKey("repuestos.id"), nullable=False)
    cantidad = Column(Numeric(10, 2), nullable=False)
    precio_unitario = Column(Numeric(10, 2), nullable=False)
    subtotal = Column(Numeric(10, 2), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

# En Servicio
class Servicio(Base):
    __tablename__ = "servicios"

    repuestos = relationship("ServicioRepuesto", back_populates="servicio")

# En Repuesto
class Repuesto(Base):
    __tablename__ = "repuestos"

    servicios = relationship("ServicioRepuesto", back_populates="repuesto")
```

### 4. Indices
```python
from sqlalchemy import Index

class Camion(Base):
    __tablename__ = "camiones"

    patente = Column(String(20), unique=True, nullable=False, index=True)

    __table_args__ = (
        Index('idx_camion_estado', 'estado', 'activo'),
        Index('idx_camion_patente', 'patente'),
    )
```

### 5. Constraints
```python
from sqlalchemy import CheckConstraint

class Pesaje(Base):
    __tablename__ = "pesajes"

    peso_tara = Column(Numeric(10, 2), nullable=False)
    peso_bruto = Column(Numeric(10, 2), nullable=False)
    peso_neto = Column(Numeric(10, 2), nullable=False)

    __table_args__ = (
        CheckConstraint('peso_bruto > peso_tara', name='check_peso_bruto_mayor_tara'),
        CheckConstraint('peso_neto = peso_bruto - peso_tara', name='check_peso_neto_calculado'),
    )
```

## Modelos del Proyecto

### Usuarios
```python
class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    nombre = Column(String(100), nullable=False)
    rol = Column(SQLEnum('administrador', 'operador', 'solo_lectura', name='rol_usuario'), nullable=False)
    activo = Column(Boolean, default=True, nullable=False)
    ultimo_acceso = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
```

### Camiones
```python
class Camion(Base):
    __tablename__ = "camiones"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patente = Column(String(20), unique=True, nullable=False, index=True)
    marca = Column(String(100), nullable=True)
    modelo = Column(String(100), nullable=True)
    anio = Column(Integer, nullable=True)
    tipo = Column(SQLEnum('volcador', 'acoplado', 'mixer', 'otro', name='tipo_camion'), nullable=False)
    estado = Column(SQLEnum('operativo', 'en_servicio', 'fuera_servicio', name='estado_camion'), nullable=False, default='operativo')
    kilometraje_actual = Column(Integer, nullable=True)
    horometro_actual = Column(Numeric(10, 2), nullable=True)
    chofer_habitual = Column(String(100), nullable=True)
    foto = Column(String(500), nullable=True)  # URL Cloudinary
    observaciones = Column(Text, nullable=True)
    activo = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relaciones
    servicios = relationship("Servicio", back_populates="camion")
    pesajes = relationship("Pesaje", back_populates="camion")
    suministros_combustible = relationship("SuministroCombustible", back_populates="camion")
```

### Repuestos
```python
class Repuesto(Base):
    __tablename__ = "repuestos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    codigo = Column(String(50), unique=True, nullable=True, index=True)
    nombre = Column(String(255), nullable=False)
    categoria = Column(String(100), nullable=True)
    stock_actual = Column(Numeric(10, 2), nullable=False, default=0)
    stock_minimo = Column(Numeric(10, 2), nullable=False, default=0)
    unidad = Column(String(20), nullable=False)  # unidades, litros, kg
    precio_unitario = Column(Numeric(10, 2), nullable=True)
    proveedor = Column(String(255), nullable=True)
    ubicacion_deposito = Column(String(100), nullable=True)
    activo = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relaciones
    movimientos = relationship("MovimientoStock", back_populates="repuesto")
    servicios_repuestos = relationship("ServicioRepuesto", back_populates="repuesto")

    __table_args__ = (
        CheckConstraint('stock_actual >= 0', name='check_stock_positivo'),
    )
```

### Servicios
```python
class Servicio(Base):
    __tablename__ = "servicios"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    camion_id = Column(UUID(as_uuid=True), ForeignKey("camiones.id"), nullable=False)
    fecha = Column(DateTime, nullable=False)
    tipo = Column(SQLEnum('preventivo', 'correctivo', 'emergencia', name='tipo_servicio'), nullable=False)
    descripcion = Column(Text, nullable=False)
    kilometraje_servicio = Column(Integer, nullable=True)
    horometro_servicio = Column(Numeric(10, 2), nullable=True)
    mecanico = Column(String(255), nullable=True)
    costo_mano_obra = Column(Numeric(10, 2), nullable=False, default=0)
    costo_total = Column(Numeric(10, 2), nullable=False, default=0)  # Calculado
    estado = Column(SQLEnum('programado', 'en_proceso', 'completado', name='estado_servicio'), nullable=False, default='programado')
    observaciones = Column(Text, nullable=True)
    documentos = Column(JSONB, nullable=True)  # URLs de fotos/documentos
    created_by = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relaciones
    camion = relationship("Camion", back_populates="servicios")
    repuestos = relationship("ServicioRepuesto", back_populates="servicio")
    created_by_user = relationship("Usuario")
```

### Pesajes
```python
class Pesaje(Base):
    __tablename__ = "pesajes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    numero_pesaje = Column(Integer, unique=True, nullable=False, autoincrement=True)
    fecha = Column(DateTime, nullable=False, default=datetime.utcnow)
    camion_id = Column(UUID(as_uuid=True), ForeignKey("camiones.id"), nullable=False)
    chofer = Column(String(100), nullable=False)
    peso_tara = Column(Numeric(10, 2), nullable=False)
    peso_bruto = Column(Numeric(10, 2), nullable=False)
    peso_neto = Column(Numeric(10, 2), nullable=False)  # Calculado
    material = Column(String(100), nullable=False)
    cliente_destino = Column(String(255), nullable=False)
    observaciones = Column(Text, nullable=True)
    remito_generado = Column(Boolean, default=False, nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relaciones
    camion = relationship("Camion", back_populates="pesajes")
    remito = relationship("Remito", back_populates="pesaje", uselist=False)
    created_by_user = relationship("Usuario")
```

## Migraciones con Alembic

### Crear Migración
```bash
alembic revision --autogenerate -m "Crear tabla camiones"
```

### Aplicar Migración
```bash
alembic upgrade head
```

### Revertir Migración
```bash
alembic downgrade -1
```

## Checklist de Implementación

- [ ] Incluir campos estándar (id, activo, created_at, updated_at)
- [ ] Definir relaciones con `relationship()` y `ForeignKey`
- [ ] Agregar índices para campos buscados frecuentemente
- [ ] Usar constraints para validación a nivel de BD
- [ ] Usar ENUM para campos con valores limitados
- [ ] Documentar el modelo con docstrings
- [ ] Crear migración Alembic
- [ ] Probar la migración en ambiente de desarrollo
