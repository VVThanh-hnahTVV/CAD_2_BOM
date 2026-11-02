from fastapi import APIRouter

api_router = APIRouter()

# Gắn router của từng nhóm route ở đây, ví dụ:
# from backend.api.v1 import drawings
# api_router.include_router(drawings.router, prefix="/drawings", tags=["drawings"])
