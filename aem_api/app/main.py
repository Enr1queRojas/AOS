from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .db.database import engine
from .db import models
from .api.endpoints import market, agents, devops, dashboard

# Crea las tablas de la base de datos de manera automática
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AEM Microservice (Agentic Economic Market Central Bank)",
    version="1.0.0"
)

# Configuración CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusión de cada router con su ruta base respectiva
app.include_router(market.router, prefix="/api/v1/market", tags=["Market"])
app.include_router(agents.router, prefix="/api/v1/agents", tags=["Agents"])
app.include_router(devops.router, prefix="/api/v1/devops", tags=["DevOps"])
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["Dashboard"])

@app.get("/")
def root():
    return {"message": "Welcome to AEM Microservice API"}
