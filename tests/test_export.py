from io import BytesIO

import pytest
from pptx import Presentation
from pydantic import ValidationError

from core.schemas import Slide, Slides
from utils.pptx_export import build_pptx


def test_real_powerpoint_round_trip():
    deck = Slides(slides=[
        Slide(title=f"Slide {number}", bullets=["A concise academic point."], source_pages=[2])
        for number in range(1, 7)
    ])
    presentation = Presentation(BytesIO(build_pptx(deck)))
    assert len(presentation.slides) == 6
    for number, slide in enumerate(presentation.slides, 1):
        texts = [shape.text for shape in slide.shapes if shape.has_text_frame]
        assert f"Slide {number}" in texts
        assert any("academic point" in item for item in texts)
        assert any("Source PDF pages 2" in item for item in texts)


def test_invalid_deck_is_rejected():
    with pytest.raises(ValidationError):
        Slides(slides=[])
    with pytest.raises(ValidationError):
        Slide(title="Bad", bullets=["x" * 126], source_pages=[1])
    deck = Slides(slides=[Slide(title="Bad", bullets=["point"], source_pages=[0])] * 5)
    with pytest.raises(ValueError, match="valid PDF"):
        build_pptx(deck)
