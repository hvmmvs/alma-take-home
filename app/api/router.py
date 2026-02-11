from fastapi import APIRouter

from app.api.endpoints.auth import router as auth_router
from app.api.endpoints.leads import router as leads_router

api_router = APIRouter(prefix="/api")
api_router.include_router(auth_router)
api_router.include_router(leads_router)
