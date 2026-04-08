# Advanced Dual-Mode Calculator (FastAPI & CLI)

This project is a professional-grade, dual-mode Calculator application built in Python. It features a complete **Command-Line Interface (REPL)** for terminal enthusiasts and a rich **FastAPI Web Server** with a stunning Glassmorphism frontend UI for browser interactions.

Both interfaces share perfectly synced core mathematical logic, decoupled operations using the Command Pattern, a unified calculation history via Pandas, and robust Undo/Redo/Memory implementations.

## 🚀 Features

- **Dual Interaction Modes**:
  - `FastAPI Web Application`: A gorgeous Single Page Application (SPA) providing a physical-calculator aesthetic using vanilla HTML/CSS/JS.
  - `CLI REPL`: An interactive console application with robust error handling and command interpretation.
- **Advanced Architecture**: Designed entirely using SOLID principles (Factory, Command, Facade, Memento, Observer, Strategy, Singleton patterns).
- **Extensive Operations**: 10 built-in mathematical operations (Add, Subtract, Multiply, Divide, Int Divide, Power, Root, Modulus, Percent, Absolute Difference).
- **Persistent Memory & History**: Calculations are saved via a Pandas DataFrame (`data/history.csv`); memory states can be stored, recalled, and cleared reliably.
- **Enterprise Testing**: 197 tests with 92% coverage via Pytest — Unit Tests, CLI integration tests, FastAPI API tests, and End-to-End (E2E) browser tests using Playwright.
- **Continuous Integration**: GitHub Actions CI directly enforces testing and coverage rules against all modes.
- **Containerized**: Full Docker Compose setup with FastAPI app, PostgreSQL, and pgAdmin for database management.

---

## 🛠️ Installation & Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/sairamcharan9/CALCULATOR_WEB_SYSTEMS.git
   cd CALCULATOR_WEB_SYSTEMS
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```

3. **Install dependencies** (including Pytest and Playwright for tests):
   ```bash
   pip install -r requirements.txt
   playwright install  # Required for running E2E UI Tests
   ```

---

## 🌐 Mode 1: FastAPI Web Application

To use the calculator via a beautiful, browser-based graphical interface, simply run `main.py` without any arguments.

![FastAPI Web Application](screenshots/image%20copy%205.png)

### Start the Server
```bash
python main.py
```

### Accessing the API & GUI
- **Application GUI**: Open [http://127.0.0.1:8000/](http://127.0.0.1:8000/) in your favorite browser.
- **Swagger Documentation**: View the auto-generated API specifications at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

### API Endpoint Examples
You can interface directly with the FastAPI backend without using the GUI:
```bash
# Add two numbers
curl -X POST http://127.0.0.1:8000/add -H "Content-Type: application/json" -d '{"a":"10","b":"5"}'

# View History
curl http://127.0.0.1:8000/history
```

---

## 💻 Mode 2: The Interactive CLI (REPL)

For developers who want a fast, interactive terminal calculator, you can launch the CLI mode.

![CLI Interface](screenshots/image%20copy.png)

### Start the CLI
```bash
python main.py --cli
```

### Example Usage:
```text
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

>>> exit
Goodbye!
```

---

## 🧪 Testing and Coverage

This project maintains **92% code coverage** across 197 automated tests.

### Running Tests Locally
```bash
# Run exclusively the shared core / unit tests (164 tests)
pytest tests/unit -v

# Run exclusively CLI interface tests (16 tests)
pytest tests/cli -v

# Run strictly the FastAPI Integration tests (17 tests)
pytest tests/fastapi/integration -v

# Run the complete unified test suite with Coverage Report
pytest --cov=app --cov=main --cov-fail-under=90 tests/
```

> **Note**: The E2E tests (`tests/fastapi/e2e/`) require the FastAPI server to be running in a background terminal (`python main.py`) or they will get "Connection Refused". They use Playwright to simulate button clicks natively.

---

## 🐳 Docker Deployment

### Single Container (Calculator Only)

To launch the Web Application independently via Docker:

```bash
docker build -t fast-calculator .
docker run -p 8000:8000 fast-calculator
```

### Full Stack with Docker Compose (Calculator + PostgreSQL + pgAdmin)

To launch the complete multi-service environment:

```bash
docker-compose up -d --build
```

This starts three services:

| Service | Container | Port | Purpose |
|---|---|---|---|
| `app` | `fastapi_calculator` | `8000` | FastAPI Web Calculator |
| `db` | `postgres_db` | `5432` | PostgreSQL 15 Database |
| `pgadmin` | `pgadmin_gui` | `5050` | pgAdmin 4 GUI |

- **Calculator UI**: [http://localhost:8000](http://localhost:8000)
- **pgAdmin**: [http://localhost:5050](http://localhost:5050) (login: `admin@admin.com` / `admin`)

### Running Tests inside Docker

To execute the full test suite inside the container:

```bash
docker run --rm --entrypoint /bin/bash fast-calculator ./run_tests_internal.sh
```

This script automatically handles the background server startup required for the browser-based E2E tests.

---

## 🗄️ SQL Database Assignment

The project includes a containerized PostgreSQL database integration exercise:

- **`setup_db.sql`**: Complete SQL script covering table creation, CRUD operations, and JOINs
- **`sql_assignment_documentation.md`**: Step-by-step documentation with screenshots
- **`reflection.md`**: Reflection on Docker containerization and SQL integration

### SQL Operations Covered
1. **Table Creation** — `users` and `calculations` tables with foreign key relationships
2. **Data Insertion** — Sample users and calculation records
3. **Data Retrieval & JOINs** — Querying related data across tables
4. **Record Update** — Modifying existing records
5. **Record Deletion** — Removing records with referential integrity

---

## 🏗️ Architecture & Design Patterns

| Pattern | Implementation | File |
|---|---|---|
| **Factory** | `CalculatorFactory` assembles dependencies | `app/calculator_factory.py` |
| **Command** | `Calculation` extends `Command` ABC | `app/calculation.py` |
| **Strategy** | Operations as pluggable `@command` functions | `app/operations.py` |
| **Observer** | `LoggingObserver`, `AutoSaveObserver` | `app/history.py` |
| **Memento** | `MementoCaretaker` for undo/redo | `app/calculator_memento.py` |
| **Facade** | `Calculator` REPL orchestrates subsystems | `app/calculator_repl.py` |
| **Singleton** | `CommandManager` singleton registry | `app/commands.py` |
| **Plugin** | Dynamic plugin loading via `@command` decorator | `app/__init__.py` |

---

## 📁 Project Structure

```
CALCULATOR_WEB_SYSTEMS/
├── app/                          # Core application package
│   ├── __init__.py               # Plugin loader
│   ├── calculation.py            # Calculation model (Command pattern)
│   ├── calculator_config.py      # Environment configuration
│   ├── calculator_factory.py     # Factory for assembling Calculator
│   ├── calculator_memento.py     # Undo/Redo (Memento pattern)
│   ├── calculator_repl.py        # REPL interface (Facade)
│   ├── command_loader.py         # Singleton CommandManager instance
│   ├── commands.py               # Command registration system
│   ├── exceptions.py             # Custom exception hierarchy
│   ├── history.py                # History + Observer pattern
│   ├── input_validators.py       # Input validation (LBYL)
│   ├── interfaces.py             # Abstract base classes
│   ├── logger.py                 # Centralized logging
│   ├── operations.py             # 10 arithmetic operations (Strategy)
│   └── plugins/                  # Dynamically loaded command plugins
│       ├── greet.py
│       ├── help.py
│       ├── history_commands.py
│       └── memory_commands.py
├── templates/
│   └── index.html                # Glassmorphism SPA frontend
├── tests/
│   ├── unit/                     # 164 unit tests
│   ├── cli/                      # 16 CLI integration tests
│   └── fastapi/
│       ├── integration/          # 17 API tests
│       └── e2e/                  # 4 Playwright browser tests
├── screenshots/                  # UI and SQL assignment screenshots
├── main.py                       # FastAPI app + CLI entry point
├── Dockerfile                    # Container image definition
├── docker-compose.yml            # Multi-service orchestration
├── setup_db.sql                  # SQL assignment script
├── requirements.txt              # Python dependencies
├── pytest.ini                    # Test configuration
├── verification.md               # Full project verification report
├── reflection.md                 # Assignment reflection
└── sql_assignment_documentation.md
```

---

*Created as a Web Systems assignment submission demonstrating Enterprise Python architectural principles.*
