# Advanced Dual-Mode Calculator (FastAPI & CLI)

This project is a professional-grade, dual-mode Calculator application built in Python. It features a complete **Command-Line Interface (REPL)** for terminal enthusiasts and a rich **FastAPI Web Server** with a stunning Glassmorphism frontend UI for browser interactions. 

Both interfaces share perfectly synced core mathematical logic, decoupled operations using the Command Pattern, a unified calculation history via Pandas, and robust Undo/Redo/Memory implementations.

## 🚀 Features

- **Dual Interaction Modes**:
  - `FastAPI Web Application`: A gorgeous Single Page Application (SPA) providing a physical-calculator aesthetic using vanilla HTML/CSS/JS. 
  - `CLI REPL`: An interactive console application with robust error handling and command interpretation.
- **Advanced Architecture**: Designed entirely using SOLID principles (Factory, Command, Facade, Memento, Observer patterns).
- **Extensive Operations**: 10 built-in mathematical operations (Add, Subtract, Multiply, Divide, Int Divide, Power, Root, Modulus, Percent, Absolute Difference).
- **Persistent Memory & History**: Calculations are saved via a Pandas DataFrame (`data/history.csv`); memory states can be stored, recalled, and cleared reliably.
- **Enterprise Testing**: Fully graded with 95%+ Coverage via Pytest. Features deeply parameterized Unit Tests for shared logic, CLI integration testing, and explicit End-to-End (E2E) Browser tests using Playwright.
- **Continuous Integration**: GitHub Actions CI directly enforces testing and coverage rules against all modes.
- **Containerized**: `Dockerfile` is provided for instant, isolated deployment.

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

This project strictly maintains over 90% code coverage. 

### Running Tests Locally
```bash
# Run exclusively the shared core / unit tests
pytest tests/unit -v

# Run exclusively CLI interface tests
pytest tests/cli -v

# Run strictly the FastAPI Integration & E2E framework
pytest tests/fastapi -v

# Run the complete unified test suite with Coverage Report
pytest --cov=app --cov=main --cov-fail-under=90 tests/
```

> **Note**: The E2E tests require the FastAPI server to be running in a background terminal `python main.py` or they will "Connection Refused". They use Playwright to simulate button clicks natively.

---

## 🐳 Docker Deployment

To launch the Web Application independently via Docker ensuring pristine cross-compatibility:

```bash
docker build -t fast-calculator .
docker run -p 8000:8000 fast-calculator
```
Then navigate horizontally to `http://localhost:8000`.

---
*Created as a Midterm Submission demonstrating Enterprise Python architectural principles.*
