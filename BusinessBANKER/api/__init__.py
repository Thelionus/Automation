from fastapi import APIRouter
from .clients import router as clients_router
from .loan_requests import router as requests_router

api_router = APIRouter()
api_router.include_router(clients_router)
api_router.include_router(requests_router)

__all__ = ["api_router"]
