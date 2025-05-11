"""
Główny punkt wejścia aplikacji FastAPI.
Importuje wszystkie moduły, rejestruje routery, konfiguruje bazę danych.
"""

import uvicorn
#import aioredis
import redis.asyncio as aioredis
from fastapi import FastAPI
from contextlib import asynccontextmanager
from vetclinic_api.routers import users, appointments, animals, medical_records, invoices, weight_logs
from vetclinic_api.core.database import engine, Base

@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    app.state.redis = aioredis.from_url(
        "redis://localhost",
        encoding="utf-8",
        decode_responses=True
    )
    yield
    # shutdown
    await app.state.redis.close()

app = FastAPI(
    title="System Zarządzania Kliniką Weterynaryjną",
    description="Aplikacja wykorzystująca FastAPI, SQLAlchemy oraz defensywne programowanie.",
    version="1.0.0",
    lifespan=lifespan,  # <-- tutaj przekazujemy nasz context manager
)

# Rejestracja routerów
app.include_router(users.router)
app.include_router(appointments.router)
app.include_router(animals.router)
app.include_router(medical_records.router)
app.include_router(invoices.router)
app.include_router(weight_logs.router)

# Tworzenie tabel w bazie danych (jeśli nie istnieją)
Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
