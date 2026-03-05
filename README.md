<div align="center">
  <h1>🧮 Advanced Calculator Application</h1>
  <p><i>A beautifully styled, fully-featured command-line calculator built with Python.</i></p>

  ![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
  ![Coverage](https://img.shields.io/badge/Coverage-97%25-brightgreen.svg)
  ![Design Patterns](https://img.shields.io/badge/Design_Patterns-Facade_|_Observer_|_Strategy-purple.svg)
</div>

<br />

## 📸 Showcase & REPL Demo

Experience our intuitive, color-coded REPL interface in action. The application features robust syntax highlighting for commands, success messages, operational status, and errors natively leveraging `colorama` for a seamless user experience!

<div align="center">
  <img src="screenshots/image%20copy.png" width="48%" />
  <img src="screenshots/image%20copy%203.png" width="48%" />
</div>

<div align="center" style="margin-top: 10px;">
  <img src="screenshots/image%20copy%202.png" width="98%" />
</div>

<div align="center" style="margin-top: 10px;">
  <img src="screenshots/image%20copy%204.png" width="98%" />
</div>

---

## 📖 Project Description

This project is a sophisticated command-line calculator application built with Python, showcasing the integration of advanced software design patterns (Facade, Observer, Strategy, and Memento) to create a modular, extensible, and maintainable system. It moves beyond basic arithmetic to offer a rich feature set including persistent history, undo/redo functionality, and comprehensive logging, all configurable via environment variables.

The core of the application is an interactive Read-Eval-Print Loop (REPL), providing a seamless user experience for performing calculations with full color-coded feedback!

### 🌟 Key Features

- **🎨 Color-Coded Interface**: Intuitive feedback with Green results, Red errors, Blue history, and Magenta branding.
- **⚡ Advanced Arithmetic**: Supports `add`, `subtract`, `multiply`, `divide`, `power`, `root`, `modulus`, `int_divide`, `percent`, and `abs_diff`.
- **🔄 Undo/Redo System**: Full state management allowing you to revert or repeat any calculation actions.
- **💾 Persistent History**: Seamlessly manages calculation history using `pandas`, with CSV save/load support.
- **🛠️ Design Patterns Focused**: Implements clean architecture using Facade, Strategy, Observer, and Memento patterns.
- **🛡️ Robust Validation**: Comprehensive input validation and custom exception handling for all operations.
- **📊 Detailed Logging**: Centralized logging system capturing all events and errors for auditability.

## 🚀 Installation & Setup

### 1. Clone & Environment
```bash
git clone https://github.com/example/calculator-app.git # NOTE: Replace with your actual repository URL
cd calculator-app
python -m venv venv
# To activate the virtual environment:
# Windows: .\venv\Scripts\activate
# macOS/Linux: source ./venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Usage
```bash
python main.py
```

## ⚙️ Configuration

Customize the application via the `.env` file:

```env
CALCULATOR_HISTORY_DIR=data
CALCULATOR_AUTO_SAVE=true
CALCULATOR_PRECISION=2
CALCULATOR_MAX_INPUT_VALUE=1e12
```

---

## 🧪 Testing and Quality

We maintain high code quality standards through comprehensive testing and CI/CD integration.

### Running Tests
To execute the test suite and check coverage:
```bash
pytest --cov=app --cov-report=term-missing --cov-fail-under=90
```

### GitHub Actions (CI)
Our automated workflow handles:
- ✅ Dependency installation
- ✅ Code linting and standards
- ✅ Cross-platform test execution
- ✅ Coverage threshold enforcement

---

---

<div align="center">
  <p>Developed with ❤️ for Advanced Software Development</p>
</div>

