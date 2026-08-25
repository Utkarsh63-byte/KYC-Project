import os
from pathlib import Path
from app.providers.base import BaseStorageProvider
from app.core.config import settings

class LocalStorageProvider(BaseStorageProvider):
    def __init__(self):
        self.base_path = Path(settings.LOCAL_STORAGE_PATH)
        self.base_path.mkdir(parents=True, exist_ok=True)

    async def save_file(self, tenant_id: str, session_id: str, file_bytes: bytes, file_name: str, mime_type: str) -> str:
        folder = self.base_path / tenant_id / session_id
        folder.mkdir(parents=True, exist_ok=True)
        file_path = folder / file_name
        
        with open(file_path, "wb") as f:
            f.write(file_bytes)
            
        return str(file_path)

    async def get_presigned_url(self, resource_path: str, expires_in_seconds: int = 900) -> str:
        # For local dev, return a local file endpoint URL
        filename = os.path.basename(resource_path)
        return f"/api/v1/kyc/files/preview?path={resource_path}&token=local_temp_token"

class S3StorageProvider(BaseStorageProvider):
    async def save_file(self, tenant_id: str, session_id: str, file_bytes: bytes, file_name: str, mime_type: str) -> str:
        import boto3
        s3_key = f"{tenant_id}/{session_id}/{file_name}"
        s3_client = boto3.client('s3', region_name=settings.AWS_REGION)
        s3_client.put_object(
            Bucket=settings.AWS_S3_BUCKET_NAME,
            Key=s3_key,
            Body=file_bytes,
            ContentType=mime_type,
            ServerSideEncryption='aws:kms'
        )
        return f"s3://{settings.AWS_S3_BUCKET_NAME}/{s3_key}"

    async def get_presigned_url(self, resource_path: str, expires_in_seconds: int = 900) -> str:
        import boto3
        s3_client = boto3.client('s3', region_name=settings.AWS_REGION)
        # Parse s3://bucket/key
        parts = resource_path.replace("s3://", "").split("/", 1)
        bucket = parts[0]
        key = parts[1]
        
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket, 'Key': key},
            ExpiresIn=expires_in_seconds
        )
        return url

def get_storage_provider() -> BaseStorageProvider:
    if settings.STORAGE_PROVIDER == "s3":
        return S3StorageProvider()
    return LocalStorageProvider()
