"""
Główny punkt wejścia aplikacji FastAPI.
Importuje wszystkie moduły, rejestruje routery, konfiguruje bazę danych.
"""

from fastapi import FastAPI
import uvicorn
from vetclinic_api.routers import users, appointments, animals, medical_records, invoices, weight_logs, doctors
from vetclinic_api.core.database import engine, Base

app = FastAPI(
    title="System Zarządzania Kliniką Weterynaryjną",
    description="Aplikacja wykorzystująca FastAPI, SQLAlchemy oraz defensywne programowanie.",
    version="1.0.0",
)

# Rejestracja routerów
app.include_router(users.router)
app.include_router(appointments.router)
app.include_router(animals.router)
app.include_router(medical_records.router)
app.include_router(invoices.router)
app.include_router(weight_logs.router)
app.include_router(doctors.router) 

# Tworzenie tabel w bazie danych (jeśli nie istnieją)
Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)