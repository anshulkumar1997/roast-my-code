# 🔥 Roast My Code

Paste any code snippet. Get roasted by AI. Receive real feedback. Learn something.

Built with **FastAPI** (Python backend) + **vanilla HTML/CSS/JS** frontend. Runs entirely in **Docker** — no local Python install needed.

---

## Project Structure

```
roast-my-code/
├── .github/
│   ├── workflows/
│   │   ├── ci.yml          # lint → test on every push/PR
│   │   └── deploy.yml      # deploy on merge to main
│   └── pull_request_template.md
│
├── backend/
│   ├── app/
│   │   ├── main.py             # FastAPI app, middleware, routing
│   │   ├── routers/
│   │   │   └── roast.py        # POST /api/roast — request/response schemas + route
│   │   ├── services/
│   │   │   └── roaster.py      # AI logic — calls Claude, parses JSON response
│   │   └── middleware/
│   │       └── errors.py       # Global error handlers
│   ├── tests/
│   │   └── test_roast.py       # Integration tests (AI is mocked)
│   ├── requirements.txt        # Production dependencies
│   ├── requirements-dev.txt    # Dev/test dependencies
│   └── pyproject.toml          # Ruff + pytest config
│
├── frontend/
│   ├── templates/
│   │   └── index.html          # Single page app
│   └── static/
│       ├── css/style.css       # Dark terminal aesthetic
│       └── js/app.js           # fetch API, animations, keyboard shortcuts
│
├── Dockerfile                  # Builds the Python 3.11 app image
├── docker-compose.yml          # Orchestrates the app (+ db when added)
├── .dockerignore               # Keeps the image lean
├── .env.example                # Commit this. NEVER commit .env
├── .gitignore
└── CHANGELOG.md
```

---

## Quick Start

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- An [Anthropic API key](https://console.anthropic.com/)

### Run the app

```bash
# 1. Clone
git clone https://github.com/you/roast-my-code.git
cd roast-my-code

# 2. Set up your environment variables
cp .env.example .env
# Open .env and add your ANTHROPIC_API_KEY

# 3. Build and start
docker compose up --build
```

App runs at → http://localhost:8000
API docs at → http://localhost:8000/docs

That's it. No Python install, no virtual environment, no version conflicts.

---

## Docker Commands

| Command | What it does |
|---|---|
| `docker compose up --build` | Build image + start (use after changing requirements.txt) |
| `docker compose up` | Start without rebuilding (faster, for code-only changes) |
| `docker compose down` | Stop everything |
| `docker compose logs -f` | Stream live logs |
| `docker compose exec app bash` | Open a shell inside the running container |

> **Live reload is enabled** — code changes in `backend/` and `frontend/` reflect instantly without restarting.

---

## Running Tests

Tests run inside Docker so the environment matches production exactly:

```bash
# Run all tests
docker compose exec app bash -c "cd /app/backend && pytest"

# With coverage report
docker compose exec app bash -c "cd /app/backend && pytest --cov=app --cov-report=term-missing"
```

Or if you prefer locally (requires Python 3.11 + dev deps):

```bash
pip install -r backend/requirements-dev.txt
cd backend && pytest
```

---

## Linting & Formatting

```bash
# Check for lint errors
docker compose exec app bash -c "cd /app/backend && ruff check app tests"

# Auto-fix lint errors
docker compose exec app bash -c "cd /app/backend && ruff check --fix app tests"

# Format code
docker compose exec app bash -c "cd /app/backend && ruff format app tests"
```

---

## API

### `POST /api/roast`

**Request:**
```json
{
  "code": "def foo():\n    x = 1\n    return x",
  "language": "python"
}
```

**Response:**
```json
{
  "roast": "This function is so pointless it makes philosophers question existence.",
  "feedback": "This function adds no value — inline the value or remove it entirely.",
  "rating": 3
}
```

**Validation:**
- `code` — required, non-empty, max 5000 characters
- `language` — optional, defaults to `"auto"`

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | Yes | Get from [console.anthropic.com](https://console.anthropic.com) |
| `ENVIRONMENT` | No | `development` or `production` (default: `development`) |
| `PORT` | No | Default: `8000` |

---

## Git Workflow

```
main      ← production, always stable, CI must pass
develop   ← integration branch, PRs merge here
feature/* ← your daily work branches
hotfix/*  ← urgent production fixes
```

**Daily flow:**
```bash
git checkout develop
git checkout -b feature/add-language-detection
# ...make changes...
git add .
git commit -m "feat: add automatic language detection"
git push origin feature/add-language-detection
# Open Pull Request → develop
```

**Commit message convention:**
```
feat:     new feature
fix:      bug fix
test:     adding/updating tests
refactor: code change that isn't a fix or feature
docs:     documentation only
chore:    dependency updates, config changes
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
      [Tests]         ← pytest with coverage, AI is mocked
         │
    (main only)
         ▼
      [Deploy]        ← your deployment step here
```

**GitHub Secrets needed** (Settings → Secrets → Actions):
- `SERVER_HOST` — your server's IP or hostname
- `SERVER_USER` — SSH username
- `SERVER_SSH_KEY` — your private SSH key

---

## Adding a New Feature

1. Create a new router in `backend/app/routers/`
2. Create a service in `backend/app/services/`
3. Register the router in `main.py`
4. Write tests in `backend/tests/` — mock external calls
5. `pytest` → `ruff check` → commit → PR

---

## Versioning

`MAJOR.MINOR.PATCH` — see [semver.org](https://semver.org)

```bash
git tag -a v1.1.0 -m "feat: add language detection"
git push origin v1.1.0
```
