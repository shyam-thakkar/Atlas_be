import os
from io import BytesIO
from pdfminer.high_level import extract_text as extract_pdf_text
import docx

def extract_text_from_file(file_obj, file_extension):
    """
    Extracts text from PDF or DOCX file object.
    """
    text = ""
    try:
        if file_extension.lower() == '.pdf':
            # PDFMiner expects a path or file-like object
            text = extract_pdf_text(file_obj)
        elif file_extension.lower() in ['.docx', '.doc']:
            # python-docx requires a file-like object
            doc = docx.Document(file_obj)
            full_text = []
            for para in doc.paragraphs:
                full_text.append(para.text)
            text = '\n'.join(full_text)
        else:
            raise ValueError("Unsupported file type")
        
        # Basic cleaning
        return clean_text(text)
    except Exception as e:
        print(f"Extraction error: {e}")
        return ""

def clean_text(text):
    """
    Removes extra whitespace and cleans up the text.
    """
    if not text:
        return ""
    
    # Split by lines, strip whitespace, remove empty lines
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return '\n'.join(lines)
