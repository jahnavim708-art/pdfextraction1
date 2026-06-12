import fitz
import requests
import os
import pandas as pd

pdf_path = r"C:\Users\Hello\Downloads\table.pdf"
doc = fitz.open(pdf_path)

output_folder = os.path.join(os.path.dirname(pdf_path), "cloud_tables")
os.makedirs(output_folder, exist_ok=True)

API_KEY = "helloworld"

all_rows = []

for i, page in enumerate(doc):
    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
    img_path = os.path.join(output_folder, f"page_{i+1}.png")
    pix.save(img_path)

    with open(img_path, "rb") as f:
        response = requests.post(
            "https://api.ocr.space/parse/image",
            files={"filename": f},
            data={
                "apikey": API_KEY,
                "language": "eng",
                "isTable": "true"
            }
        )

    result = response.json()

    if "ParsedResults" not in result:
        continue

    text = result["ParsedResults"][0]["ParsedText"]

    for line in text.split("\n"):
        if line.strip():
            all_rows.append(line.split("\t"))

df = pd.DataFrame(all_rows)

df.to_csv(os.path.join(output_folder, "all_pages.csv"), index=False, header=False)