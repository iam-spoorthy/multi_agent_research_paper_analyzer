# extracts text from pdf path with smart chunking support for heavy PDFs

import pypdf
import urllib.request
import tempfile
import os
from typing import List

def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extracts readable text from PDF page by page.
    """
    reader = pypdf.PdfReader(pdf_path)
    extracted_text = []
    
    for page_num, page in enumerate(reader.pages):
        page_text = page.extract_text()
        if page_text:
            extracted_text.append(f"--- Page {page_num + 1} ---\n" + page_text.strip())
            
    full_text = "\n\n".join(extracted_text)
    return full_text

def download_and_extract_pdf_from_url(url: str) -> str:
    """
    Downloads a PDF from a URL (e.g. arXiv URL or direct PDF URL) and extracts text.
    Handles arxiv abs URLs (e.g. arxiv.org/abs/... -> arxiv.org/pdf/...)
    """
    clean_url = url.strip()
    if "arxiv.org/abs/" in clean_url:
        clean_url = clean_url.replace("arxiv.org/abs/", "arxiv.org/pdf/") + ".pdf"
    elif not clean_url.endswith(".pdf") and "arxiv.org/pdf/" not in clean_url:
        # If it's a general URL, ensure we fetch it
        pass

    req = urllib.request.Request(
        clean_url, 
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    )
    with urllib.request.urlopen(req) as response:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(response.read())
            tmp_path = tmp.name

    try:
        text = extract_text_from_pdf(tmp_path)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    return text


def chunk_text(text: str, max_chars: int = 12000) -> List[str]:
    """
    Splits long text into manageable chunks for heavy PDF processing.
    """
    if len(text) <= max_chars:
        return [text]
        
    chunks = []
    current_chunk = []
    current_length = 0
    
    paragraphs = text.split("\n\n")
    for para in paragraphs:
        if current_length + len(para) > max_chars and current_chunk:
            chunks.append("\n\n".join(current_chunk))
            current_chunk = [para]
            current_length = len(para)
        else:
            current_chunk.append(para)
            current_length += len(para)
            
    if current_chunk:
        chunks.append("\n\n".join(current_chunk))
        
    return chunks

if __name__ == "__main__":
    sample_pdf = "sample_paper.pdf"
    try:
        text = extract_text_from_pdf(sample_pdf)
        print(f"Extracted {len(text)} characters successfully!")
        chunks = chunk_text(text, 5000)
        print(f"Split into {len(chunks)} chunks for context window safety.")
    except Exception as e:
        print(f"Test Run Warning: {e}. Provide a valid PDF to extract.")