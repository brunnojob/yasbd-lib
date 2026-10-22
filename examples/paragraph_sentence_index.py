"""Build a structured document model from paragraphs and sentences.

StructDoc exposes paragraphs containing sentence objects with paragraph-relative
character offsets. It uses ParagraphStream for paragraph grouping and
BoundaryDetector for sentence segmentation.
Run with ``python examples/paragraph_sentence_index.py``.
"""

from dataclasses import dataclass
from io import StringIO

from yasbd import BoundaryDetector, ParagraphEOF
from yasbd.utils.paragraph_stream import ParagraphStream


@dataclass(frozen=True)
class Sentence:
    """A sentence and its half-open character span within a paragraph."""

    text: str
    start: int
    end: int


@dataclass(frozen=True)
class Paragraph:
    """A paragraph with its zero-based index and segmented sentences."""

    index: int
    text: str
    sentences: tuple[Sentence, ...]


class StructDoc:
    """Represent text as paragraphs containing sentence objects.

    Args:
        text: Full document text.
        lang: Language code used by the sentence boundary detector.

    Examples:
        >>> doc = StructDoc("Dr. Green called. The clinic replied.\\n\\nNext visit is Friday.")
        >>> [(p.index, [s.text for s in p.sentences]) for p in doc.paragraphs]
        [(0, ['Dr. Green called.', ' The clinic replied.']), (1, ['Next visit is Friday.'])]
        >>> [(s.start, s.end) for s in doc.paragraphs[0].sentences]
        [(0, 17), (17, 37)]
        >>> doc.paragraphs[0].text[slice(*(
        ...     doc.paragraphs[0].sentences[0].start,
        ...     doc.paragraphs[0].sentences[0].end,
        ... ))]
        'Dr. Green called.'
    """

    def __init__(self, text: str, lang: str = "en") -> None:
        self.text = text
        self.lang = lang
        self.paragraphs = tuple(self._parse_paragraphs())

    def _parse_paragraphs(self):
        detector = BoundaryDetector(lang=self.lang)
        stream = ParagraphStream(self.text, skip_empty_lines=True)

        for index, raw_paragraph in enumerate(stream):
            paragraph_text = raw_paragraph.strip()
            if not paragraph_text:
                continue

            sentences = []
            start = 0
            for boundary in detector.detect(StringIO(paragraph_text), relative=True):
                if boundary is ParagraphEOF:
                    continue
                sentences.append(
                    Sentence(
                        text=paragraph_text[start:boundary],
                        start=start,
                        end=boundary,
                    )
                )
                start = boundary

            if start < len(paragraph_text):
                sentences.append(
                    Sentence(
                        text=paragraph_text[start:],
                        start=start,
                        end=len(paragraph_text),
                    )
                )

            yield Paragraph(
                index=index,
                text=paragraph_text,
                sentences=tuple(sentences),
            )


if __name__ == "__main__":
    sample = (
        "Dr. Green called. The clinic replied.\n\n"
        "Next visit is Friday. Please arrive early."
    )
    document = StructDoc(sample)

    for paragraph in document.paragraphs:
        print(f"Paragraph {paragraph.index}: {paragraph.text}")
        for sentence in paragraph.sentences:
            print(f"  [{sentence.start}:{sentence.end}] {sentence.text}")
