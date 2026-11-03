"""Public profesionales listing (used by the booking flow, CU-04) and admin listing."""

from app.models.profesional import Servicio

BASE = "/api/v1/profesionales"


class TestListadoPublico:
    async def test_incluye_solo_servicios_activos(
        self, async_client, auth_headers, db_session, sample_profesional, sample_servicio
    ):
        db_session.add_all(
            [
                Servicio(profesional_id=sample_profesional.id, nombre="Barba", duracion_min=20, precio=300000),
                Servicio(
                    profesional_id=sample_profesional.id, nombre="Viejo", duracion_min=30, precio=1, activo=False
                ),
            ]
        )
        await db_session.commit()
        await db_session.refresh(sample_profesional, ["servicios"])

        response = await async_client.get(BASE, headers=auth_headers)
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["total"] == 1
        prof = data["items"][0]
        assert prof["id"] == sample_profesional.id
        assert {s["nombre"] for s in prof["servicios"]} == {"Corte", "Barba"}
        assert prof["servicios"][0].keys() >= {"id", "nombre", "duracion_min", "precio"}

    async def test_excluye_inactivos(self, async_client, auth_headers, make_profesional):
        await make_profesional(nombre="Activo")
        await make_profesional(nombre="Inactivo", activo=False)
        response = await async_client.get(BASE, headers=auth_headers)
        assert [p["nombre"] for p in response.json()["items"]] == ["Activo"]

    async def test_sin_datos_privados(self, async_client, auth_headers, sample_profesional):
        response = await async_client.get(BASE, headers=auth_headers)
        prof = response.json()["items"][0]
        assert "email" not in prof
        assert "user_id" not in prof

    async def test_detalle_publico(self, async_client, auth_headers, sample_profesional, sample_servicio):
        response = await async_client.get(f"{BASE}/{sample_profesional.id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "email" not in data
        assert data["servicios"][0]["nombre"] == "Corte"


class TestListadoAdmin:
    async def test_admin_ve_email(self, async_client, admin_headers, sample_profesional, db_session):
        from app.models.user import User

        user = await db_session.get(User, sample_profesional.user_id)
        response = await async_client.get("/api/v1/admin/profesionales", headers=admin_headers)
        assert response.status_code == 200, response.text
        assert response.json()["items"][0]["email"] == user.email
