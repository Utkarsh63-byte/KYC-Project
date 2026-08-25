from abc import ABC, abstractmethod
from typing import Dict, Any, List, Tuple, Optional

class BaseOCRProvider(ABC):
    @abstractmethod
    async def extract_text_and_fields(self, image_bytes: bytes, doc_type: str) -> Tuple[List[Dict[str, Any]], float]:
        """Returns extracted fields list and average confidence"""
        pass

class BaseLivenessProvider(ABC):
    @abstractmethod
    async def verify_liveness(self, selfie_bytes: bytes, challenge_data: Optional[Dict[str, Any]] = None) -> Tuple[float, str, Dict[str, Any]]:
        """Returns liveness_score (0-100), liveness_status ('PASSED'/'FAILED'), and raw metadata"""
        pass


class BaseFaceMatchProvider(ABC):
    @abstractmethod
    async def compare_faces(self, document_photo_bytes: bytes, selfie_bytes: bytes) -> Tuple[float, str, Dict[str, Any]]:
        """Returns match_confidence (0-100), match_status ('MATCH'/'NO_MATCH'), and raw metadata"""
        pass

class BaseStorageProvider(ABC):
    @abstractmethod
    async def save_file(self, tenant_id: str, session_id: str, file_bytes: bytes, file_name: str, mime_type: str) -> str:
        """Saves file securely and returns resource path/URI"""
        pass

    @abstractmethod
    async def get_presigned_url(self, resource_path: str, expires_in_seconds: int = 900) -> str:
        """Returns secure short-lived URL for viewing document evidence"""
        pass
