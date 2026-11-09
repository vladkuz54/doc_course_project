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
