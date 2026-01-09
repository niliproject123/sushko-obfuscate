"""
Hebrew PDF Text Extractor with OCR Support

Handles both:
1. Text-based PDFs (embedded text layer)
2. Image-based PDFs (scanned documents) - requires OCR

Dependencies:
    pip install pymupdf pdfplumber easyocr pdf2image Pillow

System dependency (for pdf2image):
    Ubuntu/Debian: apt-get install poppler-utils
    macOS: brew install poppler
    Windows: Download from https://github.com/osber/poppler-windows/releases
"""

import sys
import json
from pathlib import Path

# Core PDF libraries
import fitz  # pymupdf
import pdfplumber


def extract_with_pymupdf(pdf_path: str) -> str:
    """
    PyMuPDF extraction - for PDFs with embedded text.
    Fast, handles Hebrew well.
    """
    doc = fitz.open(pdf_path)
    full_text = []
    
    for page_num, page in enumerate(doc):
        full_text.append(f"\n{'='*50}")
        full_text.append(f"PAGE {page_num + 1}")
        full_text.append(f"{'='*50}\n")
        full_text.append(page.get_text())
    
    doc.close()
    return "\n".join(full_text)


def extract_with_pdfplumber(pdf_path: str) -> str:
    """
    pdfplumber extraction - better for structured layouts/tables.
    """
    full_text = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            full_text.append(f"\n{'='*50}")
            full_text.append(f"PAGE {page_num + 1}")
            full_text.append(f"{'='*50}\n")
            text = page.extract_text()
            if text:
                full_text.append(text)
    
    return "\n".join(full_text)


def extract_with_ocr(pdf_path: str, languages: list = None) -> str:
    """
    OCR extraction - for scanned/image-based PDFs.
    Uses EasyOCR with Hebrew + English support.
    
    Args:
        pdf_path: Path to PDF file
        languages: List of language codes (default: ['he', 'en'])
    
    Returns:
        Extracted text from all pages
    """
    try:
        import easyocr
        from pdf2image import convert_from_path
        import numpy as np
    except ImportError as e:
        raise ImportError(
            f"OCR dependencies not installed: {e}\n"
            "Run: pip install easyocr pdf2image Pillow\n"
            "Also install poppler-utils (system package)"
        )
    
    if languages is None:
        languages = ['he', 'en']
    
    # Initialize OCR reader (downloads models on first run)
    print(f"Initializing EasyOCR with languages: {languages}", file=sys.stderr)
    reader = easyocr.Reader(languages, gpu=False)
    
    # Convert PDF pages to images
    print(f"Converting PDF to images...", file=sys.stderr)
    images = convert_from_path(pdf_path, dpi=300)
    
    full_text = []
    for page_num, image in enumerate(images):
        full_text.append(f"\n{'='*50}")
        full_text.append(f"PAGE {page_num + 1}")
        full_text.append(f"{'='*50}\n")
        
        print(f"OCR processing page {page_num + 1}/{len(images)}...", file=sys.stderr)
        
        # Convert PIL Image to numpy array for EasyOCR
        image_np = np.array(image)
        
        # Run OCR
        results = reader.readtext(image_np)
        
        # Extract text from results: [(bbox, text, confidence), ...]
        page_text = "\n".join([text for _, text, _ in results])
        full_text.append(page_text)
    
    return "\n".join(full_text)


def extract_tables_pdfplumber(pdf_path: str) -> list:
    """
    Extract tables specifically using pdfplumber.
    Returns list of tables per page.
    """
    all_tables = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            tables = page.extract_tables()
            if tables:
                all_tables.append({
                    "page": page_num + 1,
                    "tables": tables
                })
    
    return all_tables


def has_text_layer(pdf_path: str) -> bool:
    """
    Check if PDF has extractable text or is image-based.
    Returns True if text layer exists, False if OCR needed.
    """
    doc = fitz.open(pdf_path)
    total_text = ""
    
    for page in doc:
        total_text += page.get_text().strip()
    
    doc.close()
    
    # If very little text found, likely image-based
    return len(total_text) > 50


def smart_extract(pdf_path: str, force_ocr: bool = False) -> str:
    """
    Automatically choose extraction method based on PDF type.
    
    Args:
        pdf_path: Path to PDF file
        force_ocr: Force OCR even if text layer exists
    
    Returns:
        Extracted text
    """
    if force_ocr:
        print("Forcing OCR extraction...", file=sys.stderr)
        return extract_with_ocr(pdf_path)
    
    if has_text_layer(pdf_path):
        print("Text layer detected, using PyMuPDF...", file=sys.stderr)
        return extract_with_pymupdf(pdf_path)
    else:
        print("No text layer, using OCR...", file=sys.stderr)
        return extract_with_ocr(pdf_path)


def extract_to_dict(pdf_path: str, use_ocr: bool = False) -> dict:
    """
    Extract all content into structured dict.
    
    Args:
        pdf_path: Path to PDF file
        use_ocr: Use OCR for text extraction
    """
    doc = fitz.open(pdf_path)
    
    result = {
        "metadata": doc.metadata,
        "page_count": len(doc),
        "has_text_layer": has_text_layer(pdf_path),
        "pages": []
    }
    
    if use_ocr:
        # OCR extraction
        try:
            import easyocr
            from pdf2image import convert_from_path
            import numpy as np
            
            reader = easyocr.Reader(['he', 'en'], gpu=False)
            images = convert_from_path(pdf_path, dpi=300)
            
            for page_num, image in enumerate(images):
                image_np = np.array(image)
                ocr_results = reader.readtext(image_np)
                page_text = "\n".join([text for _, text, _ in ocr_results])
                
                page_data = {
                    "page_number": page_num + 1,
                    "text": page_text,
                    "ocr_details": [
                        {"text": text, "confidence": conf, "bbox": bbox}
                        for bbox, text, conf in ocr_results
                    ]
                }
                result["pages"].append(page_data)
        except ImportError as e:
            raise ImportError(f"OCR dependencies not installed: {e}")
    else:
        # Standard extraction
        for page_num, page in enumerate(doc):
            page_data = {
                "page_number": page_num + 1,
                "text": page.get_text(),
                "blocks": page.get_text("blocks"),
            }
            result["pages"].append(page_data)
        
        # Add tables from pdfplumber
        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages):
                tables = page.extract_tables()
                if i < len(result["pages"]):
                    result["pages"][i]["tables"] = tables
    
    doc.close()
    return result


def main():
    """CLI interface"""
    if len(sys.argv) < 2:
        print("""
Hebrew PDF Text Extractor with OCR Support

Usage: python hebrew_pdf_extractor.py <pdf_path> [mode]

Modes:
    text      - Extract text using PyMuPDF (default)
    ocr       - Extract text using OCR (for scanned PDFs)
    smart     - Auto-detect: use OCR only if needed
    tables    - Extract tables only (pdfplumber)
    json      - Full structured extraction as JSON
    json-ocr  - Full structured extraction with OCR as JSON
    check     - Check if PDF has text layer

Examples:
    python hebrew_pdf_extractor.py document.pdf
    python hebrew_pdf_extractor.py scanned.pdf ocr
    python hebrew_pdf_extractor.py document.pdf smart
    python hebrew_pdf_extractor.py document.pdf json > output.json
        """)
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    mode = sys.argv[2] if len(sys.argv) > 2 else "text"
    
    if not Path(pdf_path).exists():
        print(f"Error: File not found: {pdf_path}", file=sys.stderr)
        sys.exit(1)
    
    if mode == "text":
        print(extract_with_pymupdf(pdf_path))
    
    elif mode == "ocr":
        print(extract_with_ocr(pdf_path))
    
    elif mode == "smart":
        print(smart_extract(pdf_path))
    
    elif mode == "tables":
        tables = extract_tables_pdfplumber(pdf_path)
        for page_data in tables:
            print(f"\n=== Page {page_data['page']} ===")
            for i, table in enumerate(page_data['tables']):
                print(f"\n--- Table {i+1} ---")
                for row in table:
                    print(row)
    
    elif mode == "json":
        data = extract_to_dict(pdf_path, use_ocr=False)
        print(json.dumps(data, ensure_ascii=False, indent=2))
    
    elif mode == "json-ocr":
        data = extract_to_dict(pdf_path, use_ocr=True)
        print(json.dumps(data, ensure_ascii=False, indent=2))
    
    elif mode == "check":
        has_text = has_text_layer(pdf_path)
        print(f"Has text layer: {has_text}")
        print(f"Recommendation: {'Use text mode' if has_text else 'Use ocr mode'}")
    
    else:
        print(f"Unknown mode: {mode}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
