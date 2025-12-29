"""OCR utilities for image text extraction"""
from PIL import Image
import subprocess
from config import USE_EASYOCR, USE_GPU


# Initialize OCR engines
TESSERACT_AVAILABLE = False
EASYOCR_READER = None

# Check Tesseract availability
try:
    result = subprocess.run(
        ["tesseract", "--version"],
        capture_output=True,
        text=True,
        timeout=5
    )
    if result.returncode == 0:
        TESSERACT_AVAILABLE = True
        import pytesseract
        print("✅ Tesseract OCR is available")
except Exception:
    print("⚠️ Tesseract OCR not found. Install with: sudo apt install tesseract-ocr")

# Initialize EasyOCR if requested
if USE_EASYOCR:
    try:
        import easyocr
        EASYOCR_READER = easyocr.Reader(['en'], gpu=USE_GPU)
        print(f"✅ EasyOCR initialized (GPU: {USE_GPU})")
    except Exception as e:
        print(f"⚠️ EasyOCR initialization failed: {e}")
        print("   Falling back to Tesseract only")


def run_ocr_for_image(img_path):
    """
    Run OCR on an image using available engines
    
    Priority: EasyOCR (if enabled) -> Tesseract
    
    Args:
        img_path (str): Path to image file
        
    Returns:
        str: Extracted text or None
    """
    if img_path is None:
        return None

    # Try EasyOCR first if enabled
    if EASYOCR_READER is not None:
        try:
            result = EASYOCR_READER.readtext(img_path, detail=0)
            if result:
                return " ".join(result)
        except Exception as e:
            print(f"EasyOCR failed for {img_path}: {e}")

    # Fallback to Tesseract
    if TESSERACT_AVAILABLE:
        try:
            text = pytesseract.image_to_string(Image.open(img_path))
            return text.strip() if text.strip() else None
        except Exception as e:
            print(f"Tesseract failed for {img_path}: {e}")
            return None

    return None


def normalize_bbox(bbox, page_w, page_h):
    """Normalize BBOX values to 0-1 range"""
    if bbox is None:
        return None
    x0, y0, x1, y1 = bbox
    return [
        round(x0 / page_w, 6),
        round(y0 / page_h, 6),
        round(x1 / page_w, 6),
        round(y1 / page_h, 6),
    ]
