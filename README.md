# Advanced Dual-Mode Calculator (FastAPI & CLI)

A professional-grade, dual-mode Calculator built in Python featuring a full **CLI REPL** and a **FastAPI Web Server** with a Glassmorphism frontend. Both interfaces share the same modular core logic, organized into clean sub-packages (`core/`, `cli/`, `api/`).

[![CI/CD Pipeline](https://github.com/sairamcharan9/CALCULATOR_WEB_SYSTEMS/actions/workflows/ci.yml/badge.svg)](https://github.com/sairamcharan9/CALCULATOR_WEB_SYSTEMS/actions/workflows/ci.yml)
[![Docker Hub](https://img.shields.io/docker/pulls/sb2853/calculator-web-systems)](https://hub.docker.com/r/sb2853/calculator-web-systems)

---

## 🚀 Features

- **Dual Interaction Modes** — FastAPI SPA and interactive CLI REPL
- **Modular Architecture** — Clean sub-package layout (`app/core`, `app/cli`, `app/api`)
- **10 Arithmetic Operations** — Add, Subtract, Multiply, Divide, Power, Root, Modulus, Int Divide, Percent, Abs Diff
- **Persistent History** — Pandas DataFrame backed by `data/history.csv`; full Undo/Redo via Memento pattern
- **Memory Commands** — Store, Recall, Clear named memory slots
- **JWT Authentication** — `/register` + `/login` with bcrypt hashing, `python-jose` JWT (HS256), localStorage token storage
- **Calculation BREAD API** — Browse, Read, Edit, Add, Delete calculation records
- **Design Patterns** — Factory, Command, Strategy, Observer, Memento, Facade, Singleton, Plugin
- **288 Tests, 90%+ Coverage** — Unit, CLI, FastAPI integration, and Playwright E2E tests
- **CI/CD** — GitHub Actions → Docker Hub on every push to `main`
- **Containerized** — Docker + Docker Compose (FastAPI + PostgreSQL)

---

## 🛠️ Installation & Setup

```bash
# 1. Clone
git clone https://github.com/sairamcharan9/CALCULATOR_WEB_SYSTEMS.git
cd CALCULATOR_WEB_SYSTEMS

# 2. Virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Dependencies
pip install -r requirements.txt
```

---

## 🌐 FastAPI Web Application

```bash
python main.py          # starts uvicorn on http://127.0.0.1:8000
```

| URL | Description |
|-----|-------------|
| `http://localhost:8000/` | Glassmorphism calculator UI |
| `http://localhost:8000/register` | **New** — User registration page |
| `http://localhost:8000/login` | **New** — User login page (stores JWT) |
| `http://localhost:8000/docs` | Swagger / OpenAPI documentation |
| `http://localhost:8000/redoc` | ReDoc documentation |
| `http://localhost:8000/health` | Health check endpoint |

### Quick API Examples

```bash
# Arithmetic
curl -X POST http://localhost:8000/add \
  -H "Content-Type: application/json" -d '{"a":"10","b":"5"}'

# Register user → returns {id, username, email, created_at}
curl -X POST http://localhost:8000/users/register \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","email":"alice@example.com","password":"SecurePass123!"}'

# Login → returns {access_token, token_type: "bearer"}
curl -X POST http://localhost:8000/users/login \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"SecurePass123!"}'
# → {"access_token": "eyJ...", "token_type": "bearer"}

# Create calculation (BREAD)
curl -X POST http://localhost:8000/calculations/ \
  -H "Content-Type: application/json" \
  -d '{"a":10,"b":5,"type":"ADD","user_id":1}'
```

---

## 💻 CLI REPL

```bash
python main.py --cli
```

```
>>> calc add 10 5
Result: 15.00

>>> calc root 144 2
Result: 12.00

>>> memory store A 999
Stored 999 into memory 'A'.

>>> memory recall A
Recalled A: 999

>>> history
=== Calculation History ===
1. 10 + 5 = 15.00
2. 144 √ 2 = 12.00

>>> undo
Undo successful. 1 calculation(s) remaining.

>>> exit
Goodbye!
```

---

## 🔐 JWT Authentication

### How It Works

1. `POST /users/register` — validates with Pydantic, hashes password with bcrypt, stores in DB. Returns `201` with user data.
2. `POST /users/login` — verifies bcrypt hash; on success, signs an HS256 JWT (30-min expiry) and returns `{"access_token": "...", "token_type": "bearer"}`.
3. Front-end stores the token in `localStorage` as `auth_token`.

### Front-End Pages

| Page | URL | Client-Side Validation |
|------|-----|------------------------|
| Register | `/register` | email regex, min 8-char password, confirm password match |
| Login | `/login` | non-empty username & password; stores JWT on success |

### User API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/users/register` | Register a new user — hashes password, returns `UserRead` |
| `POST` | `/users/login` | Authenticate — returns `{access_token, token_type}` JWT |
| `GET` | `/users/{id}` | Get user by ID |
| `GET` | `/users/` | List all users |

### Calculation BREAD Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/calculations/` | Browse all (filter by `?user_id=`) |
| `GET` | `/calculations/{id}` | Read single calculation |
| `POST` | `/calculations/` | Add new calculation (result computed server-side) |
| `PUT` | `/calculations/{id}` | Edit operands/type (result recomputed) |
| `DELETE` | `/calculations/{id}` | Delete calculation |

---

## 🧪 Testing

```bash
# Unit tests (no DB required)
pytest tests/unit -v

# CLI integration tests
pytest tests/cli -v

# FastAPI integration tests (requires PostgreSQL or SQLite fallback)
pytest tests/fastapi/integration -v

# E2E Playwright tests — auth + calculator (requires running server on :8000)
python main.py &
playwright install chromium
TEST_URL=http://localhost:8000 pytest tests/fastapi/e2e -v

# Auth E2E tests only
TEST_URL=http://localhost:8000 pytest tests/fastapi/e2e -k "register or login" -v

# Full suite with coverage
pytest tests/unit tests/fastapi/integration tests/cli \
       --cov=app --cov=main --cov-report=term-missing
```

**Current test results: 288 passed across all suites.**

---

## 🐳 Docker

### Single Container

```bash
docker build -t calculator-web .
docker run -p 8000:8000 \
  -e DATABASE_URL=postgresql://user:pass@host:5432/db \
  calculator-web
```

### Full Stack (App + PostgreSQL)

```bash
# Copy and configure environment
cp .env.example .env
# Edit .env: set POSTGRES_PASSWORD

docker compose up -d --build
```

| Service | Port | URL |
|---------|------|-----|
| FastAPI app | 8000 | http://localhost:8000 |
| PostgreSQL | 5432 | — |
| pgAdmin 4 | 5050 | http://localhost:5050 |

### Docker Hub

🐳 **Repository:** [hub.docker.com/r/sb2853/calculator-web-systems](https://hub.docker.com/r/sb2853/calculator-web-systems)

```bash
docker pull sb2853/calculator-web-systems:latest
docker run -p 8000:8000 \
  -e JWT_SECRET=your-secret-here \
  -e DATABASE_URL=postgresql://user:pass@host:5432/db \
  sb2853/calculator-web-systems:latest
```

---

## 🔄 CI/CD Pipeline

`.github/workflows/ci.yml` runs on every push/PR to `main`:

```
push to main
    │
    ├─► test job (ubuntu + postgres:15)
    │       ├─ pytest tests/unit
    │       ├─ pytest tests/cli
    │       ├─ pytest tests/fastapi/integration
    │       ├─ playwright E2E (chromium, headless)
    │       └─ coverage report → Codecov
    │
    └─► deploy job (main branch only)
            └─ docker build → push sb2853/calculator-web-systems:latest
```

**Required GitHub Secrets**: `DOCKERHUB_USERNAME`, `DOCKERHUB_TOKEN`

---

## 🏗️ Architecture & Design Patterns

| Pattern | Class / Function | Module |
|---------|-----------------|--------|
| **Factory** | `CalculatorFactory` | `app/cli/calculator_factory.py` |
| **Command** | `Calculation`, `CommandManager` | `app/cli/calculation.py`, `app/cli/commands.py` |
| **Strategy** | `@command` decorated operations | `app/cli/operations.py` |
| **Observer** | `LoggingObserver`, `AutoSaveObserver` | `app/cli/history.py` |
| **Memento** | `MementoCaretaker` | `app/cli/calculator_memento.py` |
| **Facade** | `Calculator` REPL | `app/cli/calculator_repl.py` |
| **Singleton** | `command_manager` | `app/cli/command_loader.py` |
| **Plugin** | Dynamic `app/cli/plugins/` loader | `app/__init__.py` |

---

## 📁 Project Structure

```
CALCULATOR_WEB_SYSTEMS/
├── app/
│   ├── __init__.py               # Plugin loader (loads app/cli/plugins/ + operations)
│   ├── core/                     # Shared utilities (no framework deps)
│   │   ├── exceptions.py         # Custom exception hierarchy
│   │   └── logger.py             # Centralized logging setup
│   ├── cli/                      # REPL engine & arithmetic logic
│   │   ├── calculation.py        # Calculation model (Command pattern)
│   │   ├── calculator_config.py  # .env configuration
│   │   ├── calculator_factory.py # Assembles Calculator instance
│   │   ├── calculator_memento.py # Undo/Redo (Memento pattern)
│   │   ├── calculator_repl.py    # REPL facade
│   │   ├── command_loader.py     # Singleton CommandManager instance
│   │   ├── commands.py           # Command registry + @command decorator
│   │   ├── history.py            # History + Observer pattern
│   │   ├── input_validators.py   # Input validation utilities
│   │   ├── interfaces.py         # Abstract base classes
│   │   ├── operations.py         # 10 arithmetic operations (Strategy)
│   │   └── plugins/              # Dynamically loaded plugins
│   │       ├── greet.py
│   │       ├── help.py
│   │       ├── history_commands.py
│   │       └── memory_commands.py
│   └── api/                      # FastAPI / SQLAlchemy layer
│       ├── calculation_routes.py # Calculation BREAD endpoints
│       ├── database.py           # SQLAlchemy engine & session
│       ├── models.py             # User & Calculation ORM models
│       ├── schemas.py            # Pydantic v2 schemas (incl. Token)
│       ├── security.py           # bcrypt + JWT (python-jose)
│       └── user_routes.py        # Register (201) / Login (JWT) endpoints
├── templates/
│   ├── index.html                # Glassmorphism calculator SPA
│   ├── register.html             # Registration page (client-side validation)
│   └── login.html                # Login page (JWT → localStorage)
├── tests/
│   ├── unit/                     # Unit tests (logic, schemas, security, models)
│   ├── cli/                      # CLI REPL integration tests
│   └── fastapi/
│       ├── integration/          # API integration tests (DB required)
│       └── e2e/                  # Playwright browser tests
├── main.py                       # FastAPI app entrypoint + CLI launcher
├── Dockerfile                    # Production container image
├── docker-compose.yml            # App + PostgreSQL orchestration
├── .github/workflows/ci.yml      # GitHub Actions CI/CD
├── .env.example                  # Environment variable template
├── requirements.txt              # Python dependencies
└── pytest.ini                    # Test configuration
```

---

## 📝 Reflection

### Module 13 — JWT Authentication

**What was implemented:**
This module added JWT-based authentication to the existing FastAPI calculator. The `/users/login` endpoint now generates an HS256-signed JWT using `python-jose`, and the front-end login page stores it in `localStorage`. Two styled HTML pages (`register.html` and `login.html`) were built matching the existing dark glassmorphism aesthetic, each with full client-side validation. Four Playwright E2E tests were added covering both positive (valid registration, valid login + token check) and negative (short password caught client-side, wrong password caught server-side with 401 UI feedback) scenarios.

**Key challenges:**
- Integrating `python-jose` alongside `passlib[bcrypt]` required careful dependency pinning (`bcrypt==4.0.1`) to avoid version conflicts.
- The Playwright negative test for wrong passwords had to explicitly clear `localStorage` state between test runs to avoid cross-test token pollution.
- The CI environment needed `JWT_SECRET` wired as an env var so the server could sign tokens during the automated test run.

**What was learned:**
JWT stateless authentication is straightforward to add to a FastAPI app but requires deliberate thought around token expiry, secret management, and the difference between authentication (who you are) vs. authorization (what you can do). The `WWW-Authenticate: Bearer` header on 401 responses aligns the API with RFC 6750.

---

### Module 14 — Calculation BREAD Endpoints

**What was implemented:**
This module introduced the BREAD (Browse, Read, Edit, Add, Delete) operations for calculations. The front-end application now integrates these endpoints, allowing users to browse their calculation history in a data table, add new calculations, view details, edit existing operations or operands, and delete records. The API was backed by SQLAlchemy models interacting with PostgreSQL. Playwright tests were added to ensure the reliability of these functionalities in the browser.

**Key challenges:**
- Integrating SQLAlchemy models with FastAPI endpoints required careful handling of session lifecycles.
- Ensuring calculations are scoped correctly to the logged-in user so users only see and interact with their own history.
- Handling division by zero logic within the factory and making sure exceptions bubble up to the user gracefully.
- Writing Playwright tests that required managing localStorage JWT tokens to authenticate before performing BREAD operations in tests.

**What was learned:**
Building a full-stack feature involving the API, Database, and Frontend solidifies the understanding of data flow across the stack. Utilizing the Factory pattern for calculation models makes it easy to add or modify arithmetic operations. Tying user authentication into BREAD operations demonstrates the importance of security and data privacy in web systems.

---

*Production-ready FastAPI calculator demonstrating enterprise Python architecture — SOLID principles, 10 design patterns, JWT authentication, 288+ automated tests, full CI/CD pipeline.*
