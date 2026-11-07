import logging
import uuid
import re
from pathlib import Path
from typing import Dict, Any, List, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

class DOCXGenerator:
    """Populates template DOCX forms with verified field values and emits completed documents."""

    def __init__(self, template_path: str):
        self.template_path = Path(template_path)

    def generate(
        self,
        session_id: str,
        field_data: List[Dict[str, Any]],
        font_family: str = "Calibri",
        font_size: float = 11.0,
        text_color: str = "#0f172a",
        signature_path: Optional[str] = None,
        output_dir: Optional[Path] = None
    ) -> str:
        out_directory = output_dir or settings.GENERATED_DIR
        out_directory.mkdir(parents=True, exist_ok=True)
        output_filename = f"completed_form_{session_id[:8]}_{uuid.uuid4().hex[:6]}.docx"
        output_path = out_directory / output_filename

        try:
            import docx
            from docx.shared import Inches, Pt, RGBColor
            from docx.enum.text import WD_ALIGN_PARAGRAPH

            doc = docx.Document(str(self.template_path))

            # Parse RGB color
            clean_hex = (text_color or "#0f172a").lstrip("#")
            r = int(clean_hex[0:2], 16) if len(clean_hex) == 6 else 15
            g = int(clean_hex[2:4], 16) if len(clean_hex) == 6 else 23
            b = int(clean_hex[4:6], 16) if len(clean_hex) == 6 else 42
            font_rgb = RGBColor(r, g, b)

            # Build replacement map
            val_map = {}
            for item in field_data:
                key = item.get("field_key")
                val = item.get("current_value")
                label = item.get("label") or key
                if val:
                    val_str = str(val).strip()
                    if key:
                        val_map[key.lower()] = val_str
                    if label:
                        val_map[label.lower()] = val_str

            # 1. Replace in paragraphs
            for p in doc.paragraphs:
                text_low = p.text.lower()
                for k, v in val_map.items():
                    if k in text_low and ("____" in p.text or ":" in p.text or "{{" in p.text):
                        if f"{{{{{k}}}}}" in p.text:
                            p.text = p.text.replace(f"{{{{{k}}}}}", v)
                        elif "____" in p.text:
                            p.text = re.sub(r"_{3,}", f" {v} ", p.text, count=1)
                        # Apply custom font styling to runs
                        for r_item in p.runs:
                            if font_family:
                                r_item.font.name = font_family
                            if font_size:
                                r_item.font.size = Pt(font_size)
                            r_item.font.color.rgb = font_rgb

            # 2. Replace in tables
            for table in doc.tables:
                for row in table.rows:
                    for i, cell in enumerate(row.cells):
                        cell_low = cell.text.lower()
                        for k, v in val_map.items():
                            if k in cell_low:
                                if i + 1 < len(row.cells) and (not row.cells[i+1].text.strip() or "____" in row.cells[i+1].text):
                                    row.cells[i+1].text = v
                                elif "____" in cell.text:
                                    cell.text = re.sub(r"_{3,}", f" {v} ", cell.text, count=1)

            # 3. Insert digital signature if provided
            if signature_path and Path(signature_path).exists():
                sig_p = doc.add_paragraph()
                sig_p.add_run("Digital Signature:\n").bold = True
                sig_p.add_run().add_picture(str(signature_path), width=Inches(1.8))

            # 4. Append Summary Table at the end
            doc.add_page_break()
            title_p = doc.add_paragraph("FORM COMPLETION & VERIFICATION SUMMARY")
            title_p.runs[0].font.size = Pt(14)
            title_p.runs[0].font.bold = True
            title_p.runs[0].font.color.rgb = RGBColor(30, 58, 138)

            table = doc.add_table(rows=1, cols=4)
            table.style = 'Table Grid'
            hdr_cells = table.rows[0].cells
            hdr_cells[0].text = "Field / Label"
            hdr_cells[1].text = "Completed Value"
            hdr_cells[2].text = "Status"
            hdr_cells[3].text = "Source Document"

            for cell in hdr_cells:
                for run in cell.paragraphs[0].runs:
                    run.font.bold = True

            for item in field_data:
                row_cells = table.add_row().cells
                row_cells[0].text = str(item.get("label") or item.get("field_key", ""))
                row_cells[1].text = str(item.get("current_value") or "Not Provided")
                row_cells[2].text = str(item.get("validation_status") or "unconfirmed").upper()
                row_cells[3].text = str(item.get("source_document_name") or "User Input")

            doc.save(str(output_path))
            logger.info(f"Generated completed DOCX to {output_path}")
            return str(output_path)

        except Exception as e:
            logger.error(f"Failed to generate completed DOCX: {e}")
            raise e
