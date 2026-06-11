from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pdfplumber
import base64
import tempfile
import os

app = FastAPI()


class PDFRequest(BaseModel):
    pdf_base64: str


@app.post("/extract-table")
async def extract_tables(request: PDFRequest):

    try:
        # -------------------------
        # Decode PDF
        # -------------------------
        pdf_bytes = base64.b64decode(request.pdf_base64)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
            temp_pdf.write(pdf_bytes)
            pdf_path = temp_pdf.name

        all_rows = []

        # -------------------------
        # Open PDF
        # -------------------------
        with pdfplumber.open(pdf_path) as pdf:

            for page in pdf.pages:

                # -------------------------
                # 1. Try LINE-BASED TABLES
                # -------------------------
                tables = page.extract_tables({
                    "vertical_strategy": "lines",
                    "horizontal_strategy": "lines"
                })

                # -------------------------
                # 2. Fallback: TEXT-BASED TABLES
                # -------------------------
                if not tables:
                    tables = page.extract_tables({
                        "vertical_strategy": "text",
                        "horizontal_strategy": "text",
                        "snap_tolerance": 3,
                        "join_tolerance": 3,
                        "intersection_tolerance": 5
                    })

                # -------------------------
                # 3. Process tables
                # -------------------------
                for table in tables:

                    if not table:
                        continue

                    for row in table:

                        if not row or not any(row):
                            continue

                        # clean None values
                        row = [c if c is not None else "" for c in row]

                        # remove junk rows
                        if len("".join(row).strip()) < 3:
                            continue

                        all_rows.append(row)

        # -------------------------
        # Cleanup temp file
        # -------------------------
        os.remove(pdf_path)

        # -------------------------
        # Validation
        # -------------------------
        if not all_rows:
            raise HTTPException(status_code=404, detail="No table data found")

        # -------------------------
        # Return JSON
        # -------------------------
        return {
            "status": "success",
            "total_rows": len(all_rows),
            "data": all_rows
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))