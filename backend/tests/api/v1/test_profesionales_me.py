"""Endpoints /profesionales/me (CU-02) cuando el id de usuario != id de profesional."""

import pytest

from app.models.profesional import Servicio
from app.models.user import User, UserRole
from app.repositories.user_repo import UserRepo
from tests.conftest import headers_for, proximo_dia_habil, unique_email

BASE = "/api/v1/profesionales/me"


@pytest.fixture
async def ids_distintos(db_session, make_profesional):
    # Un usuario "de relleno" antes: el usuario del profesional queda con otro id que su perfil
    await UserRepo(db_session).create(unique_email("relleno"), "Clave12345", "Relleno", UserRole.ADMIN)
    await db_session.commit()
    prof = await make_profesional(nombre="Ids")
    assert prof.user_id != prof.id
    db_session.add(Servicio(profesional_id=prof.id, nombre="Corte", duracion_min=30, precio=1))
    await db_session.commit()
    user = await db_session.get(User, prof.user_id)
    return prof, headers_for(user)


class TestMeConIdsDistintos:
    async def test_mi_grilla(self, async_client, ids_distintos):
        response = await async_client.get(f"{BASE}/disponibilidad", headers=ids_distintos[1])
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["profesional_id"] == ids_distintos[0].id
        assert len(data["grilla"]) == 7

    async def test_mis_servicios(self, async_client, ids_distintos):
        response = await async_client.get(f"{BASE}/servicios", headers=ids_distintos[1])
        assert response.status_code == 200
        assert [s["nombre"] for s in response.json()] == ["Corte"]

    async def test_crear_servicio(self, async_client, ids_distintos):
        response = await async_client.post(
            f"{BASE}/servicios",
            json={"nombre": "Barba", "duracion_min": 20, "precio": 300000},
            headers=ids_distintos[1],
        )
        assert response.status_code == 201, response.text
        assert response.json()["profesional_id"] == ids_distintos[0].id

    async def test_excepciones(self, async_client, ids_distintos):
        fecha = proximo_dia_habil(5).isoformat()
        created = await async_client.post(
            f"{BASE}/excepciones", json={"fecha": fecha, "tipo": "CERRADO"}, headers=ids_distintos[1]
        )
        assert created.status_code == 201, created.text
        listed = await async_client.get(f"{BASE}/excepciones", headers=ids_distintos[1])
        assert [e["fecha"] for e in listed.json()] == [fecha]

    async def test_proveedor_sin_perfil_404(self, async_client, profesional_headers):
        response = await async_client.get(f"{BASE}/disponibilidad", headers=profesional_headers)
        assert response.status_code == 404
