# extracts text from pdf path

import pypdf
# from typing import str 

def extract_text_from_pdf(pdf_path: str) -> str:
    """
    pdf takes file path and converts into readable text format
    """
    # pdf reader object
    reader = pypdf.PdfReader(pdf_path)
    
    extracted_text = []
    
    # loop to iterate line by line in every page
    for page_num, page in enumerate(reader.pages):
        # extract text of current page
        page_text = page.extract_text()
        if page_text:
            # 
            extracted_text.append(f"--- Page {page_num + 1} ---\n" + page_text.strip())
            
    # joining all pages text as single formatted string
    full_text = "\n\n".join(extracted_text)
    return full_text

if __name__ == "__main__":
    # example
    sample_pdf = "sample_paper.pdf"
    try:
        text = extract_text_from_pdf(sample_pdf)
        print(f"Extracted {len(text)} characters successfully!")
    except Exception as e:
        print(f"Test Run Warning: {e}. Provide a valid PDF to extract.")
        
    