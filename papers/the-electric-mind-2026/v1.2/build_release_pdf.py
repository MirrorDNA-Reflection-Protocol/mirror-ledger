#!/usr/bin/env python3
"""Finalize The Electric Mind v1.2 without changing the supplied source PDF.

The source is a text-based release candidate.  This build removes its explicit
publication placeholders with PDF redactions, inserts the reserved DOI and the
approved CC BY 4.0 license, creates a truthful disclosure boundary, assigns new
forecast identifiers to the materially revised calls, and preserves searchable
text throughout the document.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import fitz


OUTPUT_DIR = Path(__file__).resolve().parent
OUTPUT = OUTPUT_DIR / "The_Electric_Mind_v1.2.pdf"

DOI = "10.5281/zenodo.21889238"
DOI_URL = f"https://doi.org/{DOI}"
LICENSE_URL = "https://creativecommons.org/licenses/by/4.0/"

NAVY = (0.10, 0.29, 0.48)
GOLD = (0.78, 0.55, 0.00)
CHARCOAL = (0.12, 0.12, 0.13)
WHITE = (1.0, 1.0, 1.0)


def redact(page: fitz.Page, rect: fitz.Rect) -> None:
    page.add_redact_annot(rect, fill=WHITE)


def put_centered(
    page: fitz.Page,
    rect: fitz.Rect,
    text: str,
    *,
    fontsize: float,
    color: tuple[float, float, float],
    fontname: str = "helv",
) -> None:
    result = page.insert_textbox(
        rect,
        text,
        fontname=fontname,
        fontsize=fontsize,
        color=color,
        align=fitz.TEXT_ALIGN_CENTER,
        lineheight=1.0,
    )
    if result < 0:
        raise RuntimeError(f"Text did not fit: {text!r} in {rect}")


def put_lines(
    page: fitz.Page,
    x: float,
    y: float,
    lines: list[str],
    *,
    fontsize: float,
    leading: float,
    color: tuple[float, float, float] = CHARCOAL,
    fontname: str = "helv",
) -> None:
    for line in lines:
        page.insert_text((x, y), line, fontname=fontname, fontsize=fontsize, color=color)
        y += leading


def finalize(source: Path) -> None:
    if not source.is_file():
        raise FileNotFoundError(source)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(source)

    # Cover and running heads.
    cover = doc[0]
    redact(cover, fitz.Rect(65, 198, 530, 217))
    redact(cover, fitz.Rect(115, 360, 480, 381))

    for page in doc[1:]:
        redact(page, fitz.Rect(68, 31, 528, 50))

    # Revised forecasts must not reuse the frozen v1.0 identifiers.
    id_replacements = {
        6: [(fitz.Rect(73, 348, 121, 366), "EM-1201"),
            (fitz.Rect(73, 522, 121, 540), "EM-1202"),
            (fitz.Rect(73, 659, 121, 677), "EM-1203")],
        7: [(fitz.Rect(73, 109, 121, 128), "EM-1204"),
            (fitz.Rect(73, 258, 121, 277), "EM-1205"),
            (fitz.Rect(73, 432, 121, 451), "EM-1206")],
    }
    for page_index, replacements in id_replacements.items():
        for rect, _ in replacements:
            redact(doc[page_index], rect)
    page8 = doc[7]
    redact(page8, fitz.Rect(350, 434, 521, 535))

    # State the immutable v1.0 / revised v1.2 forecast boundary explicitly.
    page9 = doc[8]
    redact(page9, fitz.Rect(69, 225, 526, 272))

    # Remove the unresolved holdings prompt and its continuation.
    page10 = doc[9]
    page11 = doc[10]
    redact(page10, fitz.Rect(69, 713, 527, 760))
    redact(page11, fitz.Rect(69, 68, 527, 105))

    # Replace the citation/DOI/license/ORCID placeholder block.
    redact(page11, fitz.Rect(69, 191, 527, 243))

    # Closing folio.
    page13 = doc[12]
    redact(page13, fitz.Rect(68, 208, 528, 228))

    for page in doc:
        page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE)

    put_centered(
        cover,
        fitz.Rect(65, 201, 530, 217),
        "A PUBLIC THESIS  |  VERSION 1.2  |  EVIDENCE-HARDENED EDITION",
        fontsize=9.0,
        color=GOLD,
        fontname="hebo",
    )
    put_centered(
        cover,
        fitz.Rect(115, 345, 480, 360),
        "Original thesis date: 10 August 2026  |  This edition: 11 August 2026",
        fontsize=8.2,
        color=(0.38, 0.38, 0.38),
    )
    put_centered(
        cover,
        fitz.Rect(115, 363, 480, 380),
        f"DOI: {DOI}  |  India  |  Five-year horizon",
        fontsize=9.0,
        color=(0.35, 0.35, 0.35),
        fontname="hebo",
    )
    cover.insert_link({"kind": fitz.LINK_URI, "from": fitz.Rect(133, 362, 304, 379), "uri": DOI_URL})

    running_head = "THE ELECTRIC MIND  |  PUBLIC THESIS  |  VERSION 1.2  |  EVIDENCE-HARDENED EDITION"
    for page in doc[1:]:
        page.insert_text((72, 43), running_head, fontname="hebo", fontsize=7.6, color=NAVY)
        page.draw_line((72, 49), (523, 49), color=NAVY, width=0.55)

    for page_index, replacements in id_replacements.items():
        page = doc[page_index]
        for rect, value in replacements:
            if value:
                page.insert_text((rect.x0 + 2, rect.y0 + 13), value, fontname="hebo", fontsize=7.4, color=CHARCOAL)
    put_lines(
        page8,
        352,
        448,
        [
            "Confirm: aggregate reported",
            "operating profit from annual filings",
            "of the universes frozen under",
            "EM-1201.",
            "Wrong: the equipment layer's",
            "operating-profit growth exceeds the",
            "broader stack's.",
        ],
        fontsize=8.6,
        leading=13.2,
    )

    put_lines(
        page9,
        72,
        238,
        [
            "Version 1.2 is date-stamped and archived under its DOI. Its revised forecasts are new",
            "entries EM-1201-EM-1206; the original EM-001-EM-006 remain frozen and scoreable.",
            "Forecasts will be marked wrong when evidence requires it. Receipts, not vibes.",
        ],
        fontsize=9.1,
        leading=13.6,
    )

    put_lines(
        page10,
        72,
        727,
        [
            "HOLDINGS DISCLOSURE: Not provided for this edition. No representation is made about",
            "the author's or immediate family's exposure to the sectors discussed.",
        ],
        fontsize=9.0,
        leading=14.0,
        fontname="hebo",
    )

    put_lines(
        page11,
        72,
        205,
        [
            "Cite as: Desai, P. (2026). The Electric Mind: Why India's AI boom will be built in",
            f"substations before server halls (Version 1.2). {DOI_URL}",
            "License: Creative Commons Attribution 4.0 International (CC BY 4.0).",
        ],
        fontsize=9.0,
        leading=14.0,
    )
    page11.insert_link({"kind": fitz.LINK_URI, "from": fitz.Rect(72, 207, 386, 225), "uri": DOI_URL})
    page11.insert_link({"kind": fitz.LINK_URI, "from": fitz.Rect(72, 223, 432, 240), "uri": LICENSE_URL})

    put_centered(
        page13,
        fitz.Rect(68, 211, 528, 227),
        f"PAUL DESAI  |  AUGUST 2026  |  THE ELECTRIC MIND, VERSION 1.2  |  DOI {DOI}",
        fontsize=7.3,
        color=NAVY,
        fontname="hebo",
    )
    page13.insert_link({"kind": fitz.LINK_URI, "from": fitz.Rect(367, 209, 527, 228), "uri": DOI_URL})

    metadata = doc.metadata
    metadata.update(
        {
            "title": "The Electric Mind: Why India's AI boom will be built in substations before server halls",
            "author": "Paul Desai",
            "subject": "A public, falsifiable thesis on India's AI infrastructure, electricity delivery, and grid investment.",
            "keywords": "India, artificial intelligence, data centres, electricity grid, transmission, transformers, storage, infrastructure, forecast ledger",
            "creator": "Paul Desai",
            "producer": "Active Mirror release build",
            "creationDate": "D:20260811120000+05'30'",
            "modDate": "D:20260811180000+05'30'",
        }
    )
    doc.set_metadata(metadata)

    temp = OUTPUT.with_suffix(".tmp.pdf")
    doc.save(temp, garbage=4, deflate=True, clean=True)
    doc.close()
    os.replace(temp, OUTPUT)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(f"Usage: {Path(sys.argv[0]).name} SOURCE_PDF")
    finalize(Path(sys.argv[1]).expanduser().resolve())
    print(OUTPUT)
