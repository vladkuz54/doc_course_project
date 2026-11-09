# Fleet Management

A web app for managing a vehicle fleet: drivers, vehicles, routes, fuel, repairs, insurance, reports and notifications.

- **Backend:** FastAPI and SQLAlchemy (Python 3.13)
- **Frontend:** Next.js and React
- **Database:** PostgreSQL 17

## Run with Docker

You need Docker with Compose, and ports `3000`, `8000` and `5432` must be free.

```bash
docker compose up --build
```

The first build takes a few minutes. Then open:

| What | URL |
| --- | --- |
| App | http://localhost:3000 |
| API docs | http://localhost:8000/docs |

On first start, the backend creates the tables and fills the empty database with demo data. Data is kept between restarts.

### Demo logins

| Role | Username | Password |
| --- | --- | --- |
| Admin | `admin` | `admin` |
| Driver | `petrenko`, `kovalenko`, `shevchenko`, `bondar`, `melnyk` | `password` |

These passwords are public, so don't expose the demo data on a shared network.

### Everyday commands

| Task | Command |
| --- | --- |
| Start in the background | `docker compose up -d` |
| Rebuild after a code change | `docker compose up --build -d` |
| Follow the logs | `docker compose logs -f` |
| Stop | `docker compose down` |
| Reset to fresh demo data (deletes all current data) | `docker compose exec backend python -m backend.dal.generate_data` |
| Stop and delete the database (deletes all current data) | `docker compose down -v` |

## Configuration

All settings are optional. To change one, set it in your shell or in a `.env` file next to `compose.yaml`.

| Variable | Default | Purpose |
| --- | --- | --- |
| `POSTGRES_PASSWORD` | `fleet` | Database password. It only applies when the database is first created. |
| `JWT_SECRET_KEY` | random at each start | Signs login tokens. Set it to keep users logged in across backend restarts. |
| `TZ` | `Europe/Kyiv` | Backend timezone. Route times are compared with this clock, so use the fleet's local timezone. |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Backend URL as seen from the browser. It is built into the frontend, so rebuild after changing it. |
| `CORS_ORIGINS` | `http://localhost:3000` | Comma-separated frontend URLs allowed to call the API. |

To run on another machine, set both URLs to its address and rebuild:

```bash
NEXT_PUBLIC_API_URL=http://<server>:8000 CORS_ORIGINS=http://<server>:3000 docker compose up --build -d
```

## Run for development

You need [uv](https://docs.astral.sh/uv/), Node.js 20.9 or newer, and Docker for the database.

1. Start only the database:

   ```bash
   docker compose up -d db
   ```

2. In a second terminal, create the tables and demo data if the database is empty, then start the backend at http://localhost:8000:

   ```bash
   uv sync
   uv run python -m backend.dal.generate_data --if-empty
   uv run uvicorn backend.main:app --reload
   ```

3. In a third terminal, start the frontend at http://localhost:3000:

   ```bash
   cd src/frontend
   npm install
   npm run dev
   ```

## Tests

The backend tests create their own temporary SQLite database, so they don't need Docker and don't touch your data:

```bash
uv run python -m unittest discover -s tests -t tests
```

The full suite takes several minutes because it reseeds the database for each test.
