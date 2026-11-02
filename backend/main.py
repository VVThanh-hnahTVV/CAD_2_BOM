from fastapi import FastAPI

from backend.api.v1.router import api_router

app = FastAPI(title="CAD2BOM")
app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
