import logging
import os
from decimal import Decimal
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from app.calculator_factory import CalculatorFactory

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Advanced Web Calculator")

templates_dir = os.path.join(os.path.dirname(__file__), "templates")
templates = Jinja2Templates(directory=templates_dir)

# Initialize the rich calculator core (handles history, undo/redo, memory, observers)
calculator = CalculatorFactory.create_calculator()

class Numbers(BaseModel):
    a: str
    b: str = "0"  # Default 0 for unary operations or if left blank

class SingleInput(BaseModel):
    value: str = ""

@app.get("/", response_class=HTMLResponse)
async def read_item(request: Request):
    return templates.TemplateResponse(request=request, name="index.html", context={"request": request})

def execute_math(op_name: str, a: str, b: str):
    logger.info(f"API Executing {op_name} {a} {b}")
    # Process through the CLI repl logic directly to trigger history and observers
    res = calculator.process_input(f"calc {op_name} {a} {b}")
    
    if "Error" in res:
        return {"error": res}
        
    # Extract only the final result for the Web UI (since REPL usually returns "Result: A + B = C")
    if "=" in res:
        final_val = res.split("=")[-1].strip()
        return {"result": final_val}
        
    return {"result": res}

@app.post("/add")
def api_add(numbers: Numbers):
    return execute_math("add", numbers.a, numbers.b)

@app.post("/subtract")
def api_subtract(numbers: Numbers):
    return execute_math("subtract", numbers.a, numbers.b)

@app.post("/multiply")
def api_multiply(numbers: Numbers):
    return execute_math("multiply", numbers.a, numbers.b)

@app.post("/divide")
def api_divide(numbers: Numbers):
    return execute_math("divide", numbers.a, numbers.b)

@app.post("/power")
def api_power(numbers: Numbers):
    return execute_math("power", numbers.a, numbers.b)

@app.post("/root")
def api_root(numbers: Numbers):
    return execute_math("root", numbers.a, numbers.b)

@app.post("/modulus")
def api_modulus(numbers: Numbers):
    return execute_math("modulus", numbers.a, numbers.b)

@app.post("/int_divide")
def api_int_divide(numbers: Numbers):
    return execute_math("int_divide", numbers.a, numbers.b)

@app.post("/percent")
def api_percent(numbers: Numbers):
    return execute_math("percent", numbers.a, numbers.b)

@app.post("/abs_diff")
def api_abs_diff(numbers: Numbers):
    return execute_math("abs_diff", numbers.a, numbers.b)

# --- ADVANCED COMMANDS EXPOSED AS APIs ---

@app.post("/memory/store")
def api_memory_store(inp: SingleInput):
    val = inp.value if inp.value else "0"
    logger.info(f"API Memory Store: value={val}")
    res = calculator.process_input(f"memory store mem {val}")
    return {"result": res}

@app.get("/memory/recall")
def api_mem_recall():
    logger.info("API Executing memory recall")
    res = calculator.process_input("memory recall mem")
    if "not found" in res.lower() or "Error" in res:
        return {"error": res}
    # Extract numerical value format: "Memory 'mem': 999" -> "999"
    if ":" in res:
        final_val = res.split(":")[-1].strip()
        return {"result": final_val}
    return {"result": res}

@app.post("/memory/clear")
def api_memory_clear():
    logger.info("API Memory Clear")
    res = calculator.process_input("memory clear")
    return {"result": res}

@app.get("/history")
def api_history():
    logger.info("API History View")
    res = calculator.process_input("history")
    return {"result": res}

@app.post("/history/clear")
def api_history_clear():
    logger.info("API History Clear")
    res = calculator.process_input("clear")
    return {"result": res}

@app.post("/undo")
def api_undo():
    logger.info("API Undo")
    res = calculator.process_input("undo")
    return {"result": res}

@app.post("/redo")
def api_redo():
    logger.info("API Redo")
    res = calculator.process_input("redo")
    return {"result": res}

if __name__ == "__main__":
    import sys

    if "--cli" in sys.argv:
        # Run as interactive CLI (REPL) calculator
        calculator.run()
    else:
        # Run as web application (default)
        import uvicorn
        uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
