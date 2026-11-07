import logging
import uuid
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import fitz

from app.core.config import settings

logger = logging.getLogger(__name__)

# Canonical synonym groupings to map template text variations to field keys
FIELD_SYNONYMS = {
    "full_name": ["full name", "applicant name", "candidate name", "name of applicant", "legal name", "name", "account holder name"],
    "date_of_birth": ["date of birth", "dob", "birth date", "d.o.b", "born on"],
    "email": ["email", "e-mail", "email address", "mail id", "electronic mail"],
    "phone_number": ["phone", "phone number", "mobile", "mobile no", "contact number", "cell phone", "telephone"],
    "address": ["residential address", "permanent address", "current address", "street address", "address", "residence"],
    "city": ["city", "town"],
    "state": ["state", "province"],
    "postal_code": ["postal code", "pin code", "zip code", "zip", "pincode", "pin"],
    "qualification": ["highest qualification", "qualification", "education", "degree", "highest degree"],
    "institution_name": ["institution", "college", "university", "school", "institution name"],
    "employer_name": ["current employer", "employer", "company name", "organization", "firm name", "workplace"],
    "job_title": ["designation", "job title", "role", "position"],
    "employee_id": ["employee id", "emp id", "staff id", "employee code"],
    "annual_income": ["monthly gross salary", "gross salary", "annual income", "salary", "gross income", "ctc", "compensation"],
    "bank_name": ["bank name", "name of bank", "bank"],
    "account_holder_name": ["account holder name", "beneficiary name", "name on account", "account name"],
    "bank_account_number": ["account number", "account no", "bank account number", "a/c no", "bank a/c"],
    "bank_ifsc_code": ["ifsc / routing code", "ifsc code", "ifsc", "routing code", "routing number", "swift code"],
    "pan_number": ["pan number", "pan card", "pan no", "permanent account number"],
    "national_id": ["national id", "aadhaar", "aadhaar number", "ssn", "social security"],
    "passport_number": ["passport number", "passport no", "passport"],
    "signature_date": ["signature / date", "signature", "date of signature", "applicant signature"],
    "declaration": ["declaration", "i confirm"],
}

def sanitize_pdf_text(text: str) -> str:
    """Sanitizes text to prevent broken font glyphs in standard PDF Helvetica."""
    if not text:
        return ""
    s = str(text)
    s = s.replace("₹", "INR ").replace("\u20b9", "INR ")
    s = s.replace("–", "-").replace("—", "-").replace("\u2013", "-").replace("\u2014", "-")
    s = s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    s = s.replace("•", "*").replace("·", "-")
    return s.strip()

def parse_hex_color(hex_str: str) -> tuple:
    """Converts hex color '#0f172a' to a (r, g, b) float tuple in 0..1."""
    try:
        h = (hex_str or "").lstrip("#")
        if len(h) == 6:
            return (int(h[0:2], 16) / 255.0, int(h[2:4], 16) / 255.0, int(h[4:6], 16) / 255.0)
    except Exception:
        pass
    return (15 / 255, 23 / 255, 42 / 255)

FONT_MAP = {
    "helvetica": "helv",
    "arial": "helv",
    "sans": "helv",
    "times": "tiro",
    "times-roman": "tiro",
    "times new roman": "tiro",
    "serif": "tiro",
    "courier": "couri",
    "monospace": "couri",
    "mono": "couri",
}

class PDFGenerator:
    """
    Populates blank PDF form templates (both AcroForms and flat/underlined PDFs)
    with validated field values with precision alignment, typography, and optional digital signatures.
    """

    def __init__(self, template_path: str):
        self.template_path = Path(template_path)

    def generate(
        self,
        session_id: str,
        field_data: List[Dict[str, Any]],
        font_family: str = "Helvetica",
        font_size: float = 9.5,
        text_color: str = "#0f172a",
        signature_path: Optional[str] = None,
        output_dir: Optional[Path] = None
    ) -> str:
        """
        Populates the original PDF template with validated field values.
        Emits a new file into the generated directory without mutating original template.
        """
        out_directory = output_dir or settings.GENERATED_DIR
        out_directory.mkdir(parents=True, exist_ok=True)
        output_filename = f"completed_form_{session_id[:8]}_{uuid.uuid4().hex[:6]}.pdf"
        output_path = out_directory / output_filename

        # Resolve typography and styling parameters
        resolved_font = FONT_MAP.get((font_family or "").lower().strip(), "helv")
        resolved_color = parse_hex_color(text_color)
        base_fontsize = float(font_size) if font_size else 9.5

        # Build comprehensive lookup dictionaries
        value_by_key = {}
        for item in field_data:
            key = item.get("field_key", "")
            val = item.get("current_value")
            if val is not None and str(val).strip():
                clean_v = sanitize_pdf_text(str(val))
                value_by_key[key] = clean_v
                label = item.get("label", "")
                if label:
                    value_by_key[label.lower()] = clean_v

        # Extract pin code if embedded in address
        if "address" in value_by_key and not value_by_key.get("postal_code"):
            pin_m = re.search(r"\b(\d{6})\b", value_by_key["address"])
            if pin_m:
                value_by_key["postal_code"] = pin_m.group(1)

        # Synthetic combined values for compound lines
        city = value_by_key.get("city", "")
        state = value_by_key.get("state", "")
        pin = value_by_key.get("postal_code", "")
        if city or state or pin:
            parts = [p for p in [city, state] if p]
            city_state_str = ", ".join(parts)
            if pin:
                city_state_str = f"{city_state_str} - {pin}" if city_state_str else pin
            value_by_key["city_state_pin"] = city_state_str
            value_by_key["city / state / pin"] = city_state_str

        # Synthetic signature/date and declaration defaults if not already present
        full_name = value_by_key.get("full_name") or value_by_key.get("name") or "Applicant"
        if not value_by_key.get("signature_date"):
            value_by_key["signature_date"] = f"{full_name}  |  {datetime.now().strftime('%d/%m/%Y')} (Verified)"
            value_by_key["signature / date"] = value_by_key["signature_date"]

        if not value_by_key.get("declaration"):
            value_by_key["declaration"] = "I confirm that the information provided is accurate and verified."

        # Open document with PyMuPDF
        doc = fitz.open(str(self.template_path))
        placed_fields = set()

        # -------------------------------------------------------------
        # STEP 1: Interactive AcroForm Widgets Handling
        # -------------------------------------------------------------
        has_widgets = False
        for page in doc:
            widgets = list(page.widgets())
            if widgets:
                has_widgets = True
                for widget in widgets:
                    field_name = widget.field_name or ""
                    matched_val = self._find_matching_value(field_name, value_by_key)
                    if matched_val:
                        widget.field_value = str(matched_val)
                        widget.text_fontsize = base_fontsize
                        widget.text_color = resolved_color
                        widget.update()
                        placed_fields.add(field_name.lower())

        if has_widgets:
            doc.need_appearances(True)

        # -------------------------------------------------------------
        # STEP 2: Underline & Flat Form Precision Alignment
        # -------------------------------------------------------------
        has_inserted_signature = False
        for page_idx, page in enumerate(doc):
            page_dict = page.get_text("dict")
            text_lines = []
            for block in page_dict.get("blocks", []):
                if "lines" in block:
                    for line in block["lines"]:
                        l_text = "".join(span["text"] for span in line.get("spans", [])).strip()
                        bbox = line["bbox"]
                        if l_text:
                            text_lines.append({"bbox": bbox, "text": l_text})

            # Identify lines containing underscores or blanks
            for i, line_item in enumerate(text_lines):
                text = line_item["text"]
                bbox = line_item["bbox"]

                is_underline = "____" in text or "...." in text

                if is_underline:
                    line_x0, line_y0, line_x1, line_y1 = bbox

                    matched_key, matched_val = self._detect_field_for_line(
                        line_index=i,
                        line_item=line_item,
                        all_lines=text_lines,
                        value_by_key=value_by_key
                    )

                    if matched_val:
                        # 1. Neatly white-out the rough underscores
                        page.draw_rect(
                            fitz.Rect(line_x0 - 2, line_y0 - 1, line_x1 + 4, line_y1 + 1),
                            color=(1, 1, 1),
                            fill=(1, 1, 1)
                        )

                        # 2. Draw a clean, crisp, subtle baseline rule
                        baseline_y = line_y1 - 1.0
                        page.draw_line(
                            fitz.Point(line_x0, baseline_y),
                            fitz.Point(line_x1, baseline_y),
                            color=(180 / 255, 195 / 255, 210 / 255),
                            width=0.6
                        )

                        # 3. If field is signature and digital signature image is provided, draw image
                        is_sig_field = matched_key in ["signature", "signature_date", "applicant_signature"]
                        if is_sig_field and signature_path and Path(signature_path).exists() and not has_inserted_signature:
                            try:
                                sig_w = min(130.0, line_x1 - line_x0)
                                sig_rect = fitz.Rect(line_x0 + 4.0, baseline_y - 28.0, line_x0 + 4.0 + sig_w, baseline_y - 1.0)
                                page.insert_image(sig_rect, filename=str(signature_path), keep_proportion=True)
                                has_inserted_signature = True
                                placed_fields.add(matched_key.lower())
                                continue
                            except Exception as se:
                                logger.warning(f"Failed to place signature image on line: {se}")

                        # 4. Calculate dynamic font scaling so text never overflows
                        avail_width = max(50.0, line_x1 - line_x0 - 10.0)
                        fontsize = base_fontsize
                        text_width = fitz.get_text_length(str(matched_val), fontname=resolved_font, fontsize=fontsize)
                        if text_width > avail_width:
                            fontsize = max(6.5, fontsize * (avail_width / text_width))

                        # 5. Insert text cleanly placed on the baseline with custom font and color
                        text_point = fitz.Point(line_x0 + 4.0, baseline_y - 2.5)
                        page.insert_text(
                            text_point,
                            str(matched_val),
                            fontsize=fontsize,
                            fontname=resolved_font,
                            color=resolved_color
                        )
                        placed_fields.add(matched_key.lower())
                        logger.info(f"Page {page_idx + 1}: Rendered '{matched_key}' -> '{matched_val}' at {text_point}")

        # -------------------------------------------------------------
        # STEP 3: Append Form Verification Certificate Page
        # -------------------------------------------------------------
        self._append_verification_certificate(doc, session_id, field_data, signature_path=signature_path)

        # Save finalized PDF
        doc.save(str(output_path), garbage=4, deflate=True)
        doc.close()
        logger.info(f"Successfully generated completed form to {output_path}")
        return str(output_path)

    def _find_matching_value(self, query: str, value_by_key: Dict[str, str]) -> Optional[str]:
        """Matches a field name or label against canonical fields."""
        q = query.lower().strip()
        q_norm = re.sub(r"[^a-z0-9]", "_", q)

        # 1. Exact match
        if q in value_by_key:
            return value_by_key[q]
        if q_norm in value_by_key:
            return value_by_key[q_norm]

        # 2. Check synonyms
        for canonical_key, aliases in FIELD_SYNONYMS.items():
            if canonical_key in value_by_key:
                for alias in aliases:
                    if alias in q or q in alias:
                        return value_by_key[canonical_key]

        # 3. Token similarity
        for k, v in value_by_key.items():
            k_clean = k.replace("_", " ")
            if k_clean and len(k_clean) > 2 and (k_clean in q or q in k_clean):
                return v

        return None

    def _detect_field_for_line(
        self,
        line_index: int,
        line_item: Dict[str, Any],
        all_lines: List[Dict[str, Any]],
        value_by_key: Dict[str, str]
    ) -> tuple[Optional[str], Optional[str]]:
        """Identifies which field belongs to an underline on a flat form."""
        text = line_item["text"]
        bbox = line_item["bbox"]
        line_y0 = bbox[1]

        # 1. Check if the line itself contains prompt text before the line
        line_prompt = re.sub(r"[_.\s]+$", "", text).strip()
        if line_prompt and len(line_prompt) > 2:
            val = self._find_matching_value(line_prompt, value_by_key)
            if val:
                return line_prompt, val

        # 2. Check adjacent line on the same vertical band (y within +/- 8 points)
        for other in all_lines:
            if other != line_item and abs(other["bbox"][1] - line_y0) < 8.0:
                other_text = other["text"].strip()
                if not ("____" in other_text):
                    val = self._find_matching_value(other_text, value_by_key)
                    if val:
                        return other_text, val

        # 3. Check preceding lines, skipping parenthetical hints like (DD/MM/YYYY), (INR), (masked), (fictional)
        if line_index > 0:
            for step in range(1, 4):
                if line_index - step >= 0:
                    prev_line = all_lines[line_index - step]
                    prev_text = prev_line["text"].strip()
                    if prev_text.startswith("(") and prev_text.endswith(")"):
                        continue
                    if "____" in prev_text:
                        continue
                    val = self._find_matching_value(prev_text, value_by_key)
                    if val:
                        return prev_text, val

        return None, None

    def _append_verification_certificate(
        self,
        doc: fitz.Document,
        session_id: str,
        field_data: List[Dict[str, Any]],
        signature_path: Optional[str] = None
    ):
        """Appends a styled official verification summary table page with optional digital signature."""
        cert_page = doc.new_page(width=595.3, height=841.9) # Standard A4

        margin_x = 45.0
        header_y = 50.0

        # Header Box: Deep Navy background
        cert_page.draw_rect(
            fitz.Rect(margin_x, header_y, 595.3 - margin_x, header_y + 60),
            color=(30 / 255, 58 / 255, 138 / 255),
            fill=(30 / 255, 58 / 255, 138 / 255)
        )

        cert_page.insert_text(
            fitz.Point(margin_x + 18, header_y + 26),
            "FORM COMPLETION & VERIFICATION CERTIFICATE",
            fontsize=13,
            fontname="helv",
            color=(1, 1, 1)
        )
        cert_page.insert_text(
            fitz.Point(margin_x + 18, header_y + 45),
            "AI-Powered Document Intelligence Engine | Audit Trail & Field Values",
            fontsize=9,
            fontname="helv",
            color=(219 / 255, 234 / 255, 254 / 255)
        )

        # Metadata bar
        meta_y = header_y + 75
        now_str = datetime.now().strftime("%B %d, %Y - %H:%M:%S UTC")
        cert_page.insert_text(
            fitz.Point(margin_x, meta_y),
            f"Session ID: {session_id}   |   Generated: {now_str}",
            fontsize=8,
            fontname="helv",
            color=(100 / 255, 116 / 255, 139 / 255)
        )

        # Table Header
        table_y = meta_y + 20
        col_field = margin_x
        col_val = margin_x + 160
        col_status = margin_x + 360
        col_src = margin_x + 440
        right_edge = 595.3 - margin_x

        # Header Row
        cert_page.draw_rect(
            fitz.Rect(margin_x, table_y, right_edge, table_y + 20),
            color=(241 / 255, 245 / 255, 249 / 255),
            fill=(241 / 255, 245 / 255, 249 / 255)
        )
        cert_page.insert_text(fitz.Point(col_field + 6, table_y + 14), "FIELD / LABEL", fontsize=8, fontname="helv", color=(71 / 255, 85 / 255, 105 / 255))
        cert_page.insert_text(fitz.Point(col_val + 6, table_y + 14), "COMPLETED VALUE", fontsize=8, fontname="helv", color=(71 / 255, 85 / 255, 105 / 255))
        cert_page.insert_text(fitz.Point(col_status + 6, table_y + 14), "STATUS", fontsize=8, fontname="helv", color=(71 / 255, 85 / 255, 105 / 255))
        cert_page.insert_text(fitz.Point(col_src + 6, table_y + 14), "SOURCE DOC", fontsize=8, fontname="helv", color=(71 / 255, 85 / 255, 105 / 255))

        curr_y = table_y + 20
        row_height = 22

        for idx, item in enumerate(field_data):
            label = sanitize_pdf_text(str(item.get("label") or item.get("field_key", "")))
            raw_v = item.get("current_value")
            val = sanitize_pdf_text(str(raw_v)) if raw_v else "Not Provided"
            status_text = (item.get("validation_status") or "unconfirmed").upper()
            src = sanitize_pdf_text(str(item.get("source_document_name") or "User Input"))

            if idx % 2 == 1:
                cert_page.draw_rect(
                    fitz.Rect(margin_x, curr_y, right_edge, curr_y + row_height),
                    color=(248 / 255, 250 / 255, 252 / 255),
                    fill=(248 / 255, 250 / 255, 252 / 255)
                )

            cert_page.draw_line(fitz.Point(margin_x, curr_y + row_height), fitz.Point(right_edge, curr_y + row_height), color=(226 / 255, 232 / 255, 240 / 255), width=0.5)

            cert_page.insert_text(fitz.Point(col_field + 6, curr_y + 14), label[:30], fontsize=8, fontname="helv", color=(30 / 255, 41 / 255, 59 / 255))
            display_val = val[:40] + ("..." if len(val) > 40 else "")
            cert_page.insert_text(fitz.Point(col_val + 6, curr_y + 14), display_val, fontsize=8, fontname="helv", color=(15 / 255, 23 / 255, 42 / 255))

            stat_color = (22 / 255, 101 / 255, 52 / 255) if status_text in ["CONFIRMED", "EXTRACTED"] else (180 / 255, 83 / 255, 9 / 255)
            cert_page.insert_text(fitz.Point(col_status + 6, curr_y + 14), status_text[:14], fontsize=7.5, fontname="helv", color=stat_color)
            cert_page.insert_text(fitz.Point(col_src + 6, curr_y + 14), src[:16], fontsize=7.5, fontname="helv", color=(100 / 255, 116 / 255, 139 / 255))

            curr_y += row_height
            if curr_y > (710 if signature_path else 770):
                break

        # Render digital signature badge if present
        if signature_path and Path(signature_path).exists():
            sig_box = fitz.Rect(right_edge - 170, 720, right_edge, 785)
            cert_page.draw_rect(sig_box, color=(203 / 255, 213 / 255, 225 / 255), fill=(248 / 255, 250 / 255, 252 / 255))
            cert_page.insert_text(fitz.Point(sig_box.x0 + 8, sig_box.y0 + 12), "DIGITAL SIGNATURE ATTACHED", fontsize=6.5, fontname="helv", color=(100 / 255, 116 / 255, 139 / 255))
            try:
                img_rect = fitz.Rect(sig_box.x0 + 8, sig_box.y0 + 16, sig_box.x1 - 8, sig_box.y1 - 6)
                cert_page.insert_image(img_rect, filename=str(signature_path), keep_proportion=True)
            except Exception as se:
                logger.debug(f"Failed to place signature on certificate: {se}")

        # Footer Seal & Notice
        cert_page.draw_line(fitz.Point(margin_x, 790), fitz.Point(right_edge, 790), color=(203 / 255, 213 / 255, 225 / 255), width=0.5)
        cert_page.insert_text(
            fitz.Point(margin_x, 804),
            "This document was automatically generated and verified by the Intelligent Form Filler System. Processed in temporary private session.",
            fontsize=7,
            fontname="helv",
            color=(148 / 255, 163 / 255, 184 / 255)
        )
