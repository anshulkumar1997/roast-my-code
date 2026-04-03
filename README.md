# 🔥 Roast My Code

Paste any code snippet. Get roasted by AI. Receive real feedback. Learn something.

Built with **FastAPI** + **MongoDB Atlas** + **Redis** + **vanilla HTML/CSS/JS**. Runs entirely in **Docker**. Deployed on **Render**.
---

## Project Structure

```
roast-my-code/
├── .github/
│   ├── workflows/
│   │   ├── ci.yml              # lint → test on every push/PR
│   │   └── deploy.yml          # deploy on merge to main
│   └── pull_request_template.md
│
├── backend/
│   ├── app/
│   │   ├── main.py             # FastAPI app, lifespan, routing
│   │   ├── database.py         # MongoDB connection (Motor async)
│   │   ├── limiter.py          # Redis rate limiting (sliding window, per user)
│   │   ├── routers/
│   │   │   ├── roast.py        # POST /api/roast (protected, rate limited)
│   │   │   └── auth.py         # POST /api/auth/register, /login  GET /me
│   │   ├── services/
│   │   │   ├── roaster.py      # AI logic — calls Claude
│   │   │   └── auth.py         # password hashing (bcrypt) + JWT tokens
│   │   ├── middleware/
│   │   │   ├── errors.py       # global error handlers (incl. 429 with retry_after)
│   │   │   └── auth.py         # get_current_user dependency
│   │   └── models/
│   │       └── user.py         # Pydantic user schemas
│   ├── tests/
│   │   └── test_roast.py       # integration tests (AI, DB, Redis all mocked)
│   ├── requirements.txt        # production dependencies
│   ├── requirements-dev.txt    # dev/test dependencies
│   └── pyproject.toml          # ruff + pytest config
│
├── frontend/
│   ├── templates/index.html    # single page app
│   └── static/
│       ├── css/style.css       # dark terminal aesthetic
│       └── js/app.js           # auth flow, roast logic, rate limit countdown
│
├── Dockerfile                  # multi-stage: base → development → production
├── docker-compose.yml          # local development (app + Redis)
├── docker-compose.prod.yml     # production (app + Redis, no hot reload)
├── .env.example                # template — commit this, NEVER commit .env
├── .gitattributes              # consistent LF line endings
└── .gitignore
```

---

## Quick Start

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- An [OpenAI API Key](https://platform.openai.com/api-keys)
- [MongoDB Atlas](https://cloud.mongodb.com/) free cluster (M0)

### 1. Clone and configure

```bash
# 1. Clone
git clone https://github.com/anshulkumar1997/roast-my-code.git
cd roast-my-code

cp .env.example .env
# Edit .env — fill in your keys (see Environment Variables below)
```

### 2. Run

```bash
docker compose up --build
```

| URL | What's there |
|---|---|
| http://localhost:8000 | The app |
| http://localhost:8000/docs | Auto-generated API docs (Swagger UI) |
| http://localhost:8000/health | Health check |

---

## Environment Variables

Copy `.env.example` → `.env` and fill in:

| Variable | Required | Description |
|---|---|---|
| `OPENAI_API_KEY` | ✅ | Get from [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys) |
| `MONGODB_URL` | ✅ | Atlas connection string: `mongodb+srv://user:pass@cluster.mongodb.net/` |
| `DB_NAME` | No | Database name (default: `roastmycode`) |
| `JWT_SECRET` | ✅ | Long random string — signs auth tokens |
| `JWT_ALGORITHM` | No | Default: `HS256` |
| `JWT_EXPIRE_MINUTES` | No | Default: `30` |
| `REDIS_URL` | No | Default: `redis://redis:6379` (Docker sets this automatically) |
| `ENVIRONMENT` | No | `development` or `production` |
| `PORT` | No | Default: `8000` |

> **Generate a strong JWT_SECRET:**
> ```bash
> python -c "import secrets; print(secrets.token_hex(32))"
> ```

---

## Docker Commands

| Command | What it does |
|---|---|
| `docker compose up --build` | Build + start (use after changing requirements.txt) |
| `docker compose up` | Start without rebuilding |
| `docker compose down` | Stop everything |
| `docker compose logs -f` | Stream live logs |
| `docker compose exec app bash` | Shell inside the running container |

> **Live reload is on** — changes to `backend/` and `frontend/` reflect instantly.

---

## API Endpoints

### Auth
| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api/auth/register` | ❌ | Create account, returns JWT |
| POST | `/api/auth/login` | ❌ | Login, returns JWT |
| GET | `/api/auth/me` | ✅ | Get current user info |

### Roast (protected + rate limited)
| Method | Path | Limit | Description |
|---|---|---|---|
| POST | `/api/roast` | 2/hour per user | Submit code, get roasted |

### Other
| Method | Path | Description |
|---|---|---|
| GET | `/health` | Health check |

**How to authenticate:**
All protected routes require a JWT token in the `Authorization` header:
```
Authorization: Bearer <your-token>
```

**Example flow:**
```bash
# 1. Register
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "you@example.com", "password": "mypassword"}'
# → {"access_token": "eyJ...", "token_type": "bearer"}
 
# 2. Roast some code
curl -X POST http://localhost:8000/api/roast \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJ..." \
  -d '{"code": "x = 1\nprint(x)", "language": "python"}'
```

---

## Rate Limiting
 
Rate limits are enforced **per user** (not per IP) using a Redis sliding window:
 
| Endpoint | Limit |
|---|---|
| `POST /api/roast` | 2 requests / hour |
| `POST /api/auth/register` | 3 requests / minute |
| `POST /api/auth/login` | 5 requests / minute |
 
When a limit is hit, the API returns:
```json
HTTP 429 Too Many Requests
{"detail": "Rate limit exceeded", "retry_after": 3547}
```
 
The frontend shows a live countdown on the button until the limit resets.
 
---

## Running Tests

```bash
# Inside Docker (recommended)
docker compose exec app bash -c "cd /app/backend && pytest"

# With coverage
docker compose exec app bash -c "cd /app/backend && pytest --cov=app --cov-report=term-missing"
```
Tests mock all external services (AI, MongoDB, Redis) — no real infrastructure needed.

---

## Linting & Formatting

```bash
# Check
docker compose exec app bash -c "ruff check backend/app backend/tests"

# Fix
docker compose exec app bash -c "ruff check --fix backend/app backend/tests"

# Format
docker compose exec app bash -c "ruff format backend/app backend/tests"
```

---

## Deployment (Render)
 
This app is deployed on [Render](https://render.com) using Docker.
 
### Services on Render
| Service | Type | Plan |
|---|---|---|
| `roast-my-code` | Web Service (Docker) | Free |
| `roast-redis` | Redis | Free |
 
### Environment variables to set on Render
All variables from `.env.example` except `REDIS_URL` — Render injects that automatically when you link the Redis service.
 
### Auto-deploy
Render watches the `main` branch — every merge triggers a new deployment automatically.
 
---

## Git Workflow

```
main      ← production, always stable, CI must pass
develop   ← integration branch, PRs merge here
feature/* ← your daily work branches
hotfix/*  ← urgent production fixes
```

```bash
git checkout -b feature/my-feature
# ...make changes...
git add .
git commit -m "feat: add my feature"
git push origin feature/my-feature
# Open Pull Request → develop
```

**Commit conventions:**
```
feat:     new feature
fix:      bug fix
test:     adding/updating tests
refactor: code cleanup
docs:     documentation only
chore:    deps, config changes
```

---

## CI/CD Pipeline

```
Push / PR to main or develop
         │
         ▼
    [Lint & Format]   ← ruff check + ruff format --check
         │
         ▼
      [Tests]         ← pytest (AI, DB, Redis all mocked)
         │
         ▼
      (main only)
         │
         ▼
    [Render deploys automatically]
```

**GitHub Secrets to add** (Settings → Secrets → Actions):

| Secret | Value |
|---|---|
| `OPENAI_API_KEY` | Your OpenAI key |
| `MONGODB_URL` | Your Atlas connection string |
| `JWT_SECRET` | Your JWT secret |


---

## Adding a New Feature — Checklist

1. `git checkout -b feature/your-feature`
2. Add route in `backend/app/routers/`
3. Add business logic in `backend/app/services/`
4. Register router in `main.py`
5. Write tests in `backend/tests/` — mock external calls
6. `pytest` → `ruff check` → commit → PR

---

## Versioning

`MAJOR.MINOR.PATCH` — [semver.org](https://semver.org)

```bash
git tag -a v1.1.0 -m "feat: add user auth"
git push origin v1.1.0
```