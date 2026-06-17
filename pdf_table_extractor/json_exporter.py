import json


class JSONExporter:

    def __init__(self):
        # Store header once for entire PDF
        self.columns = None

    def center_x(self, bbox):
        return sum(p[0] for p in bbox) / 4

    def convert(self, rows):

        if not rows or len(rows) < 2:
            return []

        output = []

        # ----------------------------
        # STEP 1: Build header ONCE
        # ----------------------------
        if self.columns is None:

            header_row = rows[0]
            self.columns = []

            for cell in header_row["cells"]:
                self.columns.append({
                    "name": cell["text"],
                    "x": self.center_x(cell["bbox"])
                })

            self.columns.sort(key=lambda x: x["x"])

        # ----------------------------
        # STEP 2: Convert rows
        # ----------------------------
        for row in rows[1:]:

            record = {
                col["name"]: ""
                for col in self.columns
            }

            for cell in row["cells"]:

                cell_x = self.center_x(cell["bbox"])

                nearest = min(
                    self.columns,
                    key=lambda c: abs(c["x"] - cell_x)
                )

                if record[nearest["name"]]:
                    record[nearest["name"]] += " " + cell["text"]
                else:
                    record[nearest["name"]] = cell["text"]

            output.append(record)

        return output

    def save(self, data, path):

        with open(path, "w", encoding="utf-8") as f:
            json.dump(
                data,
                f,
                indent=4,
                ensure_ascii=False
            )