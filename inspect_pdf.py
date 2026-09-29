import fitz
import sys

file_path = r"C:\Users\Dev\Downloads\datatalk\PPT CONTENT\DataSaarthi_MicroProject_Progress_Report.pdf"
doc = fitz.open(file_path)

for page_num in range(len(doc)):
    page = doc[page_num]
    text_instances = page.search_for("Signature")
    if text_instances:
        print(f"Found 'Signature' on page {page_num + 1}:")
        for inst in text_instances:
            print(inst)
    
    text = page.get_text()
    for line in text.split('\n'):
        if 'Signature' in line or 'Mentor' in line or 'Head' in line:
            print(line.strip())
