"""
Stage 2 of the pipeline: splitting documents into chunks.

⚠️ THIS IS THE FILE YOU CHANGE IN MILESTONE 3.

`split_documents` below is deliberately plain. It cuts every document into
fixed-size pieces with a fixed overlap and pays no attention to where sentences
or paragraphs end. It works, and it is not good.

On a corpus of short posts it may not cut anything at all: `campus_life` comes
out as 88 documents and 88 chunks, because almost nothing in it reaches 800
characters. That is the baseline, not a bug — Milestone 3 is where you decide
whether one post should stay one chunk.

Your job in Milestone 3 is to replace the *body* of `split_documents` with a
strategy that fits the documents you actually read in Milestone 1. Keep the
name and the shape of what it returns — the rest of the pipeline calls it, and
your README has to name the function that produced your chunks.

If you get stuck for 30 minutes, `fallback_split` is the original. Switch back
to it, write down what you saw, and move on. That's a real observation about
your pipeline, not giving up.
"""

from dataclasses import dataclass

import config
from ingest import Document


@dataclass
class Chunk:
    """One piece of one document."""

    text: str
    source: str        # which file it came from
    index: int         # which chunk within that file, starting at 0
    produced_by: str   # the function that made it — cite this in your README

    @property
    def label(self) -> str:
        return f"{self.source}#{self.index}"


def fallback_split(
    documents: list[Document],
    chunk_size: int | None = None,
    overlap: int | None = None,
) -> list[Chunk]:
    """
    The starter's original chunker. Fixed-size character windows with overlap.

    Keep this function. Milestone 3's stop rule points back at it, and having
    something to compare your own strategy against is useful in unit 2.
    """
    chunk_size = chunk_size or config.CHUNK_SIZE
    overlap = overlap or config.CHUNK_OVERLAP

    if overlap >= chunk_size:
        raise ValueError("overlap has to be smaller than chunk_size")

    chunks: list[Chunk] = []
    for doc in documents:
        start = 0
        index = 0
        while start < len(doc.text):
            piece = doc.text[start : start + chunk_size].strip()
            if piece:
                chunks.append(
                    Chunk(
                        text=piece,
                        source=doc.source,
                        index=index,
                        produced_by="chunker.py::fallback_split",
                    )
                )
                index += 1
            start += chunk_size - overlap

    return chunks


def split_documents(documents: list[Document]) -> list[Chunk]:
    """
    Split Markdown guides at section and paragraph boundaries.

    ``CHUNK_SIZE`` is a soft target. A complete paragraph is allowed to exceed
    it because keeping a thought intact is more useful than cutting at an
    arbitrary character. When a section needs several chunks, its document and
    section headings are repeated so each result still identifies its subject.
    """
    chunks: list[Chunk] = []

    for doc in documents:
        blocks = [
            block.strip()
            for block in doc.text.split("\n\n")
            if block.strip()
        ]
        if not blocks:
            continue

        document_heading = blocks[0] if blocks[0].startswith("# ") else ""
        sections: list[tuple[str, list[str]]] = []
        section_heading = document_heading
        section_paragraphs: list[str] = []

        for block in blocks[1:] if document_heading else blocks:
            if block.startswith("#"):
                if section_paragraphs:
                    sections.append((section_heading, section_paragraphs))
                section_heading = block
                section_paragraphs = []
            else:
                section_paragraphs.append(block)

        if section_paragraphs:
            sections.append((section_heading, section_paragraphs))

        index = 0
        for heading, paragraphs in sections:
            heading_parts = [part for part in (document_heading, heading) if part]
            # Avoid repeating the document title in the introductory section.
            heading_text = "\n\n".join(dict.fromkeys(heading_parts))
            current_parts = [heading_text] if heading_text else []

            for paragraph in paragraphs:
                candidate = "\n\n".join([*current_parts, paragraph])
                has_body = len(current_parts) > (1 if heading_text else 0)

                if has_body and len(candidate) > config.CHUNK_SIZE:
                    chunks.append(
                        Chunk(
                            text="\n\n".join(current_parts),
                            source=doc.source,
                            index=index,
                            produced_by="chunker.py::split_documents",
                        )
                    )
                    index += 1
                    current_parts = [heading_text, paragraph] if heading_text else [paragraph]
                else:
                    current_parts.append(paragraph)

            text = "\n\n".join(current_parts).strip()
            if text:
                chunks.append(
                    Chunk(
                        text=text,
                        source=doc.source,
                        index=index,
                        produced_by="chunker.py::split_documents",
                    )
                )
                index += 1

    return chunks


def describe(chunks: list[Chunk]) -> str:
    """A one-line summary, printed after indexing."""
    if not chunks:
        return "0 chunks"
    lengths = [len(c.text) for c in chunks]
    return (
        f"{len(chunks)} chunks, "
        f"{sum(lengths) // len(lengths)} characters on average "
        f"(shortest {min(lengths)}, longest {max(lengths)}), "
        f"produced by {chunks[0].produced_by}"
    )


if __name__ == "__main__":
    from ingest import load_documents

    chunks = split_documents(load_documents())
    print(describe(chunks))
