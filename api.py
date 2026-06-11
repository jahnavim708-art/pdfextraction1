import pdfplumber
import json
import re
pdf_file = r"C:\Users\Hello\Downloads\table.pdf"

output_data = []
last_columns = None

with pdfplumber.open(pdf_file) as pdf:
    for page in pdf.pages:
        tables = page.extract_tables()

        for table in tables:

            if not table:
                continue

            first_row = table[0]

            # ==================================================
            # PROPER TABLE
            # ==================================================
            if len(first_row) > 1:

                # First proper table found -> store header
                if last_columns is None:
                    last_columns = [
                        str(col).replace("\n", " ").strip()
                        if col is not None else f"column{i+1}"
                        for i, col in enumerate(first_row)
                    ]

                    rows = table[1:]  # skip header row

                else:
                    # Check if current first row is actually the header again
                    current_header = [
                        str(col).replace("\n", " ").strip()
                        if col is not None else ""
                        for col in first_row
                    ]

                    if current_header == last_columns:
                        rows = table[1:]  # skip repeated header
                    else:
                        rows = table      # continuation page

                # Process rows using stored header
                for row in rows:

                    if not row:
                        continue

                    row = [
                        "" if v is None else str(v).replace("\n", " ").strip()
                        for v in row
                    ]

                    # Normalize row length
                    if len(row) < len(last_columns):
                        row.extend([""] * (len(last_columns) - len(row)))

                    row = row[:len(last_columns)]

                    record = {}

                    for col_name, value in zip(last_columns, row):
                        record[col_name] = value

                    output_data.append(record)

            # ==================================================
            # IMPROPER TABLE
            # ==================================================
            else:

                for row in table[1:]:

                    if not row or not row[0]:
                        continue

                    values = (
                        str(row[0])
                        .replace("\n", " ")
                        .split()
                    )
                    #values = re.split(r"\s{2,}", row[0].replace("\n", " "))

                    record = {}

                    for idx, value in enumerate(values, start=1):
                        record[f"column{idx}"] = value

                    output_data.append(record)

# ==================================================
# SAVE OUTPUT
# ==================================================
output_file = "structured_output.json"

with open(output_file, "w", encoding="utf-8") as f:
    json.dump(output_data, f, indent=2, ensure_ascii=False)

print(f"Saved {len(output_data)} records to {output_file}")