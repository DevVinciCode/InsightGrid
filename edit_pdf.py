import pymupdf
import os

file_path = r"C:\Users\Dev\Downloads\datatalk\PPT CONTENT\DataSaarthi_MicroProject_Progress_Report.pdf"
doc = pymupdf.open(file_path)

page = doc[2] # 3rd page

# Find exact text to move
mentor_text = "(Signature of Mentor)"
hod_text = "(Signature of the Head of the Department)"

mentor_instances = page.search_for(mentor_text)
hod_instances = page.search_for(hod_text)

# Redact the old text
for inst in mentor_instances:
    page.add_redact_annot(inst, fill=(1, 1, 1)) # white fill
for inst in hod_instances:
    page.add_redact_annot(inst, fill=(1, 1, 1))
    
page.apply_redactions()

page_width = page.rect.width

font_size = 11
page.insert_text((page_width - 200, 650), mentor_text, fontsize=font_size, fontname="helv", color=(0, 0, 0))
page.insert_text((page_width - 250, 750), hod_text, fontsize=font_size, fontname="helv", color=(0, 0, 0))

temp_path = r"C:\Users\Dev\Downloads\datatalk\PPT CONTENT\temp.pdf"
doc.save(temp_path)
doc.close()

# Replace original file
os.replace(temp_path, file_path)
print("Updated the original file:", file_path)
