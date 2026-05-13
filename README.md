# AI Project Management SaaS

Production-ready scaffold: Django + DRF + Channels + MySQL + Redis + OpenAI, with a vanilla JS / Tailwind frontend.

> Note: this codebase lives in the `saas/` folder of a Lovable project. The Lovable preview runs a React app (`src/`); this Django app does **not** run in that preview. Use Docker Compose locally.

## Stack

| Layer | Tech |
|---|---|
| Frontend | HTML5, Tailwind (CDN), Vanilla JS, Chart.js, SortableJS |
| Backend | Django 5, DRF, Django Channels, SimpleJWT |
| Realtime | Channels + Redis (WebSockets) |
| DB | MySQL 8 |
| AI | OpenAI API |
| Deploy | Docker Compose, Nginx, Gunicorn, Daphne |

## Quick start

```bash
cd saas
cp .env.example .env          # fill OPENAI_API_KEY, SECRET_KEY, etc.
docker compose up --build
# Backend:  http://localhost:8000
# Frontend: http://localhost (served by nginx)
```

First run:

```bash
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py createsuperuser
```

## Layout

```
saas/
├── backend/        Django project (core/, apps/, api/, websocket/, services/)
├── frontend/       Static HTML/CSS/JS site
├── nginx/          Reverse-proxy config
├── docker-compose.yml
└── .env.example
```

## API

Versioned under `/api/v1/`:

- `auth/`        register, login, refresh, logout, google, password reset
- `users/`       profile, list, roles
- `projects/`    CRUD, members, invites, archive
- `tasks/`       CRUD, subtasks, comments, attachments, reorder
- `notifications/`  list, mark read
- `analytics/`   project, team, productivity
- `ai/`          generate-subtasks, plan-project, suggest
- `uploads/`     signed file uploads

## WebSockets

- `ws/projects/<id>/`  task sync, presence, typing, comments
- `ws/notifications/`  per-user notification stream

## Auth

JWT (access + refresh) via SimpleJWT. Google OAuth via `dj-rest-auth` + `allauth`. Roles: `admin`, `manager`, `developer` enforced via DRF permissions.

## Security

CSRF, XSS headers, SQL-injection-safe ORM, file-type/size validation, DRF throttling, secure cookies, audit log on writes.

## Docs

See `docs/` for: architecture overview, API reference, deployment, scaling notes.
