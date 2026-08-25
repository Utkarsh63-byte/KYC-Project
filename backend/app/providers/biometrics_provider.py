from typing import Dict, Any, Tuple, Optional
from app.providers.base import BaseLivenessProvider, BaseFaceMatchProvider
from app.core.config import settings

class MockLivenessProvider(BaseLivenessProvider):
    async def verify_liveness(self, selfie_bytes: bytes, challenge_data: Optional[Dict[str, Any]] = None) -> Tuple[float, str, Dict[str, Any]]:
        # Simulate high quality liveness score
        score = 98.4
        status = "PASSED"
        metadata = {
            "provider": "MockRekognitionLiveness",
            "modelVersion": "3.0",
            "motionCheck": "PASSED",
            "reflectionCheck": "PASSED",
            "depthPulse": "PASSED",
            "spoofSignals": []
        }
        return score, status, metadata

class RealAWSRekognitionLivenessProvider(BaseLivenessProvider):
    async def verify_liveness(self, selfie_bytes: bytes, challenge_data: Optional[Dict[str, Any]] = None) -> Tuple[float, str, Dict[str, Any]]:

        import boto3
        client = boto3.client(
            'rekognition',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        session_id = challenge_data.get("session_id") if challenge_data else "test_session"
        response = client.get_face_liveness_session_results(SessionId=session_id)
        confidence = response.get("Confidence", 0.0)
        status = "PASSED" if confidence >= settings.LIVENESS_MIN_CONFIDENCE else "FAILED"
        metadata = {
            "provider": "AWSRekognitionFaceLiveness",
            "status": response.get("Status"),
            "auditImages": len(response.get("AuditImages", []))
        }
        return float(confidence), status, metadata

from app.processing.face_engine import FaceEngine

class MockFaceMatchProvider(BaseFaceMatchProvider):
    async def compare_faces(self, document_photo_bytes: bytes, selfie_bytes: bytes) -> Tuple[float, str, Dict[str, Any]]:
        return FaceEngine.compare_faces_cv(document_photo_bytes, selfie_bytes)


class RealAWSRekognitionFaceMatchProvider(BaseFaceMatchProvider):
    async def compare_faces(self, document_photo_bytes: bytes, selfie_bytes: bytes) -> Tuple[float, str, Dict[str, Any]]:
        import boto3
        client = boto3.client(
            'rekognition',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        response = client.compare_faces(
            SourceImage={'Bytes': document_photo_bytes},
            TargetImage={'Bytes': selfie_bytes},
            SimilarityThreshold=settings.FACE_MATCH_MIN_CONFIDENCE
        )
        matches = response.get('FaceMatches', [])
        if matches:
            confidence = matches[0].get('Similarity', 0.0)
            status = "MATCH" if confidence >= settings.FACE_MATCH_MIN_CONFIDENCE else "NO_MATCH"
        else:
            confidence = 0.0
            status = "NO_MATCH"

        metadata = {
            "provider": "AWSRekognitionCompareFaces",
            "unmatchedFacesCount": len(response.get('UnmatchedFaces', [])),
            "faceMatchesCount": len(matches)
        }
        return float(confidence), status, metadata

def get_liveness_provider() -> BaseLivenessProvider:
    if settings.KYC_PROVIDER_MODE == "production":
        return RealAWSRekognitionLivenessProvider()
    return MockLivenessProvider()

def get_face_match_provider() -> BaseFaceMatchProvider:
    if settings.KYC_PROVIDER_MODE == "production":
        return RealAWSRekognitionFaceMatchProvider()
    return MockFaceMatchProvider()
