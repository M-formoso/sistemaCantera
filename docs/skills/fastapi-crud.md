# Skill: FastAPI CRUD Pattern

## Objetivo
Generar CRUDs completos siguiendo las mejores prácticas de FastAPI y la arquitectura del proyecto.

## Patrón de Implementación

### 1. Model (SQLAlchemy)
```python
# backend/app/models/{entidad}.py
from sqlalchemy import Column, String, Boolean, DateTime, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
from app.db.base import Base

class Entidad(Base):
    __tablename__ = "{entidades}"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre = Column(String(255), nullable=False)
    activo = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
```

### 2. Schema (Pydantic)
```python
# backend/app/schemas/{entidad}.py
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from uuid import UUID
from typing import Optional

class EntidadBase(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=255)

class EntidadCreate(EntidadBase):
    pass

class EntidadUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=1, max_length=255)

class EntidadSchema(EntidadBase):
    id: UUID
    activo: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
```

### 3. Service Layer
```python
# backend/app/services/{entidad}_service.py
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from fastapi import HTTPException

from app.models.{entidad} import Entidad
from app.schemas.{entidad} import EntidadCreate, EntidadUpdate

def obtener_todos(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    solo_activos: bool = True
) -> List[Entidad]:
    """Obtiene lista de entidades con paginación."""
    query = db.query(Entidad)
    if solo_activos:
        query = query.filter(Entidad.activo == True)
    return query.offset(skip).limit(limit).all()

def obtener_por_id(db: Session, entidad_id: UUID) -> Optional[Entidad]:
    """Obtiene una entidad por ID."""
    return db.query(Entidad).filter(Entidad.id == entidad_id).first()

def crear(db: Session, entidad: EntidadCreate) -> Entidad:
    """Crea una nueva entidad."""
    db_entidad = Entidad(**entidad.model_dump())
    db.add(db_entidad)
    db.commit()
    db.refresh(db_entidad)
    return db_entidad

def actualizar(db: Session, entidad_id: UUID, entidad: EntidadUpdate) -> Entidad:
    """Actualiza una entidad existente."""
    db_entidad = obtener_por_id(db, entidad_id)
    if not db_entidad:
        raise HTTPException(status_code=404, detail="Entidad no encontrada")

    update_data = entidad.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_entidad, field, value)

    db.commit()
    db.refresh(db_entidad)
    return db_entidad

def eliminar(db: Session, entidad_id: UUID) -> Entidad:
    """Soft delete de una entidad."""
    db_entidad = obtener_por_id(db, entidad_id)
    if not db_entidad:
        raise HTTPException(status_code=404, detail="Entidad no encontrada")

    db_entidad.activo = False
    db.commit()
    db.refresh(db_entidad)
    return db_entidad
```

### 4. Endpoints (FastAPI)
```python
# backend/app/api/v1/endpoints/{entidad}.py
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.core.deps import get_db, get_current_active_user, require_admin
from app.models.usuario import Usuario
from app.schemas.{entidad} import EntidadSchema, EntidadCreate, EntidadUpdate
from app.services import {entidad}_service

router = APIRouter()

@router.get("/", response_model=List[EntidadSchema])
async def listar_entidades(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    solo_activos: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Lista todas las entidades con paginación."""
    return {entidad}_service.obtener_todos(
        db,
        skip=skip,
        limit=limit,
        solo_activos=solo_activos
    )

@router.post("/", response_model=EntidadSchema, status_code=status.HTTP_201_CREATED)
async def crear_entidad(
    entidad: EntidadCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    """Crea una nueva entidad."""
    return {entidad}_service.crear(db, entidad)

@router.get("/{id}", response_model=EntidadSchema)
async def obtener_entidad(
    id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Obtiene una entidad específica."""
    entidad = {entidad}_service.obtener_por_id(db, id)
    if not entidad:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entidad no encontrada"
        )
    return entidad

@router.put("/{id}", response_model=EntidadSchema)
async def actualizar_entidad(
    id: UUID,
    entidad: EntidadUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    """Actualiza una entidad existente."""
    return {entidad}_service.actualizar(db, id, entidad)

@router.delete("/{id}", response_model=EntidadSchema)
async def eliminar_entidad(
    id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    """Elimina (soft delete) una entidad."""
    return {entidad}_service.eliminar(db, id)
```

### 5. Registro del Router
```python
# backend/app/api/v1/api.py
from fastapi import APIRouter
from app.api.v1.endpoints import {entidad}

api_router = APIRouter()

api_router.include_router(
    {entidad}.router,
    prefix="/{entidades}",
    tags=["{entidades}"]
)
```

## Checklist de Implementación

- [ ] Crear modelo en `models/{entidad}.py`
- [ ] Crear schemas en `schemas/{entidad}.py`
- [ ] Crear service en `services/{entidad}_service.py`
- [ ] Crear endpoints en `api/v1/endpoints/{entidad}.py`
- [ ] Registrar router en `api/v1/api.py`
- [ ] Crear migración Alembic
- [ ] Escribir tests básicos

## Consideraciones Especiales

1. **Soft Delete**: Siempre usar campo `activo` en vez de eliminar registros
2. **Validación**: Usar Pydantic para validación de datos
3. **Dependency Injection**: Usar `Depends()` para DB session y autenticación
4. **Error Handling**: Usar HTTPException con códigos de estado apropiados
5. **Type Hints**: SIEMPRE usar type hints en todas las funciones
6. **Transacciones**: Usar `db.commit()` solo después de operaciones exitosas
