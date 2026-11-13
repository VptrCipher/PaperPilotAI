from io import BytesIO

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_AUTO_SIZE
from pptx.util import Inches, Pt

from core.schemas import Slides

PAPER = "F4F6FD"
INK = "192441"
MUTED = "4C5973"
INDIGO = "4C4FC6"


def rgb(hex_code: str):
    return RGBColor.from_string(hex_code)


def block(slide, x, y, w, h, text, size, color, bold=False):
    shape = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    frame = shape.text_frame
    frame.word_wrap = True
    frame.auto_size = MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE
    frame.margin_left = frame.margin_right = Pt(0)
    frame.margin_top = frame.margin_bottom = Pt(0)
    paragraph = frame.paragraphs[0]
    paragraph.text = text
    paragraph.font.name = "Aptos"
    paragraph.font.size = Pt(size)
    paragraph.font.bold = bold
    paragraph.font.color.rgb = rgb(color)
    return shape


def build_pptx(data: Slides) -> bytes:
    # Revalidate even if a caller changed a mutable Pydantic object.
    data = Slides.model_validate(data.model_dump())
    if any(not item.source_pages or min(item.source_pages) < 1 for item in data.slides):
        raise ValueError("Each slide needs one or more valid PDF page numbers.")

    presentation = Presentation()
    presentation.slide_width = Inches(13.333)
    presentation.slide_height = Inches(7.5)
    presentation.core_properties.title = data.slides[0].title
    presentation.core_properties.author = "PaperPilot AI"

    for number, item in enumerate(data.slides, start=1):
        cover = number == 1
        slide = presentation.slides.add_slide(presentation.slide_layouts[6])
        slide.background.fill.solid()
        slide.background.fill.fore_color.rgb = rgb(INK if cover else PAPER)
        accent = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE, Inches(0.78), Inches(0.65), Inches(0.85), Inches(0.08)
        )
        accent.fill.solid()
        accent.fill.fore_color.rgb = rgb("A5ABFF" if cover else INDIGO)
        accent.line.fill.background()
        heading = block(
            slide, 0.78, 1.02, 11.65, 1.55, item.title,
            44 if cover else 36, "FFFFFF" if cover else INK, True,
        )
        heading.name = "Slide title"
        for offset, bullet in enumerate(item.bullets):
            block(
                slide, 0.83, 2.86 + offset * 0.9, 11.5, 0.81, "•  " + bullet,
                23, "ECF0FF" if cover else INK,
            )
        pages = ", ".join(map(str, sorted(set(item.source_pages))))
        block(
            slide, 0.78, 7, 11.75, 0.28,
            f"Source PDF pages {pages}   /   {number} of {len(data.slides)}",
            11, "BCC6E7" if cover else MUTED,
        )
    buffer = BytesIO()
    presentation.save(buffer)
    return buffer.getvalue()
