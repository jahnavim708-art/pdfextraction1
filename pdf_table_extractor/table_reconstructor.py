class TableReconstructor:

    def center_x(self, bbox):
        return sum(p[0] for p in bbox) / 4

    def center_y(self, bbox):
        return sum(p[1] for p in bbox) / 4

    def build_table(self, words):

        rows = []

        words = sorted(
            words,
            key=lambda x: self.center_y(x["bbox"])
        )

        tolerance = 20

        for word in words:

            y = self.center_y(word["bbox"])

            found = False

            for row in rows:

                if abs(row["y"] - y) < tolerance:
                    row["cells"].append(word)
                    found = True
                    break

            if not found:
                rows.append({
                    "y": y,
                    "cells": [word]
                })

        return rows