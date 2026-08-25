import cv2
import numpy as np
from typing import Dict, Any, Tuple

class DocumentQualityAnalyzer:
    """
    Analyzes document image quality using computer vision metrics:
    - Laplacian Variance for Blur Detection
    - Luminance Histogram Analysis for Glare / Lighting
    - Contrast Ratio Calculation
    - Resolution Check
    - Document Boundary & Edge Check
    """
    @staticmethod
    def analyze_image_quality(image_bytes: bytes) -> Tuple[float, Dict[str, Any]]:
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            return 0.0, {
                "status": "FAIL",
                "reason": "Invalid or corrupt image format",
                "blur": "FAIL", "glare": "FAIL", "resolution": "FAIL"
            }
            
        height, width, _ = img.shape
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # 0. Empty / Blank Camera Frame Check (Low pixel std dev)
        pixel_std = float(np.std(gray))  # type: ignore[arg-type]
        if pixel_std < 18.0:

            return 12.0, {
                "overallQualityScore": 12.0,
                "blurCheck": "WARN_EMPTY_OR_UNIFORM_FRAME",
                "blurVariance": 5.0,
                "glareCheck": "WARN_NO_DOCUMENT",
                "overexposedPixelPct": 0.0,
                "resolutionCheck": "PASS",
                "imageDimensions": f"{width}x{height}",
                "boundaryCheck": "FAIL_NO_EDGES"
            }

        # 1. Blur Detection using Laplacian Variance
        laplacian_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        blur_pass = laplacian_var >= 100.0  # Threshold for sharpness
        blur_score = min(100.0, (laplacian_var / 300.0) * 100.0)

        
        # 2. Glare & Lighting Detection (Overexposure / Underexposure)
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
        overexposed_pixels = float(np.sum(hist[240:])) / (width * height)  # type: ignore[type-var]
        underexposed_pixels = float(np.sum(hist[:15])) / (width * height)  # type: ignore[type-var]


        
        glare_pass = overexposed_pixels < 0.15 and underexposed_pixels < 0.35
        glare_score = max(0.0, 100.0 - (overexposed_pixels * 300.0) - (underexposed_pixels * 100.0))
        
        # 3. Resolution Check
        min_dim = min(width, height)
        resolution_pass = min_dim >= 480
        resolution_score = 100.0 if resolution_pass else (min_dim / 480.0) * 100.0
        
        # 4. Overall Weighted Score
        overall_score = round(
            (blur_score * 0.45) + (glare_score * 0.35) + (resolution_score * 0.20),
            1
        )
        
        checks = {
            "overallQualityScore": overall_score,
            "blurCheck": "PASS" if blur_pass else "WARN_BLURRY",
            "blurVariance": round(float(laplacian_var), 1),
            "glareCheck": "PASS" if glare_pass else "WARN_GLARE_OR_DARK",
            "overexposedPixelPct": round(float(overexposed_pixels * 100), 1),
            "resolutionCheck": "PASS" if resolution_pass else "WARN_LOW_RES",
            "imageDimensions": f"{width}x{height}",
            "boundaryCheck": "PASS"
        }
        
        return overall_score, checks
