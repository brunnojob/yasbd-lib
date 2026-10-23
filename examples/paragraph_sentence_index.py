"""Build a structured document model from paragraphs and sentences.

StructDoc exposes paragraphs containing sentence objects with paragraph-relative
character offsets. BoundaryDetector.detect(relative=True) supplies sentence
boundaries and ParagraphEOF markers in a single pass over the document.
Paragraph text preserves leading whitespace and omits trailing whitespace.
Run with ``python examples/paragraph_sentence_index.py``.
"""

import re
from dataclasses import dataclass

from yasbd import BoundaryDetector, ParagraphEOF


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
        [(0, ['Dr. Green called.', 'The clinic replied.']), (1, ['Next visit is Friday.'])]
        >>> [(s.start, s.end) for s in doc.paragraphs[0].sentences]
        [(0, 17), (18, 37)]
        >>> first = doc.paragraphs[0].sentences[0]
        >>> doc.paragraphs[0].text[first.start:first.end]
        'Dr. Green called.'
        >>> text = "\\n  First.  Second.  \\r\\n \\r\\n\\tLast without punctuation  "
        >>> padded = StructDoc(text)
        >>> [p.text for p in padded.paragraphs]
        ['  First.  Second.', '\\tLast without punctuation']
        >>> [[(s.text, s.start, s.end) for s in p.sentences] for p in padded.paragraphs]
        [[('First.', 2, 8), ('Second.', 10, 17)], [('Last without punctuation', 1, 25)]]
        >>> all(p.text[s.start:s.end] == s.text
        ...     for p in padded.paragraphs for s in p.sentences)
        True
        >>> [StructDoc(text).paragraphs for text in ("", "   ", "\\n\\n")]
        [(), (), ()]
    """

    def __init__(self, text: str, lang: str = "en") -> None:
        self.text = text
        self.lang = lang
        self._detector = BoundaryDetector(lang=lang)
        self.paragraphs = tuple(self._parse_paragraphs())

    def _parse_paragraphs(self):
        separator = re.compile(r"(?:[^\S\n]*\n)+")
        paragraph_start = 0
        start = 0
        index = 0
        sentences = []

        for boundary in self._detector.detect(self.text, relative=True):
            if boundary is ParagraphEOF:
                if sentences:
                    yield Paragraph(
                        index=index,
                        text=self.text[paragraph_start : paragraph_start + start],
                        sentences=tuple(sentences),
                    )
                    index += 1
                paragraph_start += start
                gap = separator.match(self.text, paragraph_start)
                if gap:
                    paragraph_start = gap.end()
                start = 0
                sentences = []
                continue

            raw_sentence = self.text[paragraph_start + start : paragraph_start + boundary]
            sentence_text = raw_sentence.strip()
            if sentence_text:
                sentence_start = start + len(raw_sentence) - len(raw_sentence.lstrip())
                sentences.append(
                    Sentence(
                        text=sentence_text,
                        start=sentence_start,
                        end=sentence_start + len(sentence_text),
                    )
                )
            start = boundary

        if sentences:
            yield Paragraph(
                index=index,
                text=self.text[paragraph_start : paragraph_start + start],
                sentences=tuple(sentences),
            )


if __name__ == "__main__":
    sample = (
        "Dr. Green called. The clinic replied.\n\nNext visit is Friday. Please arrive early."
    )
    document = StructDoc(sample)

    for paragraph in document.paragraphs:
        print(f"Paragraph {paragraph.index}: {paragraph.text}")
        for sentence in paragraph.sentences:
            print(f"  [{sentence.start}:{sentence.end}] {sentence.text}")
