"""Pydantic schemas for Turno (appointments)."""

from datetime import date, datetime, time

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from app.schemas.pagination import PageResponse

# ============================================================================
# Turno Schemas
# ============================================================================

class TurnoBase(BaseModel):
    """Campos base de turno."""

    profesional_id: int = Field(ge=1, description="ID del profesional")
    servicio_id: int = Field(ge=1, description="ID del servicio")
    fecha: date = Field(description="Fecha del turno")
    hora_inicio: time = Field(description="Hora de inicio del turno")


class TurnoCreate(TurnoBase):
    """Schema para crear turno (reserva manual por cliente)."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "profesional_id": 1,
                "servicio_id": 1,
                "fecha": "2026-10-15",
                "hora_inicio": "10:00:00"
            }
        }
    )


class TurnoEstadoUpdate(BaseModel):
    """Schema para actualizar estado de turno (profesional)."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "nuevo_estado": "EN_CURSO"
            }
        }
    )

    nuevo_estado: str = Field(pattern="^(PENDIENTE|CONFIRMADO|EN_CURSO|FINALIZADO|CANCELADO_CLIENTE|CANCELADO_PROFESIONAL|NO_ASISTIO)$")


class TurnoReasignar(BaseModel):
    """Schema para reasignar turno a otro slot (profesional)."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "nueva_fecha": "2026-10-15",
                "nueva_hora_inicio": "11:00:00",
                "motivo": "Cambio de horario solicitado por cliente"
            }
        }
    )

    nueva_fecha: date = Field(description="Nueva fecha del turno")
    nueva_hora_inicio: time = Field(description="Nueva hora de inicio")
    motivo: str = Field(min_length=1, max_length=500, description="Motivo de la reasignación")


class TurnoCancelar(BaseModel):
    """Schema para cancelar turno (cliente o profesional)."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "motivo": "Imprevisto personal"
            }
        }
    )

    motivo: str = Field(min_length=1, max_length=500, description="Motivo de la cancelación")


class TurnoNotasUpdate(BaseModel):
    """Schema para actualizar notas del profesional."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "notas_profesional": "Cliente prefiere corte seco"
            }
        }
    )

    notas_profesional: str = Field(max_length=1000, description="Notas internas del profesional")


class TurnoFiltros(BaseModel):
    """Filtros para listado de turnos."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "estado": "CONFIRMADO",
                "desde": "2026-10-01",
                "hasta": "2026-10-31",
                "page": 1,
                "size": 20
            }
        }
    )

    estado: str | None = Field(default=None, pattern="^(PENDIENTE|CONFIRMADO|EN_CURSO|FINALIZADO|CANCELADO_CLIENTE|CANCELADO_PROFESIONAL|NO_ASISTIO)$")
    desde: date | None = Field(default=None, description="Fecha desde (inclusive)")
    hasta: date | None = Field(default=None, description="Fecha hasta (inclusive)")
    page: int = Field(default=1, ge=1, description="Número de página")
    size: int = Field(default=20, ge=1, le=100, description="Tamaño de página (máx 100)")


class TurnoResponse(BaseModel):
    """Schema de respuesta completa para turno."""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "cliente_id": 1,
                "profesional_id": 1,
                "servicio_id": 1,
                "fecha_inicio": "2026-10-15T10:00:00+00:00",
                "fecha_fin": "2026-10-15T10:45:00+00:00",
                "estado": "CONFIRMADO",
                "notas_cliente": "Quiero corte degradado",
                "notas_profesional": "Cliente prefiere corte seco",
                "cancelado_por": None,
                "motivo_cancelacion": None,
                "cancelado_en": None,
                "creado_por": "cliente",
                "creado_en": "2026-10-10T10:30:00+00:00",
                "actualizado_en": "2026-10-10T10:30:00+00:00",
                "confirmado_en": "2026-10-10T10:30:00+00:00",
                "finalizado_en": None
            }
        }
    )

    id: int
    cliente_id: int
    profesional_id: int
    servicio_id: int
    fecha_inicio: datetime
    fecha_fin: datetime
    estado: str
    notas_cliente: str | None = None
    notas_profesional: str | None = None
    cancelado_por: str | None = None
    motivo_cancelacion: str | None = None
    cancelado_en: datetime | None = None
    creado_por: str
    # El modelo usa created_at/updated_at; la API expone creado_en/actualizado_en
    creado_en: datetime = Field(validation_alias=AliasChoices("creado_en", "created_at"))
    actualizado_en: datetime = Field(validation_alias=AliasChoices("actualizado_en", "updated_at"))
    confirmado_en: datetime | None = None
    finalizado_en: datetime | None = None


class TurnoListResponse(PageResponse[TurnoResponse]):
    """Respuesta paginada de turnos."""

    items: list[TurnoResponse]


# ============================================================================
# Chatbot (Internal) Schemas
# ============================================================================

class ChatbotReservarRequest(BaseModel):
    """Request para crear turno desde chatbot (endpoint interno)."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "cliente_id": 1,
                "profesional_id": 1,
                "servicio_id": 1,
                "fecha": "2026-10-15",
                "hora_inicio": "10:00:00"
            }
        }
    )

    cliente_id: int = Field(ge=1, description="ID del cliente")
    profesional_id: int = Field(ge=1, description="ID del profesional")
    servicio_id: int = Field(ge=1, description="ID del servicio")
    fecha: date = Field(description="Fecha del turno")
    hora_inicio: time = Field(description="Hora de inicio del turno")


class ChatbotReservarResponse(BaseModel):
    """Response para creación de turno desde chatbot."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "turno_id": 1,
                "estado": "CONFIRMADO",
                "profesional_nombre": "Juan Pérez",
                "servicio_nombre": "Corte de cabello",
                "fecha": "2026-10-15",
                "hora_inicio": "10:00:00",
                "hora_fin": "10:45:00"
            }
        }
    )

    turno_id: int
    estado: str
    profesional_nombre: str
    servicio_nombre: str
    fecha: date
    hora_inicio: time
    hora_fin: time


# ============================================================================
# Disponibilidad Response (para endpoint público/cliente)
# ============================================================================

class SlotDisponibleResponse(BaseModel):
    """Slot individual disponible."""

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


class ProfesionalConSlotsResponse(BaseModel):
    """Profesional con sus slots agrupados por fecha."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "profesional_id": 1,
                "profesional_nombre": "Juan Pérez",
                "slot_duracion_min": 30,
                "slots_por_fecha": {
                    "2026-10-15": [
                        {"fecha": "2026-10-15", "hora_inicio": "10:00:00", "hora_fin": "10:30:00", "disponible": True},
                        {"fecha": "2026-10-15", "hora_inicio": "10:30:00", "hora_fin": "11:00:00", "disponible": False}
                    ],
                    "2026-10-16": [
                        {"fecha": "2026-10-16", "hora_inicio": "09:00:00", "hora_fin": "09:30:00", "disponible": True}
                    ]
                }
            }
        }
    )

    profesional_id: int
    profesional_nombre: str
    slot_duracion_min: int
    slots_por_fecha: dict[str, list[SlotDisponibleResponse]]


class DisponibilidadResponse(BaseModel):
    """Respuesta completa de disponibilidad (agrupada por profesional)."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "desde": "2026-10-15",
                "hasta": "2026-10-21",
                "profesionales": [
                    {
                        "profesional_id": 1,
                        "profesional_nombre": "Juan Pérez",
                        "slot_duracion_min": 30,
                        "slots_por_fecha": {
                            "2026-10-15": [
                                {"fecha": "2026-10-15", "hora_inicio": "10:00:00", "hora_fin": "10:30:00", "disponible": True}
                            ]
                        }
                    }
                ]
            }
        }
    )

    desde: date
    hasta: date
    profesionales: list[ProfesionalConSlotsResponse]


# Resolve forward references
TurnoListResponse.model_rebuild()
