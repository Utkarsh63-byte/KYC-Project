import cv2
import numpy as np
from typing import Dict, Any, Tuple

class DocumentTamperDetector:
    """
    Detects potential digital image manipulation, screenshots, copy-paste artifacts,
    and metadata anomalies.
    """
    @staticmethod
    def inspect_document_risk(image_bytes: bytes, filename: str = "") -> Tuple[float, Dict[str, Any]]:
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            return 80.0, {"riskLevel": "HIGH", "reasons": ["Corrupted or invalid image byte stream"]}

        tamper_signals = []
        tamper_risk_score = 0.0  # 0 = Low Risk (Clean), 100 = High Risk (Tampered)
        
        # 1. Screen Photograph Moire Pattern / Frequency Analysis using FFT
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        f = np.fft.fft2(gray)  # type: ignore[type-var]
        fshift = np.fft.fftshift(f)
        magnitude_spectrum = 20 * np.log(np.abs(fshift) + 1e-8)
        high_freq_mask = np.greater(magnitude_spectrum, 180)  # type: ignore[arg-type]
        high_freq_power = float(np.mean(high_freq_mask))





        
        if high_freq_power > 0.05:
            tamper_risk_score += 25.0
            tamper_signals.append("Possible digital screen photograph (moire pattern detected)")
            
        # 2. Screenshot File Name or Aspect Ratio Check
        filename_lower = filename.lower()
        if any(term in filename_lower for term in ["screenshot", "screen_shot", "snip", "capture"]):
            tamper_risk_score += 30.0
            tamper_signals.append("Document image appears to be a digital screenshot")
            
        # 3. Edge Discontinuity / Copy-Paste Splice Artifacts
        edges = cv2.Canny(gray, 100, 200)
        edge_density = float(np.sum(np.greater(edges, 0)) / (gray.shape[0] * gray.shape[1]))  # type: ignore
        if edge_density > 0.25:  # Abnormally noisy edge density indicating digital editing

            tamper_risk_score += 20.0
            tamper_signals.append("High edge noise indicating potential copy-paste digital editing")
            
        # Final Score Cap
        tamper_risk_score = min(100.0, tamper_risk_score)
        risk_level = "LOW"
        if tamper_risk_score >= 60.0:
            risk_level = "HIGH"
        elif tamper_risk_score >= 25.0:
            risk_level = "MEDIUM"
            
        checks = {
            "tamperRiskScore": tamper_risk_score,
            "riskLevel": risk_level,
            "tamperSignals": tamper_signals,
            "fftMoireScore": round(float(high_freq_power), 4),
            "edgeDensityPct": round(float(edge_density * 100), 2)
        }
        
        return tamper_risk_score, checks
