# Agendame

Sistema de gestión de turnos multi-prestador con asistente virtual (LangChain).

- **Frontend:** React + Vite + Tailwind
- **Backend:** FastAPI + SQLAlchemy (async) + SQLite
- **Asistente:** LangChain con proveedor configurable (Groq por defecto)

## Levantar todo con Docker

Requisito: [Docker Desktop](https://www.docker.com/products/docker-desktop/) abierto.

```bash
docker compose up --build
```

La primera vez tarda unos minutos en construir las imágenes. Después:

| Qué | Dónde |
|-----|-------|
| Aplicación | http://localhost:5173 |
| API (Swagger) | http://localhost:8000/docs |

Al iniciar, el backend crea la base y carga **datos de demo** automáticamente
(profesionales, servicios, horarios, clientes y turnos de esta semana y la siguiente).
Se puede volver a correr sin duplicar nada.

### Usuarios de prueba

| Rol | Email | Contraseña |
|-----|-------|------------|
| Administrador | admin@agendame.com | Admin12345 |
| Profesional (Juan Pérez) | juan@agendame.com | Prof12345 |
| Profesional (María Gómez) | maria@agendame.com | Prof12345 |
| Cliente (Ana López) | ana@agendame.com | Cliente12345 |
| Cliente (Beto Ruiz) | beto@agendame.com | Cliente12345 |
| Cliente | cliente@agendame.com | Cliente12345 |

También se puede reservar desde la home sin cuenta y crearla al confirmar.

### Asistente virtual (opcional)

El chat necesita una API key de Groq (gratuita en https://console.groq.com/keys).
Sin key, el resto de la aplicación funciona igual y el chat avisa que no está disponible.

```bash
cp .env.example .env      # y completar GROQ_API_KEY
docker compose up --build
```

El asistente aparece en las pantallas del cliente (por ejemplo, con ana@agendame.com).

### Comandos útiles

```bash
docker compose down                                         # apagar
docker compose down -v                                      # apagar y borrar la base
docker compose exec backend python scripts/seed_dev.py      # recargar datos de demo
docker compose logs -f backend                              # ver logs del backend
```

Si los puertos 5173 u 8000 están ocupados:

```bash
FRONTEND_PORT=3000 BACKEND_PORT=8080 docker compose up --build
```

En PowerShell: `$env:FRONTEND_PORT=3000; $env:BACKEND_PORT=8080; docker compose up --build`
(o poner esas variables en el archivo `.env`).

## Desarrollo local (sin Docker)

Ver [backend/README.md](backend/README.md) y [frontend/README.md](frontend/README.md).
Resumen:

```bash
cd backend && pip install -r requirements.txt && python scripts/seed_dev.py && uvicorn app.main:app --reload
cd frontend && npm install && npm run dev
```
