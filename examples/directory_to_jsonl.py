"""Build a sentence-level JSONL dataset from a directory of UTF-8 text files.

The example processes every ``.txt`` file in a directory with YASBD and
writes one JSON object per sentence. Each record keeps the source filename.
The output must be a different file from every input, including linked paths.

Example input directory:

    documents/
    ├── article.txt
    └── notes.txt

Run:

    python examples/directory_to_jsonl.py documents sentences.jsonl

Example output:

    {"source": "article.txt", "text": "Dr. Smith reviewed the report."}
    {"source": "article.txt", "text": "The results were ready for publication."}
    {"source": "notes.txt", "text": "The dataset contains 120 records."}
"""

import argparse
import json
from pathlib import Path

from yasbd import BoundaryDetector


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a sentence-level JSONL dataset from UTF-8 text files."
    )
    parser.add_argument(
        "input_dir",
        type=Path,
        help="Directory containing UTF-8 .txt files.",
    )
    parser.add_argument(
        "output",
        type=Path,
        help="Path to the output JSONL file.",
    )
    parser.add_argument(
        "--lang",
        default="en",
        help="YASBD language code (default: en).",
    )
    return parser.parse_args()


def resolve_output_path(output: Path) -> Path:
    """Resolve and validate the output path against the working directory."""
    base_dir = Path.cwd().resolve()
    target_path = output.resolve()

    if not target_path.is_relative_to(base_dir):
        raise ValueError(
            f"Output path must stay within the current working directory: {output}"
        )

    return target_path


def build_dataset(input_dir: Path, output: Path, lang: str) -> int:
    """Export sentences without overwriting an input file.

    Args:
        input_dir: Directory containing UTF-8 text files.
        output: Output file within the current working directory.
        lang: YASBD language code.

    Returns:
        Number of exported sentences.

    Raises:
        ValueError: If inputs are missing or the output aliases an input.

    >>> from tempfile import TemporaryDirectory
    >>> with TemporaryDirectory(dir=Path.cwd()) as directory:
    ...     root = Path(directory)
    ...     source = root / "article.txt"
    ...     text = "Dr. Smith arrived. The report is ready."
    ...     _ = source.write_text(text, encoding="utf-8")
    ...     alias = root / "linked.jsonl"
    ...     alias.hardlink_to(source)
    ...     for target in (source, alias):
    ...         try:
    ...             build_dataset(root, target, "en")
    ...         except ValueError as exc:
    ...             print(str(exc).startswith("Output path must not overwrite"))
    ...         assert source.read_text(encoding="utf-8") == text
    ...     output = root / "sentences.jsonl"
    ...     print(build_dataset(root, output, "en"))
    ...     print([json.loads(line)["text"] for line in output.read_text().splitlines()])
    True
    True
    2
    ['Dr. Smith arrived.', 'The report is ready.']
    """
    if not input_dir.is_dir():
        raise ValueError(f"Input directory does not exist: {input_dir}")

    text_files = sorted(path for path in input_dir.glob("*.txt") if path.is_file())

    if not text_files:
        raise ValueError(f"No .txt files found in: {input_dir}")

    detector = BoundaryDetector(lang=lang)

    output = resolve_output_path(output)
    for source_path in text_files:
        if output == source_path.resolve() or (
            output.exists() and output.samefile(source_path)
        ):
            raise ValueError(f"Output path must not overwrite an input file: {source_path}")
    output.parent.mkdir(parents=True, exist_ok=True)

    sentence_count = 0
    with output.open("w", encoding="utf-8") as output_file:
        for source_path in text_files:
            with source_path.open(encoding="utf-8") as input_file:
                for sentence in detector.segment(input_file):
                    record = {
                        "source": source_path.name,
                        "text": sentence,
                    }

                    output_file.write(json.dumps(record, ensure_ascii=False) + "\n")
                    sentence_count += 1

    return sentence_count


def main() -> None:
    args = parse_args()

    try:
        sentence_count = build_dataset(
            input_dir=args.input_dir,
            output=args.output,
            lang=args.lang,
        )
    except (OSError, ValueError) as exc:
        raise SystemExit(str(exc)) from exc

    print(f"Wrote {sentence_count} sentences to {args.output}")


if __name__ == "__main__":
    main()
