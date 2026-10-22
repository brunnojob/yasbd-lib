"""Build a paragraph-aware sentence index from a text stream.

Offsets are relative to each paragraph, so a reader can highlight a sentence
without retaining the entire input in memory. ParagraphEOF resets the offset
after a blank-line separator. Run with ``python examples/paragraph_sentence_index.py``.
"""

from collections.abc import Iterator
from dataclasses import dataclass
from io import StringIO, TextIOBase

from yasbd import BoundaryDetector, ParagraphEOF


@dataclass(frozen=True)
class SentenceLocation:
    """Paragraph number and half-open character offsets within that paragraph."""

    paragraph: int
    start: int
    end: int


def sentence_locations(source: TextIOBase, lang: str = "en") -> Iterator[SentenceLocation]:
    """Yield locations for each sentence without reading the whole source.

    Args:
        source: Open text stream. The caller remains responsible for closing it.
        lang: Language code for the boundary detector.

    Yields:
        Zero-based paragraph numbers with ``[start, end)`` offsets. Whitespace
        between sentences is part of the following span; trailing paragraph
        whitespace is excluded by the boundary detector.

    Examples:
        >>> stream = StringIO("Dr. Green called. The clinic replied."
        ...                   "\\n\\nNext visit is Friday.")
        >>> [(s.paragraph, s.start, s.end) for s in sentence_locations(stream)]
        [(0, 0, 17), (0, 17, 37), (1, 0, 21)]
    """
    paragraph = 0
    start = 0
    for boundary in BoundaryDetector(lang=lang).detect(source, relative=True):
        if boundary is ParagraphEOF:
            paragraph += 1
            start = 0
        else:
            yield SentenceLocation(paragraph, start, boundary)
            start = boundary


if __name__ == "__main__":
    sample = "Dr. Green called. The clinic replied.\n\nNext visit is Friday."
    with StringIO(sample) as stream:
        for location in sentence_locations(stream):
            print(location)
