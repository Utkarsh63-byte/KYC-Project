import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Digital KYC & Identity Verification Platform"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "bank-enterprise-kyc-super-secret-jwt-encryption-key-change-in-prod"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    DATABASE_URL: str = "sqlite+aiosqlite:///./kyc_platform.db"
    
    STORAGE_PROVIDER: str = "local"  # local or s3
    LOCAL_STORAGE_PATH: str = "./data/storage"
    AWS_S3_BUCKET_NAME: str = "enterprise-kyc-documents-secure"
    AWS_REGION: str = "ap-south-1"
    
    KYC_PROVIDER_MODE: str = "mock"  # mock or production
    AWS_ACCESS_KEY_ID: str = "mock_key"
    AWS_SECRET_ACCESS_KEY: str = "mock_secret"
    
    # Risk & Quality Thresholds
    RISK_THRESHOLD_AUTO_APPROVE: float = 20.0
    RISK_THRESHOLD_MANUAL_REVIEW: float = 75.0
    QUALITY_MIN_SCORE: float = 70.0
    OCR_MIN_CONFIDENCE: float = 80.0
    LIVENESS_MIN_CONFIDENCE: float = 85.0
    FACE_MATCH_MIN_CONFIDENCE: float = 80.0
    
    ENFORCE_TENANT_ISOLATION: bool = True
    MAX_UPLOAD_SIZE_MB: int = 10
    ALLOWED_IMAGE_TYPES: List[str] = ["image/jpeg", "image/png", "image/webp", "application/pdf"]

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
