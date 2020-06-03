from dataclasses import dataclass


@dataclass
class Payload:

    indices: list
    class_ids: list
    confidences: list
    boxes: list
