"""
Advanced Web Calculator — FastAPI Application
==============================================

Entry point for the web application. Registers all routers, creates
database tables on startup, and exposes a health-check endpoint.
"""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

# ── Canonical sub-package imports ──────────────────────────────────────────
from app.cli.calculator_factory import CalculatorFactory
from app.api.database import engine, Base
from app.api.user_routes import router as user_router
from app.api.calculation_routes import router as calc_router
from app.api.macro_routes import router as macro_router

# ── Logging ────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


# ── App Lifespan ──────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create database tables on startup, log on shutdown."""
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created / verified successfully.")
    yield
    logger.info("Application shutting down.")


# ── FastAPI Instance ──────────────────────────────────────────────────────

app = FastAPI(
    title="Advanced Web Calculator",
    description=(
        "A full-featured calculator API with persistent history, "
        "user authentication, and arithmetic BREAD operations."
    ),
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ──────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Security Headers ──────────────────────────────────────────────────────

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


# ── Router Registration ───────────────────────────────────────────────────

app.include_router(user_router)
app.include_router(calc_router)
app.include_router(macro_router)

# ── Templates & Calculator Core ───────────────────────────────────────────

templates_dir = os.path.join(os.path.dirname(__file__), "templates")
templates = Jinja2Templates(directory=templates_dir)

calculator = CalculatorFactory.create_calculator()


# ── Shared Pydantic Models ────────────────────────────────────────────────

class Numbers(BaseModel):
    a: str
    b: str = "0"


class SingleInput(BaseModel):
    value: str = ""


# ── Health Check ──────────────────────────────────────────────────────────

@app.get("/health", tags=["system"], summary="Health check")
def health_check():
    """Returns 200 OK when the service is running."""
    return {"status": "ok", "version": app.version}


# ── Frontend ──────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def read_item(request: Request):
    return templates.TemplateResponse(
        request=request, name="index.html", context={"request": request}
    )


@app.get("/register", response_class=HTMLResponse, include_in_schema=False,
         summary="Registration page")
async def register_page(request: Request):
    """Serve the user registration front-end page."""
    return templates.TemplateResponse(
        request=request, name="register.html", context={"request": request}
    )


@app.get("/login", response_class=HTMLResponse, include_in_schema=False,
         summary="Login page")
async def login_page(request: Request):
    """Serve the user login front-end page."""
    return templates.TemplateResponse(
        request=request, name="login.html", context={"request": request}
    )



# ── Arithmetic API ────────────────────────────────────────────────────────

def execute_math(op_name: str, a: str, b: str):
    logger.info("API %s %s %s", op_name, a, b)
    res = calculator.process_input(f"calc {op_name} {a} {b}")
    if "Error" in res:
        clean_msg = res.replace("Error: ", "", 1) if res.startswith("Error: ") else res
        return {"error": clean_msg}
    if "=" in res:
        return {"result": res.split("=")[-1].strip()}
    return {"result": res}


@app.post("/add", tags=["arithmetic"])
def api_add(numbers: Numbers):
    return execute_math("add", numbers.a, numbers.b)


@app.post("/subtract", tags=["arithmetic"])
def api_subtract(numbers: Numbers):
    return execute_math("subtract", numbers.a, numbers.b)


@app.post("/multiply", tags=["arithmetic"])
def api_multiply(numbers: Numbers):
    return execute_math("multiply", numbers.a, numbers.b)


@app.post("/divide", tags=["arithmetic"])
def api_divide(numbers: Numbers):
    return execute_math("divide", numbers.a, numbers.b)


@app.post("/power", tags=["arithmetic"])
def api_power(numbers: Numbers):
    return execute_math("power", numbers.a, numbers.b)


@app.post("/root", tags=["arithmetic"])
def api_root(numbers: Numbers):
    return execute_math("root", numbers.a, numbers.b)


@app.post("/modulus", tags=["arithmetic"])
def api_modulus(numbers: Numbers):
    return execute_math("modulus", numbers.a, numbers.b)


@app.post("/int_divide", tags=["arithmetic"])
def api_int_divide(numbers: Numbers):
    return execute_math("int_divide", numbers.a, numbers.b)


@app.post("/percent", tags=["arithmetic"])
def api_percent(numbers: Numbers):
    return execute_math("percent", numbers.a, numbers.b)


@app.post("/abs_diff", tags=["arithmetic"])
def api_abs_diff(numbers: Numbers):
    return execute_math("abs_diff", numbers.a, numbers.b)


# ── Memory & History API ──────────────────────────────────────────────────

@app.post("/memory/store", tags=["memory"])
def api_memory_store(inp: SingleInput):
    val = inp.value if inp.value else "0"
    logger.info("API Memory Store: value=%s", val)
    res = calculator.process_input(f"memory store mem {val}")
    return {"result": res}


@app.get("/memory/recall", tags=["memory"])
def api_mem_recall():
    res = calculator.process_input("memory recall mem")
    if "not found" in res.lower() or "Error" in res:
        return {"error": res}
    if ":" in res:
        return {"result": res.split(":")[-1].strip()}
    return {"result": res}


@app.post("/memory/clear", tags=["memory"])
def api_memory_clear():
    res = calculator.process_input("memory clear")
    return {"result": res}


@app.get("/history", tags=["history"])
def api_history():
    res = calculator.process_input("history")
    return {"result": res}


@app.post("/history/clear", tags=["history"])
def api_history_clear():
    res = calculator.process_input("clear")
    return {"result": res}


@app.post("/undo", tags=["history"])
def api_undo():
    res = calculator.process_input("undo")
    return {"result": res}


@app.post("/redo", tags=["history"])
def api_redo():
    res = calculator.process_input("redo")
    return {"result": res}


# ── Entrypoint ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    import uvicorn

    if "--cli" in sys.argv:
        calculator.run()
    else:
        uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
