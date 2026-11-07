import logging
from pathlib import Path
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class DOCXProcessor:
    """Extracts text, tables, and structural sections from DOCX files."""

    def __init__(self, file_path: str):
        self.file_path = Path(file_path)

    def extract_text_and_tables(self) -> Dict[str, Any]:
        """
        Parses paragraphs and tabular cells from a .docx file.
        """
        try:
            import docx
            doc = docx.Document(str(self.file_path))
            
            paragraphs = []
            for p in doc.paragraphs:
                text = p.text.strip()
                if text:
                    paragraphs.append(text)

            tables_data = []
            for table_idx, table in enumerate(doc.tables):
                table_rows = []
                for row in table.rows:
                    row_cells = [cell.text.strip() for cell in row.cells]
                    table_rows.append(row_cells)
                tables_data.append({
                    "table_index": table_idx + 1,
                    "rows": table_rows
                })

            full_text = "\n".join(paragraphs)
            if tables_data:
                table_text_lines = []
                for t in tables_data:
                    for row in t["rows"]:
                        table_text_lines.append(" | ".join(row))
                full_text += "\n\nTables:\n" + "\n".join(table_text_lines)

            return {
                "page_count": 1, # DOCX does not have fixed pagination without rendering engine
                "paragraphs": paragraphs,
                "tables": tables_data,
                "full_text": full_text,
                "extraction_method": "docx_parser"
            }
        except Exception as e:
            logger.error(f"Failed to parse DOCX file {self.file_path}: {e}")
            raise e
