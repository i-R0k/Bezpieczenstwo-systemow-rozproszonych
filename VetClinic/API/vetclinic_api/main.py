"""
Glowny punkt wejscia aplikacji FastAPI.
Importuje wszystkie moduly, rejestruje routery, konfiguruje baze danych.
"""

from dotenv import load_dotenv
from fastapi import FastAPI

load_dotenv()
import uvicorn

from vetclinic_api.bft import apply_fastapi_compat

apply_fastapi_compat()

from vetclinic_api.admin.network_router import router as admin_network_router
from vetclinic_api.core.database import Base, engine
from vetclinic_api.metrics import instrumentator_middleware, metrics_router
from vetclinic_api.middleware.chaos import ChaosMiddleware
from vetclinic_api.routers import (
    admin,
    animals,
    appointments,
    bft,
    blockchain,
    blockchain_records,
    cluster,
    consultants,
    doctors,
    facilities,
    invoices,
    medical_records,
    payments,
    rpc,
    users,
    weight_logs,
)

app = FastAPI(
    title="Bezpieczenstwo systemow rozproszonych - demonstrator BFT",
    description=(
        "Demonstracyjny system BFT dla bezpieczenstwa systemow rozproszonych. "
        "Warstwa /bft pokazuje Narwhal, HotStuff, SWIM, fault injection, "
        "checkpointing, recovery, crypto/replay protection i observability. "
        "VetClinic pozostaje domena demonstracyjna oraz starsza warstwa aplikacyjna."
    ),
    version="1.0.0",
)

# Rejestracja routerow
app.include_router(metrics_router)
app.include_router(users.router)
app.include_router(doctors.router)
app.include_router(consultants.router)
app.include_router(facilities.router)
app.include_router(appointments.router)
app.include_router(animals.router)
app.include_router(medical_records.router)
app.include_router(invoices.router)
app.include_router(weight_logs.router)
app.include_router(blockchain.router)
app.include_router(blockchain_records.router)
app.include_router(payments.router)
app.include_router(rpc.router)
app.include_router(cluster.router)
app.include_router(admin.router)
app.include_router(bft.router)
app.include_router(admin_network_router)

app.middleware("http")(instrumentator_middleware)
app.add_middleware(ChaosMiddleware)

# Tworzenie tabel w bazie danych (jesli nie istnieja)
Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    uvicorn.run("vetclinic_api.main:app", host="127.0.0.1", port=8000, reload=True)
