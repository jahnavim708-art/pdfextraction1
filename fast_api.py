import pdfplumber
import json

pdf_file = r"C:\Users\Hello\Downloads\table.pdf"
all_rows = []

with pdfplumber.open(pdf_file) as pdf:
    for page in pdf.pages:
        tables = page.extract_tables()

        for table in tables:
            if table:
                all_rows.extend(table)

# Save output to file
with open("extracted_tables.json", "w", encoding="utf-8") as f:
    json.dump(all_rows, f, ensure_ascii=False, indent=2)

print(f"Saved {len(all_rows)} rows to extracted_tables.json")