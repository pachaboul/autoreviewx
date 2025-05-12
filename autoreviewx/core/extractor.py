import fitz  # PyMuPDF
import os


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract all text from a PDF file."""
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"File not found: {pdf_path}")

    text = ""
    doc = fitz.open(pdf_path)
    for page in doc:
        text += page.get_text()
    doc.close()
    return text


def extract_metadata_from_text(text: str) -> dict:
    """Basic metadata extraction from full text."""
    lines = [line.strip() for line in text.split("\n") if line.strip()]

    metadata = {
        "title": lines[0] if lines else "",
        "authors": lines[1] if len(lines) > 1 else "",
        "abstract": "",
        "year": "",
        "keywords": []
    }

    # Optional: crude extraction of abstract
    for i, line in enumerate(lines):
        if "abstract" in line.lower():
            metadata["abstract"] = " ".join(lines[i + 1:i + 6])  # simple heuristic
            break

    return metadata
