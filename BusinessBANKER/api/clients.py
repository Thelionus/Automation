"""
Client Base File endpoints.
"""
import uuid
from datetime import date
from fastapi import APIRouter, HTTPException, Depends

from models.client import ClientProfile, ClientCreate
from api.dependencies import get_store

router = APIRouter(prefix="/clients", tags=["Clients"])


@router.post("/", response_model=ClientProfile, status_code=201)
def create_client(payload: ClientCreate, store=Depends(get_store)):
    if payload.client_number in store["clients"]:
        raise HTTPException(status_code=409, detail="Client number already exists.")
    client = ClientProfile(
        **payload.model_dump(),
        created_by="system",
        created_at=date.today(),
    )
    store["clients"][client.client_number] = client
    return client


@router.get("/", response_model=list[ClientProfile])
def list_clients(store=Depends(get_store)):
    return list(store["clients"].values())


@router.get("/{client_number}", response_model=ClientProfile)
def get_client(client_number: str, store=Depends(get_store)):
    client = store["clients"].get(client_number)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found.")
    return client


@router.delete("/{client_number}", status_code=204)
def deactivate_client(client_number: str, store=Depends(get_store)):
    client = store["clients"].get(client_number)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found.")
    client.is_active = False
