from transformers import (
    DetrImageProcessor,
    TableTransformerForObjectDetection
)
from PIL import Image
import torch


class TableDetector:

    def __init__(self):

        self.processor = DetrImageProcessor.from_pretrained(
            "microsoft/table-transformer-detection"
        )

        self.model = TableTransformerForObjectDetection.from_pretrained(
            "microsoft/table-transformer-detection"
        )

    def detect(self, image):

        pil_img = Image.fromarray(image)

        inputs = self.processor(
            images=pil_img,
            return_tensors="pt"
        )

        outputs = self.model(**inputs)

        results = self.processor.post_process_object_detection(
            outputs,
            threshold=0.6,
            target_sizes=torch.tensor(
                [pil_img.size[::-1]]
            )
        )[0]

        tables = []

        for box in results["boxes"]:
            tables.append(box.tolist())

        return tables