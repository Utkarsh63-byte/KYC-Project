import re
import cv2
import numpy as np
from typing import Dict, Any, List, Tuple, Optional

class RealOCREngine:
    """
    Template-Guided & Spatial Layout-Aware Optical Character Recognition (OCR) Engine.
    Uses canonical perspective normalization ($1000 \\times 630\\text{px}$) and
    targeted geometric sub-region slicing (ROI mapping) for Indian identity documents (Aadhaar, PAN, Passport, DL).
    """
    _easyocr_reader = None

    @classmethod
    def get_reader(cls):
        if cls._easyocr_reader is None:
            try:
                import easyocr  # type: ignore
                cls._easyocr_reader = easyocr.Reader(['en'], gpu=False, verbose=False)
            except Exception:
                cls._easyocr_reader = None
        return cls._easyocr_reader

    @classmethod
    def normalize_document_perspective(cls, img: np.ndarray) -> np.ndarray:
        """
        Warps and aligns any uploaded card into a standard canonical 1000x630 rectangle.
        """
        h, w = img.shape[:2]
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edged = cv2.Canny(blurred, 50, 200)

        contours, _ = cv2.findContours(edged, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours = sorted(contours, key=cv2.contourArea, reverse=True)

        card_contour = None
        for c in contours[:5]:
            peri = cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, 0.02 * peri, True)
            if len(approx) == 4 and cv2.contourArea(c) > (w * h * 0.15):
                card_contour = approx
                break

        if card_contour is not None:
            pts = card_contour.reshape(4, 2).astype(np.float32)
            rect = np.zeros((4, 2), dtype=np.float32)
            s = pts.sum(axis=1)
            rect[0] = pts[np.argmin(s)]  # Top-left
            rect[2] = pts[np.argmax(s)]  # Bottom-right
            diff = np.diff(pts, axis=1)
            rect[1] = pts[np.argmin(diff)]  # Top-right
            rect[3] = pts[np.argmax(diff)]  # Bottom-left

            dst = np.array([
                [0, 0],
                [1000, 0],
                [1000, 630],
                [0, 630]
            ], dtype=np.float32)

            M = cv2.getPerspectiveTransform(rect, dst)
            warped = cv2.warpPerspective(img, M, (1000, 630))
            return warped

        # Fallback: Resize directly to standard 1000x630 canonical dimensions
        return cv2.resize(img, (1000, 630))

    @classmethod
    def extract_text_from_slice(cls, slice_img: np.ndarray) -> List[str]:
        reader = cls.get_reader()
        lines: List[str] = []
        if reader is not None:
            try:
                results = reader.readtext(slice_img)
                for bbox, text, prob in results:
                    clean = text.strip()
                    if clean and len(clean) >= 2:
                        lines.append(clean)
                if lines:
                    return lines
            except Exception:
                pass

        try:
            import pytesseract  # type: ignore
            gray = cv2.cvtColor(slice_img, cv2.COLOR_BGR2GRAY)
            thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
            text_str = pytesseract.image_to_string(thresh, config='--oem 3 --psm 6')
            for line in text_str.split('\n'):
                clean = line.strip()
                if clean and len(clean) >= 2:
                    lines.append(clean)
        except Exception:
            pass

        return lines

    @classmethod
    def extract_text_blocks_with_coords(cls, img: np.ndarray) -> List[Dict[str, Any]]:
        blocks: List[Dict[str, Any]] = []
        reader = cls.get_reader()

        if reader is not None:
            try:
                results = reader.readtext(img)
                for bbox, text, prob in results:
                    cleaned = text.strip()
                    if cleaned and len(cleaned) >= 2:
                        y_center = float((bbox[0][1] + bbox[2][1]) / 2.0)
                        x_center = float((bbox[0][0] + bbox[2][0]) / 2.0)
                        height = float(abs(bbox[2][1] - bbox[0][1]))
                        blocks.append({
                            "text": cleaned,
                            "x": x_center,
                            "y": y_center,
                            "height": height,
                            "confidence": round(float(prob * 100.0), 1)
                        })
                if blocks:
                    blocks.sort(key=lambda b: b["y"])
                    return blocks
            except Exception:
                pass

        try:
            import pytesseract  # type: ignore
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            data = pytesseract.image_to_data(gray, output_type=pytesseract.Output.DICT)
            n_boxes = len(data['text'])
            for i in range(n_boxes):
                text_clean = data['text'][i].strip()
                conf = float(data['conf'][i])
                if text_clean and conf > 30 and len(text_clean) >= 2:
                    x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
                    blocks.append({
                        "text": text_clean,
                        "x": float(x + w / 2),
                        "y": float(y + h / 2),
                        "height": float(h),
                        "confidence": round(conf, 1)
                    })
            if blocks:
                blocks.sort(key=lambda b: b["y"])
                return blocks
        except Exception:
            pass

        return blocks

    @classmethod
    def parse_document(cls, image_bytes: bytes, doc_type: str) -> Tuple[List[Dict[str, Any]], float]:
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            return [
                {"fieldName": "documentStatus", "value": "NO_READABLE_TEXT_DETECTED", "confidence": 0.0, "source": "ocr_real", "validationStatus": "FAILED"},
                {"fieldName": "docNumber", "value": "NOT_DETECTED", "confidence": 0.0, "source": "ocr_real", "validationStatus": "MISSING"},
                {"fieldName": "fullName", "value": "NOT_DETECTED", "confidence": 0.0, "source": "ocr_real", "validationStatus": "MISSING"}
            ], 0.0

        # Step 1: Align & Normalise Document Perspective to Canonical 1000x630 Proportions
        canonical_img = cls.normalize_document_perspective(img)

        # Step 2: Global text extraction for full context matching
        blocks = cls.extract_text_blocks_with_coords(canonical_img)
        raw_lines = [b["text"] for b in blocks]
        full_text = " ".join(raw_lines).upper()
        doc_type_upper = doc_type.upper()

        if not blocks or len(full_text.strip()) < 3:
            fields = [
                {"fieldName": "documentStatus", "value": "NO_READABLE_TEXT_DETECTED", "confidence": 0.0, "source": "ocr_real", "validationStatus": "FAILED"},
                {"fieldName": "docNumber", "value": "NOT_DETECTED", "confidence": 0.0, "source": "ocr_real", "validationStatus": "MISSING"},
                {"fieldName": "fullName", "value": "NOT_DETECTED", "confidence": 0.0, "source": "ocr_real", "validationStatus": "MISSING"}
            ]
            return fields, 0.0

        if doc_type_upper == "AADHAAR":
            fields = cls._parse_aadhaar_template_guided(canonical_img, blocks, full_text)
        elif doc_type_upper == "PAN":
            fields = cls._parse_pan_template_guided(canonical_img, blocks, full_text)
        elif doc_type_upper == "PASSPORT":
            fields = cls._parse_passport_spatial(blocks, full_text)
        elif doc_type_upper in ["DRIVING_LICENSE", "DL"]:
            fields = cls._parse_driving_license_spatial(blocks, full_text)
        else:
            fields = cls._parse_voter_id_spatial(blocks, full_text)

        valid_fields = [f for f in fields if f.get("value") != "NOT_DETECTED" and float(f.get("confidence", 0)) > 0]  # type: ignore
        if not valid_fields:
            avg_conf = 0.0
        else:
            avg_conf = float(sum(float(f["confidence"]) for f in valid_fields) / max(len(valid_fields), 1))  # type: ignore

        return fields, round(avg_conf, 1)

    @classmethod
    def _parse_aadhaar_template_guided(cls, canonical_img: np.ndarray, blocks: List[Dict[str, Any]], full_text: str) -> List[Dict[str, Any]]:
        """
        Structure-Guided Aadhaar Card Slicing:
        - Name ROI: y in [20%, 42%], x in [32%, 96%]
        - DOB & Gender ROI: y in [38%, 60%], x in [32%, 96%]
        - 12-Digit UID ROI: y in [70%, 96%], x in [12%, 88%]
        """
        fields = []

        # --- 1. UID NUMBER EXTRACTION (Targeted Bottom ROI Slice: y 70%-96%, x 12%-88%) ---
        uid_slice = canonical_img[int(630 * 0.68) : int(630 * 0.98), int(1000 * 0.10) : int(1000 * 0.90)]
        uid_lines = cls.extract_text_from_slice(uid_slice)
        uid_slice_text = " ".join(uid_lines).upper()

        uid_val = "NOT_DETECTED"
        uid_match = re.search(r'\b\d{4}\s\d{4}\s\d{4}\b', uid_slice_text) or re.search(r'\b\d{4}\s\d{4}\s\d{4}\b', full_text)
        if uid_match:
            uid_val = uid_match.group(0)
        else:
            digits_12 = re.search(r'\b\d{12}\b', uid_slice_text) or re.search(r'\b\d{12}\b', full_text)
            if digits_12:
                raw_d = digits_12.group(0)
                uid_val = f"{raw_d[:4]} {raw_d[4:8]} {raw_d[8:]}"

        fields.append({
            "fieldName": "docNumber",
            "value": uid_val,
            "confidence": 98.5 if uid_val != "NOT_DETECTED" else 0.0,
            "source": "ocr_aadhaar_roi_uid",
            "validationStatus": "VALID" if uid_val != "NOT_DETECTED" else "MISSING"
        })

        # --- 2. DOB & GENDER EXTRACTION (Targeted Middle ROI Slice: y 36%-60%, x 30%-96%) ---
        dob_slice = canonical_img[int(630 * 0.36) : int(630 * 0.62), int(1000 * 0.30) : int(1000 * 0.96)]
        dob_lines = cls.extract_text_from_slice(dob_slice)
        dob_slice_text = " ".join(dob_lines).upper()

        dob_val = "NOT_DETECTED"
        dob_match = re.search(r'\b(0[1-9]|[12][0-9]|3[01])[-/.](0[1-9]|1[012])[-/.](19|20)\d\d\b', dob_slice_text) or re.search(r'\b(0[1-9]|[12][0-9]|3[01])[-/.](0[1-9]|1[012])[-/.](19|20)\d\d\b', full_text)
        if dob_match:
            dob_val = dob_match.group(0).replace('-', '/').replace('.', '/')
        else:
            yob_match = re.search(r'\b(19|20)\d\d\b', dob_slice_text) or re.search(r'\b(19|20)\d\d\b', full_text)
            if yob_match:
                dob_val = f"01/01/{yob_match.group(0)}"

        fields.append({
            "fieldName": "dob",
            "value": dob_val,
            "confidence": 98.0 if dob_val != "NOT_DETECTED" else 0.0,
            "source": "ocr_aadhaar_roi_dob",
            "validationStatus": "VALID" if dob_val != "NOT_DETECTED" else "MISSING"
        })

        gender_val = "NOT_DETECTED"
        if re.search(r'\b(MALE|FEMALE|TRANSGENDER)\b', dob_slice_text) or re.search(r'\b(MALE|FEMALE|TRANSGENDER)\b', full_text):
            gender_match = re.search(r'\b(MALE|FEMALE|TRANSGENDER)\b', dob_slice_text) or re.search(r'\b(MALE|FEMALE|TRANSGENDER)\b', full_text)
            gender_val = gender_match.group(0) if gender_match else "MALE"
        elif "पुरुष" in dob_slice_text or "पुरुष" in full_text:
            gender_val = "MALE"
        elif "महिला" in dob_slice_text or "महिला" in full_text:
            gender_val = "FEMALE"

        fields.append({
            "fieldName": "gender",
            "value": gender_val,
            "confidence": 98.0 if gender_val != "NOT_DETECTED" else 0.0,
            "source": "ocr_aadhaar_roi_gender",
            "validationStatus": "VALID" if gender_val != "NOT_DETECTED" else "MISSING"
        })

        # --- 3. FULL NAME EXTRACTION (Targeted Name ROI Slice: y 18%-42%, x 30%-96%) ---
        name_slice = canonical_img[int(630 * 0.18) : int(630 * 0.44), int(1000 * 0.30) : int(1000 * 0.96)]
        name_lines = cls.extract_text_from_slice(name_slice)

        name_val = "NOT_DETECTED"
        name_conf = 0.0

        ignore_terms = [
            "GOVERNMENT", "INDIA", "BHARAT", "AADHAAR", "UNIQUE", "AUTHORITY",
            "IDENTIFICATION", "ENROLMENT", "MALE", "FEMALE", "DOB", "YEAR", "BIRTH",
            "HELP", "UIDAI", "WWW", "GOV", "IN", "मेरा", "आधार", "पहचान", "सरकार", "DOB:"
        ]

        # First try: Look inside targeted Name Slice
        for line in name_lines:
            clean = re.sub(r'^(NAME|नाम|TO|SHRI|SMT|MR|MS)[:\s\-\.]+', '', line, flags=re.IGNORECASE).strip()
            upper = clean.upper()
            if len(clean) >= 3 and not any(t in upper for t in ignore_terms):
                if re.match(r'^[A-Za-z\s\.]+$', clean) and not re.search(r'\d', clean):
                    name_val = clean.title()
                    name_conf = 97.5
                    break

        # Second try: Global spatial blocks located between y 120px and y 320px
        if name_val == "NOT_DETECTED":
            for b in blocks:
                if 100.0 <= b["y"] <= 320.0 and b["x"] >= 250.0:
                    clean = re.sub(r'^(NAME|नाम|TO)[:\s\-\.]+', '', b["text"], flags=re.IGNORECASE).strip()
                    upper = clean.upper()
                    if len(clean) >= 3 and not any(t in upper for t in ignore_terms):
                        if re.match(r'^[A-Za-z\s\.]+$', clean) and not re.search(r'\d', clean):
                            name_val = clean.title()
                            name_conf = b["confidence"]
                            break

        fields.append({
            "fieldName": "fullName",
            "value": name_val,
            "confidence": name_conf if name_val != "NOT_DETECTED" else 0.0,
            "source": "ocr_aadhaar_roi_name",
            "validationStatus": "VALID" if name_val != "NOT_DETECTED" else "MISSING"
        })

        return fields

    @classmethod
    def _parse_pan_template_guided(cls, canonical_img: np.ndarray, blocks: List[Dict[str, Any]], full_text: str) -> List[Dict[str, Any]]:
        """
        Structure-Guided PAN Card Slicing:
        - Full Name ROI: y in [24%, 42%], x in [4%, 72%]
        - Father's Name ROI: y in [42%, 60%], x in [4%, 72%]
        - DOB ROI: y in [58%, 74%], x in [4%, 55%]
        - PAN Number ROI: y in [70%, 90%], x in [4%, 65%]
        """
        fields = []

        # --- 1. PAN NUMBER EXTRACTION (Targeted Bottom-Left Slice: y 68%-92%, x 4%-68%) ---
        pan_slice = canonical_img[int(630 * 0.68) : int(630 * 0.94), int(1000 * 0.04) : int(1000 * 0.70)]
        pan_lines = cls.extract_text_from_slice(pan_slice)
        pan_slice_text = " ".join(pan_lines).upper()

        pan_val = "NOT_DETECTED"
        pan_match = re.search(r'\b[A-Z0-9]{5}[0-9OISZB]{4}[A-Z0-9]\b', pan_slice_text) or re.search(r'\b[A-Z0-9]{5}[0-9OISZB]{4}[A-Z0-9]\b', full_text)
        if pan_match:
            raw = pan_match.group(0)
            p1 = raw[:5].replace('0', 'O').replace('1', 'I').replace('8', 'B')
            p2 = raw[5:9].replace('O', '0').replace('I', '1').replace('S', '5').replace('Z', '2').replace('B', '8')
            p3 = raw[9:].replace('0', 'O').replace('1', 'I')
            pan_val = f"{p1}{p2}{p3}"

        fields.append({
            "fieldName": "docNumber",
            "value": pan_val,
            "confidence": 98.8 if pan_val != "NOT_DETECTED" else 0.0,
            "source": "ocr_pan_roi_number",
            "validationStatus": "VALID" if pan_val != "NOT_DETECTED" else "MISSING"
        })

        # --- 2. DOB EXTRACTION (Targeted Slice: y 56%-76%, x 4%-55%) ---
        dob_slice = canonical_img[int(630 * 0.56) : int(630 * 0.78), int(1000 * 0.04) : int(1000 * 0.58)]
        dob_lines = cls.extract_text_from_slice(dob_slice)
        dob_slice_text = " ".join(dob_lines).upper()

        dob_val = "NOT_DETECTED"
        dob_match = re.search(r'\b(0[1-9]|[12][0-9]|3[01])[-/.](0[1-9]|1[012])[-/.](19|20)\d\d\b', dob_slice_text) or re.search(r'\b(0[1-9]|[12][0-9]|3[01])[-/.](0[1-9]|1[012])[-/.](19|20)\d\d\b', full_text)
        if dob_match:
            dob_val = dob_match.group(0).replace('-', '/').replace('.', '/')

        fields.append({
            "fieldName": "dob",
            "value": dob_val,
            "confidence": 98.5 if dob_val != "NOT_DETECTED" else 0.0,
            "source": "ocr_pan_roi_dob",
            "validationStatus": "VALID" if dob_val != "NOT_DETECTED" else "MISSING"
        })

        # --- 3. NAME EXTRACTION (Targeted Slice: y 22%-42%, x 4%-72%) ---
        name_slice = canonical_img[int(630 * 0.22) : int(630 * 0.44), int(1000 * 0.04) : int(1000 * 0.72)]
        name_lines = cls.extract_text_from_slice(name_slice)

        name_val = "NOT_DETECTED"
        ignore_pan = ["INCOME", "TAX", "DEPARTMENT", "GOVT", "INDIA", "PERMANENT", "ACCOUNT", "NUMBER", "CARD", "NAME"]
        for line in name_lines:
            clean = line.strip().upper()
            if len(clean) >= 3 and not any(t in clean for t in ignore_pan):
                if re.match(r'^[A-Z\s\.]+$', clean) and not re.search(r'\d', clean):
                    name_val = clean
                    break

        if name_val == "NOT_DETECTED":
            # Search in top candidate blocks
            for b in blocks:
                if 120.0 <= b["y"] <= 260.0 and b["x"] < 700.0:
                    clean = b["text"].strip().upper()
                    if len(clean) >= 3 and not any(t in clean for t in ignore_pan):
                        if re.match(r'^[A-Z\s\.]+$', clean) and not re.search(r'\d', clean):
                            name_val = clean
                            break

        fields.append({
            "fieldName": "fullName",
            "value": name_val,
            "confidence": 96.5 if name_val != "NOT_DETECTED" else 0.0,
            "source": "ocr_pan_roi_name",
            "validationStatus": "VALID" if name_val != "NOT_DETECTED" else "MISSING"
        })

        # --- 4. FATHER'S NAME EXTRACTION (Targeted Slice: y 42%-60%, x 4%-72%) ---
        father_slice = canonical_img[int(630 * 0.42) : int(630 * 0.60), int(1000 * 0.04) : int(1000 * 0.72)]
        father_lines = cls.extract_text_from_slice(father_slice)

        father_val = "NOT_DETECTED"
        for line in father_lines:
            clean = line.strip().upper()
            if len(clean) >= 3 and not any(t in clean for t in ignore_pan) and clean != name_val:
                if re.match(r'^[A-Z\s\.]+$', clean) and not re.search(r'\d', clean):
                    father_val = clean
                    break

        if father_val == "NOT_DETECTED":
            for b in blocks:
                if 250.0 <= b["y"] <= 380.0 and b["x"] < 700.0:
                    clean = b["text"].strip().upper()
                    if len(clean) >= 3 and not any(t in clean for t in ignore_pan) and clean != name_val:
                        if re.match(r'^[A-Z\s\.]+$', clean) and not re.search(r'\d', clean):
                            father_val = clean
                            break

        fields.append({
            "fieldName": "fatherName",
            "value": father_val,
            "confidence": 94.0 if father_val != "NOT_DETECTED" else 0.0,
            "source": "ocr_pan_roi_father",
            "validationStatus": "VALID" if father_val != "NOT_DETECTED" else "MISSING"
        })

        return fields

    @classmethod
    def _parse_passport_spatial(cls, blocks: List[Dict[str, Any]], full_text: str) -> List[Dict[str, Any]]:
        passport_match = re.search(r'\b[A-Z][0-9]{7}\b', full_text)
        dob_match = re.search(r'\b(0[1-9]|[12][0-9]|3[01])[-/.](0[1-9]|1[012])[-/.](19|20)\d\d\b', full_text)
        has_india = "INDIAN" in full_text or "REPUBLIC OF INDIA" in full_text

        name_val = "NOT_DETECTED"
        name_conf = 0.0
        for b in blocks:
            clean = b["text"].strip().upper()
            if len(clean) >= 3 and not re.search(r'PASSPORT|REPUBLIC|INDIA|MINISTRY|EXTERNAL|GIVEN|SURNAME|\d', clean):
                if re.match(r'^[A-Z\s\.]+$', clean):
                    name_val = clean
                    name_conf = b["confidence"]
                    break

        return [
            {"fieldName": "docNumber", "value": passport_match.group(0) if passport_match else "NOT_DETECTED", "confidence": 98.0 if passport_match else 0.0, "source": "ocr_real_passport", "validationStatus": "VALID" if passport_match else "MISSING"},
            {"fieldName": "nationality", "value": "INDIAN" if has_india else "NOT_DETECTED", "confidence": 99.0 if has_india else 0.0, "source": "ocr_real_passport", "validationStatus": "VALID" if has_india else "MISSING"},
            {"fieldName": "dob", "value": dob_match.group(0).replace('-', '/') if dob_match else "NOT_DETECTED", "confidence": 97.0 if dob_match else 0.0, "source": "ocr_real_passport", "validationStatus": "VALID" if dob_match else "MISSING"},
            {"fieldName": "fullName", "value": name_val, "confidence": name_conf if name_val != "NOT_DETECTED" else 0.0, "source": "ocr_real_passport", "validationStatus": "VALID" if name_val != "NOT_DETECTED" else "MISSING"}
        ]

    @classmethod
    def _parse_driving_license_spatial(cls, blocks: List[Dict[str, Any]], full_text: str) -> List[Dict[str, Any]]:
        dl_match = re.search(r'\b[A-Z]{2}[-\s]?[0-9]{2}[-\s]?[0-9]{4,11}\b', full_text)
        dob_match = re.search(r'\b(0[1-9]|[12][0-9]|3[01])[-/.](0[1-9]|1[012])[-/.](19|20)\d\d\b', full_text)

        name_val = "NOT_DETECTED"
        name_conf = 0.0
        for b in blocks:
            clean = b["text"].strip().upper()
            if len(clean) >= 3 and not re.search(r'DRIVING|LICENCE|LICENSE|UNION|STATE|TRANSPORT|NAME|DOB|\d', clean):
                if re.match(r'^[A-Z\s\.]+$', clean):
                    name_val = clean
                    name_conf = b["confidence"]
                    break

        return [
            {"fieldName": "docNumber", "value": dl_match.group(0) if dl_match else "NOT_DETECTED", "confidence": 97.0 if dl_match else 0.0, "source": "ocr_real_dl", "validationStatus": "VALID" if dl_match else "MISSING"},
            {"fieldName": "dob", "value": dob_match.group(0).replace('-', '/') if dob_match else "NOT_DETECTED", "confidence": 97.0 if dob_match else 0.0, "source": "ocr_real_dl", "validationStatus": "VALID" if dob_match else "MISSING"},
            {"fieldName": "fullName", "value": name_val, "confidence": name_conf if name_val != "NOT_DETECTED" else 0.0, "source": "ocr_real_dl", "validationStatus": "VALID" if name_val != "NOT_DETECTED" else "MISSING"}
        ]

    @classmethod
    def _parse_voter_id_spatial(cls, blocks: List[Dict[str, Any]], full_text: str) -> List[Dict[str, Any]]:
        epic_match = re.search(r'\b[A-Z]{3}[0-9]{7}\b', full_text)
        return [
            {"fieldName": "docNumber", "value": epic_match.group(0) if epic_match else "NOT_DETECTED", "confidence": 96.0 if epic_match else 0.0, "source": "ocr_real_voter", "validationStatus": "VALID" if epic_match else "MISSING"}
        ]
