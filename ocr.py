import pytesseract
from PIL import Image

def extract_text(image_path):
    """Extracts text from an image using OCR."""
    try:
        image = Image.open(image_path)
        return pytesseract.image_to_string(image)
    except Exception as e:
        return f"Error processing image: {str(e)}"
