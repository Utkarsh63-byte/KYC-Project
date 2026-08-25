import numpy as np
import cv2
from app.processing.document_quality import DocumentQualityAnalyzer
from app.processing.tamper_detector import DocumentTamperDetector

def test_document_quality_sharp_image():
    # Create synthetic sharp image
    img = np.zeros((600, 800, 3), dtype=np.uint8)
    cv2.putText(img, "PAN CARD TEST", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 3)
    cv2.line(img, (100, 200), (700, 200), (255, 255, 255), 5)
    
    _, image_bytes = cv2.imencode('.jpg', img)
    score, checks = DocumentQualityAnalyzer.analyze_image_quality(image_bytes.tobytes())
    
    assert score >= 60.0
    assert checks["blurCheck"] == "PASS"
    assert checks["resolutionCheck"] == "PASS"

def test_tamper_detector_clean_image():
    img = np.full((600, 800, 3), 240, dtype=np.uint8)
    cv2.putText(img, "INCOME TAX DEPARTMENT", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 2)
    
    _, image_bytes = cv2.imencode('.jpg', img)
    tamper_score, checks = DocumentTamperDetector.inspect_document_risk(image_bytes.tobytes(), "pan_card.jpg")
    
    assert tamper_score < 40.0
    assert checks["riskLevel"] in ["LOW", "MEDIUM"]

