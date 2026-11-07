import logging
import os
import shutil
from pathlib import Path
from typing import Dict, Any, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

class TesseractOCRService:
    """Handles image preprocessing with OpenCV and text extraction using Tesseract OCR."""

    def __init__(self, custom_tesseract_cmd: Optional[str] = None):
        self.tesseract_cmd = custom_tesseract_cmd or settings.TESSERACT_CMD
        self._check_tesseract_available()

    def _check_tesseract_available(self) -> bool:
        # Check standard installation locations on Windows if default command isn't in PATH
        possible_paths = [
            self.tesseract_cmd,
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Programs\Tesseract-OCR\tesseract.exe"),
        ]
        
        found = False
        for path in possible_paths:
            if shutil.which(path) or (os.path.exists(path) and os.path.isfile(path)):
                self.tesseract_cmd = path
                found = True
                break

        if not found:
            logger.warning(
                "Tesseract OCR executable not detected at standard locations. "
                "Image-based OCR will report unavailable status. Digital PDF extraction remains unaffected."
            )
        return found

    def _check_rapidocr_available(self) -> bool:
        try:
            import rapidocr_onnxruntime
            return True
        except ImportError:
            return False

    def is_available(self) -> bool:
        return self._check_tesseract_available() or self._check_rapidocr_available()

    def preprocess_image(self, image_path: Path) -> Any:
        """Applies grayscale, thresholding, and noise reduction using OpenCV."""
        try:
            import cv2
            import numpy as np

            # Read image
            img = cv2.imread(str(image_path))
            if img is None:
                raise ValueError(f"Could not load image at {image_path}")

            # Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            # Noise reduction with median filter
            denoised = cv2.medianBlur(gray, 3)

            # Adaptive or Otsu thresholding
            _, thresh = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            return thresh
        except Exception as e:
            logger.warning(f"OpenCV image preprocessing skipped due to error: {e}")
            from PIL import Image
            return Image.open(str(image_path))

    def extract_text_from_image(self, image_path: Path) -> Dict[str, Any]:
        """Runs OCR on the given image with confidence calculation."""
        # Try Tesseract if binary is available
        if self._check_tesseract_available():
            try:
                import pytesseract
                pytesseract.pytesseract.tesseract_cmd = self.tesseract_cmd
                
                # Preprocess
                processed_img = self.preprocess_image(image_path)
                
                # Extract text
                raw_text = pytesseract.image_to_string(processed_img, config="--psm 1")
                
                # Extract confidence data
                data = pytesseract.image_to_data(processed_img, output_type=pytesseract.Output.DICT)
                confidences = [int(conf) for conf in data["conf"] if conf != "-1"]
                avg_confidence = (sum(confidences) / len(confidences) / 100.0) if confidences else 0.85

                if raw_text.strip():
                    return {
                        "text": raw_text.strip(),
                        "confidence": round(avg_confidence, 2),
                        "status": "completed",
                        "extraction_method": "ocr_tesseract",
                    }
            except Exception as e:
                logger.warning(f"Tesseract OCR attempt failed, checking fallback: {e}")

        # Fallback to pure ONNX RapidOCR
        if self._check_rapidocr_available():
            try:
                from rapidocr_onnxruntime import RapidOCR
                engine = RapidOCR()
                result, _ = engine(str(image_path))
                if result:
                    lines = [str(item[1]) for item in result]
                    confs = [float(item[2]) for item in result if len(item) > 2]
                    avg_conf = (sum(confs) / len(confs)) if confs else 0.92
                    return {
                        "text": "\n".join(lines).strip(),
                        "confidence": round(avg_conf, 2),
                        "status": "completed",
                        "extraction_method": "ocr_rapidocr",
                    }
            except Exception as e:
                logger.error(f"RapidOCR extraction failed on {image_path}: {e}")

        return {
            "text": "",
            "confidence": 0.0,
            "status": "unavailable",
            "error": "OCR engine not available."
        }

    def extract_text_and_coordinates(self, image_path: Path) -> Dict[str, Any]:
        """Extracts text along with bounding box coordinates for each word/line."""
        # Try Tesseract if binary is available
        if self._check_tesseract_available():
            try:
                import pytesseract
                pytesseract.pytesseract.tesseract_cmd = self.tesseract_cmd
                processed_img = self.preprocess_image(image_path)
                data = pytesseract.image_to_data(processed_img, output_type=pytesseract.Output.DICT)
                n_boxes = len(data["text"])
                word_boxes = []
                words = []
                for i in range(n_boxes):
                    text = data["text"][i].strip()
                    conf_val = data["conf"][i]
                    conf = int(conf_val) if str(conf_val).lstrip("-").isdigit() else -1
                    if text and conf > 25:
                        words.append(text)
                        word_boxes.append({
                            "text": text,
                            "x": int(data["left"][i]),
                            "y": int(data["top"][i]),
                            "width": int(data["width"][i]),
                            "height": int(data["height"][i]),
                            "confidence": round(conf / 100.0, 2),
                        })
                if words:
                    full_text = " ".join(words)
                    return {
                        "text": full_text,
                        "word_boxes": word_boxes,
                        "confidence": 0.88,
                        "status": "completed",
                        "extraction_method": "ocr_tesseract_coordinates"
                    }
            except Exception as e:
                logger.warning(f"Tesseract coordinate extraction failed, trying RapidOCR: {e}")

        # Fallback to RapidOCR for bounding boxes
        if self._check_rapidocr_available():
            try:
                from rapidocr_onnxruntime import RapidOCR
                engine = RapidOCR()
                result, _ = engine(str(image_path))
                if result:
                    word_boxes = []
                    words = []
                    for item in result:
                        pts = item[0]  # [[x1, y1], [x2, y1], [x2, y2], [x1, y2]]
                        txt = str(item[1]).strip()
                        conf = float(item[2]) if len(item) > 2 else 0.90
                        if txt:
                            xs = [p[0] for p in pts]
                            ys = [p[1] for p in pts]
                            x_min, x_max = min(xs), max(xs)
                            y_min, y_max = min(ys), max(ys)
                            words.append(txt)
                            word_boxes.append({
                                "text": txt,
                                "x": int(round(x_min)),
                                "y": int(round(y_min)),
                                "width": int(round(x_max - x_min)),
                                "height": int(round(y_max - y_min)),
                                "confidence": round(conf, 2),
                            })
                    return {
                        "text": "\n".join(words),
                        "word_boxes": word_boxes,
                        "confidence": 0.92,
                        "status": "completed",
                        "extraction_method": "ocr_rapidocr_coordinates"
                    }
            except Exception as e:
                logger.error(f"RapidOCR coordinate extraction failed: {e}")

        return {
            "text": "",
            "word_boxes": [],
            "confidence": 0.0,
            "status": "failed",
            "error": "OCR engine unavailable."
        }
