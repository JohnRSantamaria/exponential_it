import fitz  # PyMuPDF
from pdf2image import convert_from_bytes
import pytesseract


def is_scanned_pdf_from_bytes(file_bytes: bytes) -> bool:
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    for i, page in enumerate(doc):
        text = page.get_text("text").strip()
        print(f"[Página {i}] Texto detectado: '{text}'")
        if text:
            return False
    return True


def extract_text_with_tesseract(file_bytes: bytes, lang: str = "spa") -> str:
    images = convert_from_bytes(file_bytes, dpi=300)
    full_text = ""
    for img in images:
        full_text += pytesseract.image_to_string(img, lang=lang)
    return full_text.strip()


async def extract_ocr_payload(file, file_content: bytes):
    # Primero intentamos con Taggun si no es escaneado
    if not is_scanned_pdf_from_bytes(file_content):
        # return await extract_with_taggun(file=file, file_content=file_content)
        pass

    # Fallback: Tesseract
    print(f"⚠️ PDF escaneado detectado: usando Tesseract para {file.filename}")
    ocr_text = extract_text_with_tesseract(file_content)

    return {"text": {"text": ocr_text}, "meta": {"fallback": "tesseract"}}
