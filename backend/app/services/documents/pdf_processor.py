import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class PDFProcessor:
    """Extracts text, metadata, form fields, and structure from PDF documents."""

    def __init__(self, file_path: str):
        self.file_path = Path(file_path)

    def extract_text_pages(self) -> List[Dict[str, Any]]:
        """
        Extracts text on a per-page basis.
        Attempts PyMuPDF first, then falls back to pypdf.
        """
        results = []
        
        # Try PyMuPDF (fitz)
        try:
            import fitz
            doc = fitz.open(str(self.file_path))
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text("text").strip()
                results.append({
                    "page_number": page_num + 1,
                    "text": text,
                    "has_selectable_text": len(text) > 30,
                    "extraction_method": "digital_pdf_pymupdf"
                })
            doc.close()
            return results
        except ImportError:
            pass
        except Exception as e:
            logger.warning(f"PyMuPDF text extraction failed: {e}. Falling back to pypdf.")

        # Fallback to pypdf
        try:
            from pypdf import PdfReader
            reader = PdfReader(str(self.file_path))
            for idx, page in enumerate(reader.pages):
                text = page.extract_text() or ""
                clean_text = text.strip()
                results.append({
                    "page_number": idx + 1,
                    "text": clean_text,
                    "has_selectable_text": len(clean_text) > 30,
                    "extraction_method": "digital_pdf_pypdf"
                })
            return results
        except Exception as e:
            logger.error(f"pypdf extraction failed for {self.file_path}: {e}")
            raise e

    def get_metadata(self) -> Dict[str, Any]:
        """Returns page count and fillable form field status."""
        try:
            from pypdf import PdfReader
            reader = PdfReader(str(self.file_path))
            fields = reader.get_fields()
            return {
                "page_count": len(reader.pages),
                "is_fillable": bool(fields),
                "field_names": list(fields.keys()) if fields else [],
            }
        except Exception as e:
            logger.warning(f"Could not read PDF metadata via pypdf: {e}")
            return {"page_count": 1, "is_fillable": False, "field_names": []}
