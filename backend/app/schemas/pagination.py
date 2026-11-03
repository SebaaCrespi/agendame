"""Generic pagination and filter schemas."""

from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


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


class PageResponse(BaseModel, Generic[T]):
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

    items: list[T] = Field(description="Elementos de la página actual")
    total: int = Field(description="Total de elementos")
    page: int = Field(description="Página actual")
    size: int = Field(description="Tamaño de página")
    pages: int = Field(description="Total de páginas")


def create_page_response(items: list[T], total: int, params: PageParams) -> PageResponse[T]:
    """Crear respuesta paginada a partir de items y parámetros."""
    pages = (total + params.size - 1) // params.size if params.size > 0 else 0
    return PageResponse[T](
        items=items,
        total=total,
        page=params.page,
        size=params.size,
        pages=pages
    )
