# manifold_web/main.py
from fastapi import FastAPI
from manifold_core.sync_engine import sync_all

app = FastAPI()

@app.get("/api/sync")
def trigger_sync():
    sync_all()
    return {"status": "ok"}
