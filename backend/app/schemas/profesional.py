"""Pydantic schemas for Profesional, Servicio, Disponibilidad, ExcepcionDisponibilidad."""

from datetime import date, datetime, time

from pydantic import BaseModel, ConfigDict, EmailStr, Field, ValidationInfo, field_validator

# ============================================================================
# Pagination Schemas (Generic)
# ============================================================================

class PageParams(BaseModel):
    """Parámetros de paginación estándar."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"page": 1, "size": 20}
        }
    )

    page: int = Field(default=1, ge=1, description="Número de página (1-indexed)")
    size: int = Field(default=20, ge=1, le=100, description="Tamaño de página (máx 100)")


class FilterParams(BaseModel):
    """Parámetros de filtrado genéricos."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"q": "maria", "activo": True}
        }
    )

    q: str | None = Field(default=None, description="Búsqueda textual (nombre, email, etc.)")
    activo: bool | None = Field(default=None, description="Filtrar por estado activo")


class PageResponse(BaseModel):
    """Respuesta paginada estándar."""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "items": [],
                "total": 42,
                "page": 1,
                "size": 20,
                "pages": 3
            }
        }
    )

    items: list[object] = Field(description="Elementos de la página actual")
    total: int = Field(description="Total de elementos")
    page: int = Field(description="Página actual")
    size: int = Field(description="Tamaño de página")
    pages: int = Field(description="Total de páginas")


# ============================================================================
# Profesional Schemas
# ============================================================================

class ProfesionalBase(BaseModel):
    """Campos base de profesional."""

    nombre: str = Field(min_length=1, max_length=100, description="Nombre")
    apellido: str = Field(min_length=1, max_length=100, description="Apellido")
    telefono: str | None = Field(default=None, max_length=20, description="Teléfono")
    bio: str | None = Field(default=None, description="Biografía/descripción")
    foto_url: str | None = Field(default=None, max_length=500, description="URL de foto")
    slot_duracion_min: int = Field(default=30, ge=10, le=120, description="Duración base de slot en minutos")


class ProfesionalCreate(ProfesionalBase):
    """Schema para crear profesional (Admin)."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "juan.perez@salon.com",
                "password": "temppassword123",
                "nombre": "Juan",
                "apellido": "Pérez",
                "telefono": "+54911234567",
                "bio": "Peluquero con 10 años de experiencia",
                "slot_duracion_min": 30
            }
        }
    )

    email: EmailStr = Field(description="Email del profesional (se crea usuario PROVEEDOR)")
    password: str = Field(min_length=8, max_length=128, description="Contraseña temporal")


class ProfesionalUpdate(BaseModel):
    """Schema para actualizar profesional."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {
                "nombre": "Juan Carlos",
                "telefono": "+549119876543",
                "bio": "Peluquero especializado en colorimetría",
                "slot_duracion_min": 20
            }
        }
    )

    nombre: str | None = Field(default=None, min_length=1, max_length=100)
    apellido: str | None = Field(default=None, min_length=1, max_length=100)
    telefono: str | None = Field(default=None, max_length=20)
    bio: str | None = Field(default=None)
    foto_url: str | None = Field(default=None, max_length=500)
    slot_duracion_min: int | None = Field(default=None, ge=10, le=120)
    activo: bool | None = Field(default=None)


class ProfesionalResponse(ProfesionalBase):
    """Schema de respuesta para profesional."""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "user_id": 5,
                "email": "juan.perez@salon.com",
                "nombre": "Juan",
                "apellido": "Pérez",
                "telefono": "+54911234567",
                "bio": "Peluquero con 10 años de experiencia",
                "foto_url": "https://example.com/foto.jpg",
                "activo": True,
                "slot_duracion_min": 30,
                "created_at": "2026-01-15T10:30:00Z",
                "updated_at": "2026-01-15T10:30:00Z"
            }
        }
    )

    id: int
    user_id: int
    email: EmailStr
    activo: bool
    created_at: datetime
    updated_at: datetime


class ProfesionalListResponse(BaseModel):
    """Schema para listado de profesionales (Admin)."""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "items": [],
                "total": 42,
                "page": 1,
                "size": 20,
                "pages": 3
            }
        }
    )

    items: list[ProfesionalResponse]
    total: int
    page: int
    size: int
    pages: int


# ============================================================================
# Servicio Schemas
# ============================================================================

class ServicioBase(BaseModel):
    """Campos base de servicio."""

    nombre: str = Field(min_length=1, max_length=100, description="Nombre del servicio")
    descripcion: str | None = Field(default=None, description="Descripción del servicio")
    duracion_min: int = Field(gt=0, le=480, description="Duración en minutos (1-480)")
    precio: int = Field(ge=0, description="Precio en centavos (ej: 15000 = $150.00)")
    orden: int = Field(default=0, ge=0, description="Orden de visualización")


class ServicioCreate(ServicioBase):
    """Schema para crear servicio."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "nombre": "Corte de cabello",
                "descripcion": "Corte + lavado + peinado",
                "duracion_min": 45,
                "precio": 15000,
                "orden": 1
            }
        }
    )


class ServicioUpdate(BaseModel):
    """Schema para actualizar servicio."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {
                "nombre": "Corte de cabello premium",
                "duracion_min": 60,
                "precio": 20000
            }
        }
    )

    nombre: str | None = Field(default=None, min_length=1, max_length=100)
    descripcion: str | None = Field(default=None)
    duracion_min: int | None = Field(default=None, gt=0, le=480)
    precio: int | None = Field(default=None, ge=0)
    orden: int | None = Field(default=None, ge=0)
    activo: bool | None = Field(default=None)


class ServicioResponse(ServicioBase):
    """Schema de respuesta para servicio."""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "profesional_id": 1,
                "nombre": "Corte de cabello",
                "descripcion": "Corte + lavado + peinado",
                "duracion_min": 45,
                "precio": 15000,
                "activo": True,
                "orden": 1,
                "created_at": "2026-01-15T10:30:00Z",
                "updated_at": "2026-01-15T10:30:00Z"
            }
        }
    )

    id: int
    profesional_id: int
    activo: bool
    created_at: datetime
    updated_at: datetime


# ============================================================================
# Disponibilidad Schemas
# ============================================================================

class DisponibilidadBase(BaseModel):
    """Campos base de disponibilidad."""

    dia_semana: str = Field(pattern="^(LUNES|MARTES|MIERCOLES|JUEVES|VIERNES|SABADO|DOMINGO)$")
    hora_inicio: time
    hora_fin: time

    @field_validator("hora_fin")
    @classmethod
    def hora_fin_after_inicio(cls, v: time, info: ValidationInfo) -> time:
        if info.data.get("hora_inicio") and v <= info.data["hora_inicio"]:
            raise ValueError("hora_fin debe ser posterior a hora_inicio")
        return v


class DisponibilidadCreate(DisponibilidadBase):
    """Schema para crear disponibilidad."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "dia_semana": "LUNES",
                "hora_inicio": "09:00:00",
                "hora_fin": "13:00:00"
            }
        }
    )


class DisponibilidadUpdate(BaseModel):
    """Schema para actualizar disponibilidad."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "hora_inicio": "10:00:00",
                "hora_fin": "14:00:00",
                "activo": True
            }
        }
    )

    hora_inicio: time | None = Field(default=None)
    hora_fin: time | None = Field(default=None)
    activo: bool | None = Field(default=None)


class DisponibilidadResponse(DisponibilidadBase):
    """Schema de respuesta para disponibilidad."""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "profesional_id": 1,
                "dia_semana": "LUNES",
                "hora_inicio": "09:00:00",
                "hora_fin": "13:00:00",
                "activo": True,
                "created_at": "2026-01-15T10:30:00Z",
                "updated_at": "2026-01-15T10:30:00Z"
            }
        }
    )

    id: int
    profesional_id: int
    activo: bool
    created_at: datetime
    updated_at: datetime


class GrillaDisponibilidadResponse(BaseModel):
    """Respuesta completa de grilla semanal."""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "profesional_id": 1,
                "slot_duracion_min": 30,
                "grilla": [
                    {"dia_semana": "LUNES", "hora_inicio": "09:00:00", "hora_fin": "13:00:00", "activo": True},
                    {"dia_semana": "MARTES", "hora_inicio": "09:00:00", "hora_fin": "13:00:00", "activo": True}
                ]
            }
        }
    )

    profesional_id: int
    slot_duracion_min: int
    grilla: list[DisponibilidadResponse]


# ============================================================================
# ExcepcionDisponibilidad Schemas
# ============================================================================

class ExcepcionBase(BaseModel):
    """Campos base de excepción."""

    fecha: date = Field(description="Fecha de la excepción")
    tipo: str = Field(pattern="^(CERRADO|HORARIO_ESPECIAL)$", description="Tipo de excepción")
    hora_inicio: time | None = Field(default=None, description="Hora inicio (None = cerrado)")
    hora_fin: time | None = Field(default=None, description="Hora fin (None = cerrado)")
    motivo: str | None = Field(default=None, max_length=200, description="Motivo de la excepción")

    @field_validator("hora_fin")
    @classmethod
    def validar_horario_segun_tipo(cls, v: time | None, info: ValidationInfo) -> time | None:
        tipo = info.data.get("tipo")
        hora_inicio = info.data.get("hora_inicio")

        if tipo == "CERRADO":
            if hora_inicio is not None or v is not None:
                raise ValueError("Para tipo CERRADO, hora_inicio y hora_fin deben ser null")
        elif tipo == "HORARIO_ESPECIAL":
            if hora_inicio is None or v is None:
                raise ValueError("Para tipo HORARIO_ESPECIAL, hora_inicio y hora_fin son obligatorios")
            if v <= hora_inicio:
                raise ValueError("hora_fin debe ser posterior a hora_inicio")
        return v


class ExcepcionCreate(ExcepcionBase):
    """Schema para crear excepción."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "summary": "Día cerrado",
                    "value": {
                        "fecha": "2026-12-25",
                        "tipo": "CERRADO",
                        "motivo": "Navidad"
                    }
                },
                {
                    "summary": "Horario especial",
                    "value": {
                        "fecha": "2026-11-02",
                        "tipo": "HORARIO_ESPECIAL",
                        "hora_inicio": "10:00:00",
                        "hora_fin": "14:00:00",
                        "motivo": "Feriado puente"
                    }
                }
            ]
        }
    )


class ExcepcionUpdate(BaseModel):
    """Schema para actualizar excepción (solo motivo)."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "motivo": "Feriado puente - día de la familia"
            }
        }
    )

    motivo: str | None = Field(default=None, max_length=200)


class ExcepcionResponse(ExcepcionBase):
    """Schema de respuesta para excepción."""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "profesional_id": 1,
                "fecha": "2026-12-25",
                "tipo": "CERRADO",
                "hora_inicio": None,
                "hora_fin": None,
                "motivo": "Navidad",
                "created_at": "2026-01-15T10:30:00Z"
            }
        }
    )

    id: int
    profesional_id: int
    created_at: datetime


# ============================================================================
# Slots Schemas
# ============================================================================

class SlotResponse(BaseModel):
    """Schema para un slot disponible."""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "fecha": "2026-10-15",
                "hora_inicio": "10:00:00",
                "hora_fin": "10:30:00",
                "disponible": True
            }
        }
    )

    fecha: date
    hora_inicio: time
    hora_fin: time
    disponible: bool = True


class SlotsListResponse(BaseModel):
    """Respuesta de listado de slots."""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "profesional_id": 1,
                "slot_duracion_min": 30,
                "desde": "2026-10-15",
                "hasta": "2026-10-15",
                "slots": [
                    {"fecha": "2026-10-15", "hora_inicio": "10:00:00", "hora_fin": "10:30:00", "disponible": True}
                ],
                "total": 1
            }
        }
    )

    profesional_id: int
    slot_duracion_min: int
    desde: date
    hasta: date
    slots: list[SlotResponse]
    total: int


# ============================================================================
# Mi Perfil Schemas (para endpoint /profesionales/me)
# ============================================================================

class MiPerfilResponse(BaseModel):
    """Respuesta completa del perfil del profesional autenticado."""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "profesional": {"id": 1, "nombre": "Juan", "apellido": "Pérez"},
                "servicios": [],
                "disponibilidad": {"profesional_id": 1, "slot_duracion_min": 30, "grilla": []},
                "excepciones": []
            }
        }
    )

    profesional: ProfesionalResponse
    servicios: list[ServicioResponse]
    disponibilidad: GrillaDisponibilidadResponse
    excepciones: list[ExcepcionResponse]


# Resolve forward references
PageResponse.model_rebuild()
ProfesionalListResponse.model_rebuild()
MiPerfilResponse.model_rebuild()
SlotsListResponse.model_rebuild()


# ============================================================================
# Vistas públicas (CU-03 / CU-04): sin datos de contacto privados
# ============================================================================


class ServicioPublicResponse(BaseModel):
    """Servicio tal como lo ve un cliente."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    descripcion: str | None = None
    duracion_min: int
    precio: int = Field(description="Precio en centavos")


class ProfesionalPublicResponse(BaseModel):
    """Profesional tal como lo ve un cliente (sin email ni user_id)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    apellido: str
    bio: str | None = None
    foto_url: str | None = None
    slot_duracion_min: int
    activo: bool
    servicios: list[ServicioPublicResponse] = Field(default_factory=list)

    @classmethod
    def from_model(cls, profesional: object) -> "ProfesionalPublicResponse":
        """Build from a Profesional model keeping only active services, ordered."""
        data = cls.model_validate(profesional)
        servicios = sorted(
            (s for s in getattr(profesional, "servicios", []) if s.activo),
            key=lambda s: (s.orden, s.id),
        )
        data.servicios = [ServicioPublicResponse.model_validate(s) for s in servicios]
        return data


class ProfesionalPublicListResponse(BaseModel):
    """Listado público paginado de profesionales."""

    items: list[ProfesionalPublicResponse]
    total: int
    page: int
    size: int
    pages: int
