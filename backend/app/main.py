from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import engine, Base
from app.core.middleware import SecurityAndTenantMiddleware
from app.api.v1 import auth, kyc_sessions, admin, sandbox

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB Tables on Startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Enterprise Digital KYC & Identity Verification Platform for Banking, Fintechs, and Regulated Financial Institutions.",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom Enterprise Security & Tenant Middleware
app.add_middleware(SecurityAndTenantMiddleware)

# Include Routers
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(kyc_sessions.router, prefix=settings.API_V1_STR)
app.include_router(admin.router, prefix=settings.API_V1_STR)
app.include_router(sandbox.router, prefix=settings.API_V1_STR)

@app.get("/health")
@app.get(f"{settings.API_V1_STR}/health")
async def health_check():
    return {
        "status": "UP",
        "service": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
        "provider_mode": settings.KYC_PROVIDER_MODE,
        "storage_provider": settings.STORAGE_PROVIDER
    }

