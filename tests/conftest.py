import pymupdf
import pytest

from config import ROOT


@pytest.fixture
def demo_pdf():
    return ROOT / "sample_data" / "fair-principles.pdf"


def make_pdf(*pages: str, password=False) -> bytes:
    with pymupdf.open() as pdf:
        for content in pages:
            page = pdf.new_page()
            page.insert_textbox((55, 55, 540, 760), content, fontsize=10)
        if password:
            return pdf.tobytes(
                encryption=pymupdf.PDF_ENCRYPT_AES_256, user_pw="paper", owner_pw="owner"
            )
        return pdf.tobytes()
