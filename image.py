import fitz
import os

pdf_file = r"C:\Users\Hello\Downloads\table.pdf"
output_dir = "output_images"

os.makedirs(output_dir, exist_ok=True)

doc = fitz.open(pdf_file)

for page_num in range(len(doc)):
    page = doc[page_num]

    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
    image_path = os.path.join(output_dir, f"page_{page_num + 1}.png")

    pix.save(image_path)
    print(f"Saved: {image_path}")

doc.close()