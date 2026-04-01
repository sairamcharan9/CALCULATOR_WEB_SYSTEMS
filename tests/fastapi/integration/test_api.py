from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_api_add():
    response = client.post("/add", json={"a": "2", "b": "3"})
    assert response.status_code == 200
    assert "5" in response.json()["result"]

def test_api_subtract():
    response = client.post("/subtract", json={"a": "5", "b": "3"})
    assert "2" in response.json()["result"]

def test_api_multiply():
    response = client.post("/multiply", json={"a": "4", "b": "2"})
    assert "8" in response.json()["result"]

def test_api_divide():
    response = client.post("/divide", json={"a": "10", "b": "2"})
    assert "5" in response.json()["result"]

def test_api_divide_by_zero():
    response = client.post("/divide", json={"a": "10", "b": "0"})
    assert "Error" in response.json()["error"]

def test_api_power():
    response = client.post("/power", json={"a": "2", "b": "4"})
    assert "16" in response.json()["result"]

def test_api_root():
    response = client.post("/root", json={"a": "16", "b": "2"})
    assert "4" in response.json()["result"]

def test_api_memory_lifecycle():
    # store a memory
    response = client.post("/memory/store", json={"value": "100"})
    assert "stored" in response.json()["result"].lower()
    
    # recall it
    response = client.get("/memory/recall")
    assert "100" in response.json()["result"]

def test_api_history():
    response = client.get("/history")
    assert response.status_code == 200
    assert "No calculations" in response.json()["result"] or "History" in response.json()["result"]

def test_api_modulus():
    response = client.post("/modulus", json={"a": "10", "b": "3"})
    assert response.status_code == 200
    assert "1" in response.json()["result"]

def test_api_int_divide():
    response = client.post("/int_divide", json={"a": "10", "b": "3"})
    assert response.status_code == 200
    assert "3" in response.json()["result"]

def test_api_percent():
    response = client.post("/percent", json={"a": "50", "b": "200"})
    assert response.status_code == 200
    assert "25" in response.json()["result"]

def test_api_abs_diff():
    response = client.post("/abs_diff", json={"a": "3", "b": "8"})
    assert response.status_code == 200
    assert "5" in response.json()["result"]

def test_api_memory_clear():
    # store first, then clear
    client.post("/memory/store", json={"value": "42"})
    response = client.post("/memory/clear")
    assert response.status_code == 200
    assert "cleared" in response.json()["result"].lower()

def test_api_history_clear():
    response = client.post("/history/clear")
    assert response.status_code == 200

def test_api_undo():
    # perform a calculation first
    client.post("/add", json={"a": "10", "b": "5"})
    response = client.post("/undo")
    assert response.status_code == 200

def test_api_redo():
    response = client.post("/redo")
    assert response.status_code == 200


