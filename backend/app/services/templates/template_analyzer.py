import re
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from app.services.documents.pdf_processor import PDFProcessor
from app.services.documents.docx_processor import DOCXProcessor

logger = logging.getLogger(__name__)

# Standard domain field heuristics to recognize common field patterns
COMMON_FIELD_PATTERNS = [
    # Personal
    {"regex": r"(?:full\s+)?name(?:\s+of\s+applicant)?", "key": "full_name", "label": "Full Legal Name", "type": "text", "required": True, "section": "Personal Information"},
    {"regex": r"(?:first\s+name|given\s+name)", "key": "first_name", "label": "First Name", "type": "text", "required": False, "section": "Personal Information"},
    {"regex": r"(?:last\s+name|surname|family\s+name)", "key": "last_name", "label": "Last Name", "type": "text", "required": False, "section": "Personal Information"},
    {"regex": r"(?:date\s+of\s+birth|d\.?o\.?b\.?|birth\s*date)", "key": "date_of_birth", "label": "Date of Birth", "type": "date", "required": True, "section": "Personal Information"},
    {"regex": r"(?:gender|sex)", "key": "gender", "label": "Gender", "type": "select", "required": True, "section": "Personal Information"},
    {"regex": r"(?:marital\s+status|married\s*\/)", "key": "marital_status", "label": "Marital Status", "type": "select", "required": False, "section": "Personal Information"},
    {"regex": r"(?:spouse\s+name|name\s+of\s+spouse)", "key": "spouse_name", "label": "Spouse Full Name", "type": "text", "required": False, "section": "Personal Information"},
    {"regex": r"(?:nationality|citizenship)", "key": "nationality", "label": "Nationality", "type": "text", "required": False, "section": "Personal Information"},
    
    # Contact
    {"regex": r"(?:e-?mail(?:\s+address)?)", "key": "email", "label": "Email Address", "type": "email", "required": True, "section": "Contact Details"},
    {"regex": r"(?:phone(?:\s+number)?|mobile(?:\s+no)?|contact\s+no)", "key": "phone_number", "label": "Phone Number", "type": "phone", "required": True, "section": "Contact Details"},
    {"regex": r"(?:permanent\s+address|residential\s+address|current\s+address|address)", "key": "address", "label": "Residential Address", "type": "text", "required": True, "section": "Contact Details"},
    {"regex": r"(?:city|town)", "key": "city", "label": "City", "type": "text", "required": False, "section": "Contact Details"},
    {"regex": r"(?:state|province)", "key": "state", "label": "State", "type": "text", "required": False, "section": "Contact Details"},
    {"regex": r"(?:pin\s*code|postal\s*code|zip\s*code)", "key": "postal_code", "label": "Postal Code", "type": "text", "required": True, "section": "Contact Details"},

    # Identification
    {"regex": r"(?:pan(?:\s+card|\s+number|\s+no)?|permanent\s+account\s+number)", "key": "pan_number", "label": "Permanent Account Number (PAN)", "type": "text", "required": False, "section": "Identification"},
    {"regex": r"(?:aadhaar(?:\s+card|\s+number|\s+no)?|uidai|national\s+id|ssn|social\s+security)", "key": "national_id", "label": "National ID / Aadhaar", "type": "text", "required": False, "section": "Identification"},
    {"regex": r"(?:passport(?:\s+number|\s+no)?)", "key": "passport_number", "label": "Passport Number", "type": "text", "required": False, "section": "Identification"},

    # Financial & Employment
    {"regex": r"(?:annual\s+income|gross\s+(?:income|salary|compensation)|remuneration)", "key": "annual_income", "label": "Annual Income", "type": "number", "required": False, "section": "Financial & Employment"},
    {"regex": r"(?:employer|company\s+name|organization|workplace)", "key": "employer_name", "label": "Employer / Company Name", "type": "text", "required": False, "section": "Financial & Employment"},
    {"regex": r"(?:designation|job\s+title|role|position)", "key": "job_title", "label": "Designation / Job Title", "type": "text", "required": False, "section": "Financial & Employment"},
    {"regex": r"(?:bank\s+account(?:\s+number|\s+no)?|account\s+no)", "key": "bank_account_number", "label": "Bank Account Number", "type": "text", "required": False, "section": "Financial & Employment"},
    {"regex": r"(?:bank\s+name)", "key": "bank_name", "label": "Bank Name", "type": "text", "required": False, "section": "Financial & Employment"},
    {"regex": r"(?:ifsc(?:\s+code)?|swift(?:\s+code)?|routing\s+number)", "key": "bank_ifsc_code", "label": "Bank IFSC / Routing Code", "type": "text", "required": False, "section": "Financial & Employment"},

    # Education
    {"regex": r"(?:highest\s+qualification|degree|education)", "key": "qualification", "label": "Highest Qualification", "type": "text", "required": False, "section": "Education"},
    {"regex": r"(?:university|college|institution)", "key": "institution_name", "label": "College / University Name", "type": "text", "required": False, "section": "Education"},
    {"regex": r"(?:graduation\s+year|year\s+of\s+passing)", "key": "graduation_year", "label": "Graduation Year", "type": "number", "required": False, "section": "Education"},
]

class TemplateAnalyzer:
    """Analyzes blank form templates (PDF or DOCX) to extract canonical field schemas."""

    def __init__(self, file_path: str):
        self.file_path = Path(file_path)

    def analyze(self) -> List[Dict[str, Any]]:
        """Extracts field definitions from the template."""
        extension = self.file_path.suffix.lower()
        if extension == ".pdf":
            return self._analyze_pdf()
        elif extension in [".docx", ".doc"]:
            return self._analyze_docx()
        elif extension in [".png", ".jpg", ".jpeg"]:
            return self._analyze_image()
        else:
            raise ValueError(f"Unsupported template format: {extension}")

    def _analyze_image(self) -> List[Dict[str, Any]]:
        """Analyzes an image template (.png, .jpg, .jpeg) using OCR and coordinate detection."""
        from app.services.ocr.tesseract_service import TesseractOCRService
        ocr = TesseractOCRService()
        res = ocr.extract_text_and_coordinates(self.file_path)
        full_text = res.get("text", "")
        word_boxes = res.get("word_boxes", [])

        fields: List[Dict[str, Any]] = []
        seen_keys = set()

        if full_text:
            detected = self._extract_fields_from_text(full_text, page_number=1)
            for d in detected:
                key = d["field_key"]
                if key not in seen_keys:
                    seen_keys.add(key)
                    # Find matching word box coordinates
                    lbl_lower = d["label"].lower()
                    key_lower = key.lower()
                    for box in word_boxes:
                        w = box["text"].lower()
                        if (w in lbl_lower or w in key_lower) and len(w) > 3:
                            d["bounding_box"] = {
                                "x": box["x"] + box["width"] + 10,
                                "y": box["y"],
                                "width": 200,
                                "height": max(20, box["height"]),
                                "page": 1,
                            }
                            break
                    fields.append(d)

        if not fields:
            logger.info("Image template OCR sparse; populating universal form baseline.")
            fields = self._get_default_universal_fields()

        return fields

    def _analyze_pdf(self) -> List[Dict[str, Any]]:
        processor = PDFProcessor(str(self.file_path))
        metadata = processor.get_metadata()
        pages = processor.extract_text_pages()

        fields: List[Dict[str, Any]] = []
        seen_keys = set()

        # 1. Check if it's an AcroForm with explicit fields and detect widget coordinates
        import fitz
        try:
            doc = fitz.open(str(self.file_path))
            for page_idx, page in enumerate(doc):
                for widget in page.widgets():
                    field_name = widget.field_name or ""
                    if field_name:
                        clean_label = field_name.replace("_", " ").title()
                        field_key = re.sub(r"[^a-zA-Z0-9_]", "", field_name.lower().replace(" ", "_"))
                        matched_pattern = self._match_known_pattern(clean_label)
                        if matched_pattern:
                            field_key = matched_pattern["key"]
                            clean_label = matched_pattern["label"]
                            f_type = matched_pattern["type"]
                            req = matched_pattern["required"]
                            sec = matched_pattern["section"]
                        else:
                            f_type = "text"
                            req = False
                            sec = "General"

                        rect = widget.rect
                        if field_key not in seen_keys:
                            seen_keys.add(field_key)
                            fields.append({
                                "field_key": field_key,
                                "label": clean_label,
                                "field_type": f_type,
                                "required": req,
                                "section": sec,
                                "page_number": page_idx + 1,
                                "bounding_box": {
                                    "x": round(rect.x0, 1),
                                    "y": round(rect.y0, 1),
                                    "width": round(rect.width, 1),
                                    "height": round(rect.height, 1),
                                    "page": page_idx + 1,
                                },
                                "constraints": {},
                            })
            doc.close()
        except Exception as e:
            logger.debug(f"AcroForm widget detection note: {e}")

        # 2. Extract fields from printable text / form prompts
        for page in pages:
            page_text = page["text"]
            detected = self._extract_fields_from_text(page_text, page["page_number"])
            for d in detected:
                if d["field_key"] not in seen_keys:
                    seen_keys.add(d["field_key"])
                    fields.append(d)

        # 3. Detect coordinates for flat/underlined text fields
        try:
            doc = fitz.open(str(self.file_path))
            for page_idx, page in enumerate(doc):
                words = page.get_text("words")
                for f in fields:
                    if not f.get("bounding_box") and f.get("page_number", 1) == page_idx + 1:
                        lbl_tokens = f["label"].lower().split()
                        for w in words:
                            if w[4].lower() in lbl_tokens and len(w[4]) > 3:
                                f["bounding_box"] = {
                                    "x": round(w[2] + 5, 1),
                                    "y": round(w[1], 1),
                                    "width": 180.0,
                                    "height": round(max(15, w[3] - w[1] + 4), 1),
                                    "page": page_idx + 1,
                                }
                                break
            doc.close()
        except Exception as e:
            logger.debug(f"PDF word bbox note: {e}")

        # Fallback if form is very sparse or scanned without OCR yet
        if not fields:
            logger.info("Template text sparse; populating standard universal form baseline.")
            fields = self._get_default_universal_fields()

        return fields

    def _analyze_docx(self) -> List[Dict[str, Any]]:
        processor = DOCXProcessor(str(self.file_path))
        data = processor.extract_text_and_tables()

        fields: List[Dict[str, Any]] = []
        seen_keys = set()

        # Extract from paragraphs and tables
        detected = self._extract_fields_from_text(data["full_text"], page_number=1)
        for d in detected:
            if d["field_key"] not in seen_keys:
                seen_keys.add(d["field_key"])
                fields.append(d)

        if not fields:
            fields = self._get_default_universal_fields()

        return fields

    def _extract_fields_from_text(self, text: str, page_number: int) -> List[Dict[str, Any]]:
        """Matches lines in text against known patterns and colon/underline prompt structures."""
        results: List[Dict[str, Any]] = []
        seen = set()

        # 1. Match against known catalog
        for pat in COMMON_FIELD_PATTERNS:
            if re.search(pat["regex"], text, re.IGNORECASE):
                key = pat["key"]
                if key not in seen:
                    seen.add(key)
                    results.append({
                        "field_key": key,
                        "label": pat["label"],
                        "field_type": pat["type"],
                        "required": pat["required"],
                        "section": pat["section"],
                        "page_number": page_number,
                        "constraints": {},
                    })

        # 2. Match generic "Label: _______", "Label ______", or prompt line immediately followed by underline
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        for i, line in enumerate(lines):
            raw_label = None

            # Pattern A: "Label: ______" or "Label: ......"
            colon_match = re.match(r"^([A-Za-z0-9\s/()-]{2,40})\s*:\s*(?:_{2,}|\.{2,}|\[\s*\]|$)", line)
            if colon_match:
                raw_label = colon_match.group(1).strip()

            # Pattern B: "Label ____________________" on the same line without colon
            elif re.search(r"_{3,}", line):
                candidate = re.sub(r"[_.\s]+$", "", line).strip()
                if candidate and len(candidate) > 2 and len(candidate) < 45:
                    raw_label = candidate

            # Pattern C: Line is an underline "______", and preceding line was a label
            elif re.match(r"^_{3,}$", line) and i > 0:
                prev = lines[i - 1].strip()
                # Ignore titles, headers or declarations
                if prev and len(prev) < 45 and not prev.isupper() and not "declaration" in prev.lower() and not "page" in prev.lower():
                    raw_label = prev

            if raw_label:
                # Clean up prompt like "(INR)" or "(masked)"
                clean_name = re.sub(r"\([^)]*\)", "", raw_label).strip()
                field_key = re.sub(r"[^a-zA-Z0-9_]", "", clean_name.lower().replace(" ", "_"))
                if field_key not in seen and len(field_key) > 2:
                    matched = self._match_known_pattern(raw_label) or self._match_known_pattern(clean_name)
                    if matched:
                        key = matched["key"]
                        if key not in seen:
                            seen.add(key)
                            results.append({
                                "field_key": key,
                                "label": matched["label"],
                                "field_type": matched["type"],
                                "required": matched["required"],
                                "section": matched["section"],
                                "page_number": page_number,
                                "constraints": {},
                            })
                    else:
                        seen.add(field_key)
                        results.append({
                            "field_key": field_key,
                            "label": clean_name.title(),
                            "field_type": "text",
                            "required": False,
                            "section": "General",
                            "page_number": page_number,
                            "constraints": {},
                        })

        return results

    def _match_known_pattern(self, label: str) -> Optional[Dict[str, Any]]:
        for pat in COMMON_FIELD_PATTERNS:
            if re.search(pat["regex"], label, re.IGNORECASE):
                return pat
        return None

    def _get_default_universal_fields(self) -> List[Dict[str, Any]]:
        """Baseline fields for a generic form template."""
        return [
            {"field_key": "full_name", "label": "Full Legal Name", "field_type": "text", "required": True, "section": "Personal Information", "page_number": 1, "constraints": {}},
            {"field_key": "date_of_birth", "label": "Date of Birth", "field_type": "date", "required": True, "section": "Personal Information", "page_number": 1, "constraints": {}},
            {"field_key": "gender", "label": "Gender", "field_type": "select", "required": False, "section": "Personal Information", "page_number": 1, "constraints": {}},
            {"field_key": "email", "label": "Email Address", "field_type": "email", "required": True, "section": "Contact Details", "page_number": 1, "constraints": {}},
            {"field_key": "phone_number", "label": "Phone Number", "field_type": "phone", "required": True, "section": "Contact Details", "page_number": 1, "constraints": {}},
            {"field_key": "address", "label": "Residential Address", "field_type": "text", "required": True, "section": "Contact Details", "page_number": 1, "constraints": {}},
            {"field_key": "postal_code", "label": "Postal / ZIP Code", "field_type": "text", "required": True, "section": "Contact Details", "page_number": 1, "constraints": {}},
            {"field_key": "annual_income", "label": "Annual Income", "field_type": "number", "required": False, "section": "Financial & Employment", "page_number": 1, "constraints": {}},
            {"field_key": "bank_account_number", "label": "Bank Account Number", "field_type": "text", "required": False, "section": "Financial & Employment", "page_number": 1, "constraints": {}},
            {"field_key": "bank_ifsc_code", "label": "Bank IFSC / Routing Code", "field_type": "text", "required": False, "section": "Financial & Employment", "page_number": 1, "constraints": {}},
        ]
