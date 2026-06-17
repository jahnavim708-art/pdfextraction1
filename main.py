from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pdfplumber
import base64
import tempfile
import os
import numpy as np
import re

app = FastAPI()


class PDFRequest(BaseModel):
    file_name: str
    pdf_base64: str


# ----------------------------
# CLEAN PDF TEXT (CID FIX)
# ----------------------------
def clean_text(text: str):

    if not text:
        return ""

    # remove CID artifacts like (cid:9)
    text = re.sub(r"\(cid:\d+\)", "", text)

    # remove non-printable junk
    text = re.sub(r"[^\x20-\x7E\n]", " ", text)

    # normalize spaces
    text = re.sub(r"\s+", " ", text)

    return text.strip()


# ----------------------------
# KV extractor
# ----------------------------
def extract_kv_from_line(line: str):

    if ":" not in line:
        return None, None

    key, value = line.split(":", 1)

    key = key.strip()
    value = value.strip()

    if not key or not value:
        return None, None

    if len(key) > 80:
        return None, None

    return key, value


@app.post("/extract-table")
async def pdf_to_csv(request: PDFRequest):

    try:
        pdf_bytes = base64.b64decode(request.pdf_base64)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
            temp_pdf.write(pdf_bytes)
            pdf_path = temp_pdf.name

        table_data = []
        outside_data = {}   # ONLY ONCE

        with pdfplumber.open(pdf_path) as pdf:

            for page in pdf.pages:

                # ----------------------------
                # TABLE EXTRACTION
                # ----------------------------
                table = page.extract_table()

                if table:
                    if not table_data:
                        table_data.extend(table)
                    else:
                        table_data.extend(table[1:])

                # ----------------------------
                # OUTSIDE DATA (CLEANED)
                # ----------------------------
                page_text = clean_text(page.extract_text())

                words = page.extract_words()
                tables = page.find_tables()

                table_bbox = tables[0].bbox if tables else None

                lines_map = {}

                for w in words:

                    x0 = w["x0"]
                    x1 = w["x1"]
                    top = w["top"]
                    text = w["text"]

                    # skip table region
                    if table_bbox:
                        tx0, ty0, tx1, ty1 = table_bbox

                        if (x0 >= tx0 and x1 <= tx1 and
                            top >= ty0 and top <= ty1):
                            continue

                    key = round(top, 1)

                    if key not in lines_map:
                        lines_map[key] = []

                    lines_map[key].append((x0, text))

                # rebuild clean lines
                for _, words_line in sorted(lines_map.items()):

                    words_line.sort(key=lambda x: x[0])

                    line = " ".join([w[1] for w in words_line])

                    line = clean_text(line)

                    k, v = extract_kv_from_line(line)

                    if k and v:
                        outside_data[k] = v   # ONLY ONCE

        os.remove(pdf_path)

        if not table_data:
            raise HTTPException(status_code=404, detail="No table found")

        # ----------------------------
        # TABLE → JSON
        # ----------------------------
        rows = [r for r in table_data if isinstance(r, list)]

        headers = rows[0]
        data_rows = rows[1:]

        json_data = []

        for row in data_rows:

            obj = {}

            for i, col in enumerate(headers):
                obj[col] = row[i] if i < len(row) else ""

            json_data.append(obj)

        # clean NaN
        for r in json_data:
            for k, v in r.items():
                if v is None or (isinstance(v, float) and np.isnan(v)):
                    r[k] = ""

        return {
            "status": "success",
            "file_name": request.file_name,
            #"table_data": json_data,
            "outside_data": outside_data,
            "table_data": json_data
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))