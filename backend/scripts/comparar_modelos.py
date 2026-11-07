"""
Compara modelos para el chatbot (CU-05/06) con conversaciones guionadas.

Uso (desde backend/):
    python scripts/comparar_modelos.py
    python scripts/comparar_modelos.py groq:openai/gpt-oss-120b nvidia:openai/gpt-oss-20b

Corre sobre una COPIA temporal de agendame.db (no toca la DB de desarrollo) y solo
prueba los proveedores que tengan key en el .env. Necesita los datos del seed
(Juan Pérez con "Corte" y el cliente cliente@agendame.com).
"""

import asyncio
import os
import shutil
import sys
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))

# La copia de la DB tiene que estar configurada ANTES de importar la app
_tmp = Path(tempfile.mkdtemp(prefix="agendame_cmp_"))
shutil.copy(BACKEND / "agendame.db", _tmp / "agendame.db")
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{(_tmp / 'agendame.db').as_posix()}"

from sqlalchemy import select  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.core.database import async_session_maker  # noqa: E402
from app.models.cliente import Cliente  # noqa: E402
from app.models.user import User  # noqa: E402
from app.services import chatbot_service  # noqa: E402
from app.services.chat_llm import ChatNoConfiguradoError, crear_llm  # noqa: E402
from app.services.chatbot_service import (  # noqa: E402
    ChatbotService,
    ChatSessionStore,
    ProveedorChatError,
)

MODELOS_POR_DEFECTO = [
    "groq:openai/gpt-oss-120b",
    "groq:openai/gpt-oss-20b",
    "nvidia:openai/gpt-oss-20b",
    "nvidia:deepseek-ai/deepseek-v4.1-flash",
    "nvidia:nvidia/nemotron-3.5-lightning-30b-a3b",
    "nvidia:z-ai/glm-5.3-flash",
]


@dataclass
class Paso:
    mensaje: str
    deben: set[str] = field(default_factory=set)  # herramientas que tienen que aparecer
    no_deben: set[str] = field(default_factory=set)  # herramientas prohibidas en este paso


CASOS: dict[str, list[Paso]] = {
    "consulta": [
        Paso("¿Qué horarios tiene Juan mañana para un corte?", {"consultar_disponibilidad"}, {"reservar_turno"}),
    ],
    "inexistente": [
        Paso("¿Atiende Pedro Martínez? Quiero un corte con él.", {"buscar_profesionales"}, {"reservar_turno"}),
    ],
    "reserva": [
        Paso("Quiero un corte con Juan mañana a las 11:00", set(), {"reservar_turno"}),
        Paso("Sí, confirmo", {"reservar_turno"}),
    ],
    "cancelación": [
        Paso("Quiero cancelar mi próximo turno", {"mis_turnos"}, {"cancelar_turno"}),
        Paso("Sí, cancelalo, tengo un viaje", {"cancelar_turno"}),
    ],
}


_CREAR_ORIGINAL = chatbot_service.crear_herramientas


def _registrar_llamadas(usadas: list[str]) -> None:
    """Envuelve las herramientas para anotar cuáles pide el modelo."""
    original = _CREAR_ORIGINAL

    def con_registro(session, cliente_id, acciones):  # type: ignore[no-untyped-def]
        herramientas = original(session, cliente_id, acciones)
        for h in herramientas:
            coro = h.coroutine  # type: ignore[attr-defined]

            async def envuelta(*a, _coro=coro, _nombre=h.name, **k):  # type: ignore[no-untyped-def]
                usadas.append(_nombre)
                return await _coro(*a, **k)

            h.coroutine = envuelta  # type: ignore[attr-defined]
        return herramientas

    chatbot_service.crear_herramientas = con_registro  # type: ignore[assignment]


async def _cliente_demo() -> tuple[int, int]:
    async with async_session_maker() as s:
        user = await s.scalar(select(User).where(User.email == "cliente@agendame.com"))
        if user is None:
            raise SystemExit("Falta cliente@agendame.com: corré scripts/seed_dev.py")
        cliente = await s.scalar(select(Cliente).where(Cliente.user_id == user.id))
        assert cliente is not None
        return user.id, cliente.id


async def _correr_caso(llm, pasos: list[Paso], user_id: int, cliente_id: int) -> tuple[bool, list[str], float, str]:  # type: ignore[no-untyped-def]
    store = ChatSessionStore(10, 3600)
    session_id = None
    todas: list[str] = []
    ok = True
    inicio = time.perf_counter()
    ultima = ""
    for paso in pasos:
        usadas: list[str] = []
        _registrar_llamadas(usadas)
        async with async_session_maker() as s:
            r = await ChatbotService(s, llm, store).responder(paso.mensaje, session_id, user_id, cliente_id)
        session_id, ultima = r.session_id, r.respuesta
        todas += usadas
        if not paso.deben <= set(usadas) or paso.no_deben & set(usadas):
            ok = False
    return ok, todas, time.perf_counter() - inicio, ultima


async def main(modelos: list[str]) -> None:
    user_id, cliente_id = await _cliente_demo()
    filas = []
    for spec in modelos:
        proveedor, _, modelo = spec.partition(":")
        cfg = settings.model_copy(update={"CHAT_PROVIDER": proveedor, "CHAT_MODEL": modelo})
        try:
            llm = crear_llm(cfg)
        except ChatNoConfiguradoError as e:
            print(f"- {spec}: salteado ({e})")
            continue
        for nombre, pasos in CASOS.items():
            try:
                ok, usadas, segundos, respuesta = await _correr_caso(llm, pasos, user_id, cliente_id)
                filas.append((spec, nombre, "OK" if ok else "FALLA", f"{segundos:.1f}s", ", ".join(usadas) or "-", respuesta[:70]))
            except ProveedorChatError as e:
                filas.append((spec, nombre, "ERROR", "-", "-", str(e)[:70]))
    chatbot_service.crear_herramientas = _CREAR_ORIGINAL  # type: ignore[assignment]

    if not filas:
        print("\nNingún proveedor con key. Cargá GROQ_API_KEY y/o NVIDIA_API_KEY en backend/.env.")
        return
    print()
    ancho = [max(len(str(f[i])) for f in filas) for i in range(4)]
    for f in filas:
        print("  ".join(str(f[i]).ljust(ancho[i]) for i in range(4)), "|", f[4], "|", f[5])


if __name__ == "__main__":
    try:
        asyncio.run(main(sys.argv[1:] or MODELOS_POR_DEFECTO))
    finally:
        shutil.rmtree(_tmp, ignore_errors=True)
