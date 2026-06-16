import pdfplumber
import json
import re
from collections import defaultdict
output = []

pdf_file = r"C:\Users\Hello\Downloads\table.pdf"


# =====================================================
# FILTER: reject non-table header rows (IMPORTANT FIX)
# =====================================================
def is_table_header(row_words):

    text = " ".join(w["text"] for w in row_words).lower()

    # reject statement metadata / titles
    if "statement" in text and "period" in text:
        return False

    if "account statement" in text:
        return False

    if "as on" in text:
        return False

    if len(row_words) < 4:
        return False

    return True


# =====================================================
# BUILD COLUMNS (PURELY GEOMETRIC)
# =====================================================
def build_columns(header_words):

    header_words = sorted(header_words, key=lambda x: x["x0"])

    columns = []

    current_name = header_words[0]["text"].strip()
    current_x = header_words[0]["x0"]

    for i in range(1, len(header_words)):

        prev = header_words[i - 1]
        curr = header_words[i]

        gap = curr["x0"] - prev["x1"]

        if gap < 10:
            current_name += " " + curr["text"].strip()
        else:
            columns.append({"name": current_name, "x": current_x})
            current_name = curr["text"].strip()
            current_x = curr["x0"]

    columns.append({"name": current_name, "x": current_x})

    return columns


# =====================================================
# COLUMN MATCHING
# =====================================================
def nearest_column(x, columns):
    return min(columns, key=lambda c: abs(x - c["x"]))["name"]


date_pattern = re.compile(r"\d{2}/\d{2}/\d{4}")


# =====================================================
# MAIN
# =====================================================
with pdfplumber.open(pdf_file) as pdf:

    columns = None
    header_text = None
    current_record = None

    for page in pdf.pages:

        words = page.extract_words()

        # group words into rows
        rows = defaultdict(list)

        for w in words:
            rows[round(w["top"])].append(w)

        sorted_rows = sorted(rows.items())

        # =================================================
        # HEADER DETECTION (FIXED)
        # =================================================
        if columns is None:

            best_row = None
            best_score = 0

            for _, row_words in sorted_rows:

                row_words = sorted(row_words, key=lambda x: x["x0"])

                if not is_table_header(row_words):
                    continue

                x_positions = [w["x0"] for w in row_words]

                if len(x_positions) < 4:
                    continue

                spread = max(x_positions) - min(x_positions)

                gaps = [
                    x_positions[i] - x_positions[i - 1]
                    for i in range(1, len(x_positions))
                ]

                score = spread * len(row_words)

                if score > best_score:
                    best_score = score
                    best_row = row_words

            if best_row:

                columns = build_columns(best_row)

                header_text = " ".join(w["text"] for w in best_row)

                print("\nDetected Columns:\n")
                for c in columns:
                    print(c)

        if columns is None:
            continue

        # =================================================
        # ROW PROCESSING
        # =================================================
        for _, row_words in sorted_rows:

            row_words = sorted(row_words, key=lambda x: x["x0"])

            row_text = " ".join(w["text"] for w in row_words)

            # skip header row
            if header_text and row_text.strip() == header_text.strip():
                continue

            row_data = {}

            for word in row_words:

                col = nearest_column(word["x0"], columns)

                row_data.setdefault(col, []).append(word["text"])

            row_data = {
                k: " ".join(v)
                for k, v in row_data.items()
            }

            # =================================================
            # TRANSACTION DETECTION (ONLY DATE BASED)
            # =================================================
            first_col = columns[0]["name"]

            if (
                first_col in row_data
                and date_pattern.search(row_data[first_col])
            ):

                if current_record:
                    output.append(current_record)

                current_record = {c["name"]: "" for c in columns}
                current_record.update(row_data)

            else:

                # continuation row merge
                if current_record:

                    for k, v in row_data.items():

                        if v.strip():

                            if current_record[k]:
                                current_record[k] += " "

                            current_record[k] += v

    if current_record:
        output.append(current_record)


# =====================================================
# SAVE OUTPUT
# =====================================================
with open("structured_output.json", "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print(f"\nSaved {len(output)} transactions")