from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pdfplumber
import pandas as pd
import base64
import tempfile
import os

app = FastAPI()


class PDFRequest(BaseModel):
    pdf_base64: str


@app.post("/extract-table")
async def pdf_to_json(request: PDFRequest):

    try:
        pdf_bytes = base64.b64decode(request.pdf_base64)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
            temp_pdf.write(pdf_bytes)
            pdf_path = temp_pdf.name

        all_rows = []
        header = None

        with pdfplumber.open(pdf_path) as pdf:

            for page in pdf.pages:

                tables = page.extract_tables()

                for table in tables:

                    if not table or len(table) < 2:
                        continue

                    # Set header only once
                    if header is None:
                        header = table[0]

                    for row in table[1:]:

                        if not any(row):
                            continue

                        # normalize row length
                        if header:
                            if len(row) < len(header):
                                row += [""] * (len(header) - len(row))
                            elif len(row) > len(header):
                                row = row[:len(header)]

                        all_rows.append(row)

        os.remove(pdf_path)

        if not all_rows or not header:
            raise HTTPException(status_code=404, detail="No table found")

        df = pd.DataFrame(all_rows, columns=header)
        df = df.fillna("")

        return {
            "total_rows": len(df),
            "data": df.to_dict(orient="records")
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))