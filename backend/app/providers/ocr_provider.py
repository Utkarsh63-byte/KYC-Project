from typing import Dict, Any, List, Tuple
from app.providers.base import BaseOCRProvider
from app.core.config import settings
from app.processing.real_ocr_engine import RealOCREngine

class MockOCRProvider(BaseOCRProvider):
    """
    Intelligent OCR Provider using computer vision and layout pattern parsing
    on uploaded real identity documents.
    """
    async def extract_text_and_fields(self, image_bytes: bytes, doc_type: str) -> Tuple[List[Dict[str, Any]], float]:
        fields, avg_conf = RealOCREngine.parse_document(image_bytes, doc_type)
        return fields, avg_conf





class RealAWSTextractOCRProvider(BaseOCRProvider):
    """
    AWS Textract OCR Provider integration for production deployments.
    """
    async def extract_text_and_fields(self, image_bytes: bytes, doc_type: str) -> Tuple[List[Dict[str, Any]], float]:
        import boto3
        client = boto3.client(
            'textract',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        response = client.analyze_id(DocumentPages=[{'Bytes': image_bytes}])
        
        fields = []
        confidences = []
        identity_docs = response.get('IdentityDocuments', [])
        if isinstance(identity_docs, list):
            for doc in identity_docs:
                if isinstance(doc, dict):
                    doc_fields = doc.get('IdentityDocumentFields', [])
                    if isinstance(doc_fields, list):
                        for field in doc_fields:
                            if isinstance(field, dict):
                                type_info = field.get('Type', {})
                                type_name = type_info.get('Text', 'UNKNOWN') if isinstance(type_info, dict) else 'UNKNOWN'
                                val_info = field.get('ValueDetection', {})
                                val_name = val_info.get('Text', '') if isinstance(val_info, dict) else ''
                                confidence = val_info.get('Confidence', 80.0) if isinstance(val_info, dict) else 80.0
                                
                                fields.append({
                                    "fieldName": str(type_name).lower(),
                                    "value": str(val_name),
                                    "confidence": round(float(confidence), 1),
                                    "source": "aws_textract",
                                    "validationStatus": "VALID" if float(confidence) > 75.0 else "SUSPECTED"
                                })
                                confidences.append(float(confidence))

                
        avg_conf = sum(confidences) / max(len(confidences), 1) if confidences else 85.0
        return fields, avg_conf

def get_ocr_provider() -> BaseOCRProvider:
    if settings.KYC_PROVIDER_MODE == "production":
        return RealAWSTextractOCRProvider()
    return MockOCRProvider()
