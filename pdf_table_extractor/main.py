import os
import cv2
from pdf_loader import PDFLoader
from table_detector import TableDetector
from ocr_engine import OCREngine
from table_reconstructor import TableReconstructor
from json_exporter import JSONExporter


def merge_multiline_rows(records):
    """
    Generic multiline row merger.

    Assumption:
    A new record starts when the first non-empty column appears.
    Continuation rows usually have the first column empty.
    """

    if not records:
        return []

    columns = list(records[0].keys())

    if not columns:
        return records

    first_column = columns[0]

    merged = []
    current = None

    for row in records:

        first_value = str(
            row.get(first_column, "")
        ).strip()

        # New logical row
        if first_value:

            if current:
                merged.append(current)

            current = row.copy()

        # Continuation row
        else:

            if current is None:
                continue

            for key, value in row.items():

                value = str(value).strip()

                if not value:
                    continue

                existing = str(
                    current.get(key, "")
                ).strip()

                if existing:
                    current[key] = (
                        existing + " " + value
                    )
                else:
                    current[key] = value

    if current:
        merged.append(current)

    return merged


def main():

    os.makedirs("output", exist_ok=True)
    os.makedirs("debug", exist_ok=True)

    pdf = PDFLoader()

    detector = TableDetector()

    ocr = OCREngine()

    reconstructor = TableReconstructor()

    exporter = JSONExporter()

    pdf_path = r"C:\Users\Hello\Downloads\table.pdf"

    pages = pdf.load_pdf(pdf_path)

    # DEBUG
    #pages = pages[:1]

    print(
        f"\nTotal pages being processed: "
        f"{len(pages)}"
    )

    all_records = []

    for page_idx, page in enumerate(pages):

        print("\n" + "=" * 60)
        print(
            f"PAGE "
            f"{page_idx + 1}/{len(pages)}"
        )
        print("=" * 60)

        tables = detector.detect(page)

        print(
            f"Tables found: "
            f"{len(tables)}"
        )

        for i, box in enumerate(tables[:10]):
            print(f"Table Box {i}: {box}")

        for table_idx, table_box in enumerate(tables):

            print(
                f"\nProcessing table "
                f"{table_idx+1}/{len(tables)}"
            )

            try:

                x1, y1, x2, y2 = map(int, table_box)

                # 👉 ADD PADDING HERE
                pad = 15

                x1 = max(0, x1 - pad)
                y1 = max(0, y1 - pad)
                x2 = min(page.shape[1], x2 + pad)
                y2 = min(page.shape[0], y2 + pad)

                table_img = page[y1:y2, x1:x2]
                table_img = cv2.copyMakeBorder( table_img, 10, 10, 10, 10, cv2.BORDER_CONSTANT, value=(255, 255, 255) )
                if table_img.size == 0:

                    print(
                        "Empty crop, skipping."
                    )

                    continue

                words = ocr.extract(
                    table_img
                )

                print(
                    f"OCR words: "
                    f"{len(words)}"
                )

                rows = reconstructor.build_table(
                    words
                )

                print(
                    f"Rows reconstructed: "
                    f"{len(rows)}"
                )

                json_rows = exporter.convert(
                    rows
                )

                print(
                    f"JSON rows before merge: "
                    f"{len(json_rows)}"
                )

                json_rows = merge_multiline_rows(
                    json_rows
                )

                print(
                    f"JSON rows after merge: "
                    f"{len(json_rows)}"
                )

                if json_rows:

                    print(
                        "\nSample Record:"
                    )

                    print(
                        json_rows[0]
                    )

                all_records.extend(
                    json_rows
                )

            except Exception as e:

                print(
                    f"Error processing "
                    f"table "
                    f"{table_idx+1}: {e}"
                )

    output_file = "output/result.json"

    exporter.save(
        all_records,
        output_file
    )

    print("\n" + "=" * 60)
    print("PROCESS COMPLETED")
    print("=" * 60)

    print(
        f"Records extracted: "
        f"{len(all_records)}"
    )

    print(
        f"Saved: "
        f"{output_file}"
    )


if __name__ == "__main__":
    main()