from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import Any, ClassVar, Optional
from dataclasses import dataclass
from numbers import Real
import cv2 as cv
import numpy as np
from util import cvimage as Image

def softmax(x):
    """Compute softmax values for each sets of scores in x."""
    e_x = np.exp(x - np.max(x))
    return e_x / e_x.sum(axis=0)

def get_vwvh(size):
    if isinstance(size, tuple):
        return (size[0] / 100, size[1] / 100)
    return (size.width / 100, size.height / 100)

@dataclass
class RegionOfInterest:
    template: Optional[Image.Image]
    bbox_matrix: Optional[np.matrix]
    native_resolution: Optional[tuple[int, int]]
    bbox: Optional[Image.Rect]

    def with_target_viewport(self, width, height):
        vw = width / 100
        vh = height / 100
        left, top, right, bottom = np.asarray(self.bbox_matrix * np.matrix(np.matrix([[vw], [vh], [1]]))).reshape(4)
        bbox = Image.Rect.from_ltrb(left, top, right, bottom)
        return RegionOfInterest(self.template, self.bbox_matrix, self.native_resolution, bbox)

@dataclass
class RoiMatchingResult:
    score: Real
    threshold: Real
    score_for_max_similarity: Real
    bbox: Optional[Image.Rect] = None
    context: Any = None
    if TYPE_CHECKING:
        NoMatch: ClassVar[RoiMatchingResult]

    def __bool__(self):
        if self.threshold > self.score_for_max_similarity:
            return self.score < self.threshold
        elif self.threshold <= self.score_for_max_similarity:
            return self.score > self.threshold

    def with_threshold(self, threshold):
        return RoiMatchingResult(self.score, threshold, self.bbox, self.score_for_max_similarity)

RoiMatchingResult.NoMatch = RoiMatchingResult(65025, 1, 0)

if __name__ == "__main__":
    import sys

    print(globals()[sys.argv[-2]](Image.open(sys.argv[-1])))
