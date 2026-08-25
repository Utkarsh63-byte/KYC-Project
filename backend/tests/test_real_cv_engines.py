import cv2
import numpy as np
import pytest
from app.processing.real_ocr_engine import RealOCREngine
from app.processing.face_engine import FaceEngine

def test_real_ocr_pan_parsing():
    # Synthetic PAN image
    img = np.zeros((400, 600, 3), dtype=np.uint8)
    cv2.putText(img, 'INCOME TAX DEPARTMENT', (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.putText(img, 'RAHUL SHARMA', (30, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.putText(img, 'ABCPS1234K', (30, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.putText(img, '15/08/1992', (30, 200), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    _, enc = cv2.imencode('.jpg', img)
    fields, avg_conf = RealOCREngine.parse_document(enc.tobytes(), "PAN")
    
    assert len(fields) >= 3
    assert avg_conf >= 80.0
    field_names = [f["fieldName"] for f in fields]
    assert "docNumber" in field_names
    assert "dob" in field_names

def test_real_face_matching_similar_faces():
    # Generate 2 synthetic face images
    face1 = np.ones((200, 200, 3), dtype=np.uint8) * 180
    cv2.circle(face1, (100, 100), 50, (120, 100, 80), -1)
    
    face2 = np.ones((200, 200, 3), dtype=np.uint8) * 180
    cv2.circle(face2, (100, 100), 52, (120, 100, 80), -1)

    _, enc1 = cv2.imencode('.jpg', face1)
    _, enc2 = cv2.imencode('.jpg', face2)

    score, status, meta = FaceEngine.compare_faces_cv(enc1.tobytes(), enc2.tobytes())
    
    assert score >= 70.0
    assert status == "MATCH"
    assert "histogramCorrelationScore" in meta
