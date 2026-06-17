from paddleocr import PaddleOCR


class OCREngine:

    def __init__(self):

        self.ocr = PaddleOCR(
            use_angle_cls=True,
            lang="en"
        )

    def extract(self, image):

        result = self.ocr.ocr(image)

        words = []

        for line in result[0]:

            words.append({
                "bbox": line[0],
                "text": line[1][0]
            })

        return words