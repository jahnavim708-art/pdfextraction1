from transformers import (
    DetrImageProcessor,
    TableTransformerForObjectDetection
)
from PIL import Image
import torch


class StructureDetector:

    def __init__(self):

        self.processor = DetrImageProcessor.from_pretrained(
            "microsoft/table-transformer-structure-recognition"
        )

        self.model = TableTransformerForObjectDetection.from_pretrained(
            "microsoft/table-transformer-structure-recognition"
        )

    def detect_structure(self, image):

        pil_img = Image.fromarray(image)

        inputs = self.processor(
            images=pil_img,
            return_tensors="pt"
        )

        outputs = self.model(**inputs)

        results = self.processor.post_process_object_detection(
            outputs,
            threshold=0.7,
            target_sizes=torch.tensor(
                [pil_img.size[::-1]]
            )
        )[0]

        return results