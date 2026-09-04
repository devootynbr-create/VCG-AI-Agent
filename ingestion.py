from typing import List, Dict
import fitz
import re


def clean_text(text: str) -> str:
    """Normalize whitespace while preserving text content."""
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def chunk_words(
    words: List[str],
    chunk_size: int = 800,
    overlap: int = 120
) -> List[str]:
    """
    Split a list of words into overlapping chunks.
    """
    if not words:
        return []

    chunks = []
    start = 0

    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk = " ".join(words[start:end])
        chunks.append(chunk)

        if end >= len(words):
            break

        start = end - overlap

    return chunks


def extract_and_chunk_pdf(
    file_path: str,
    document_name: str,
    document_type: str = "VCG Knowledge"
) -> List[Dict]:
    """
    Extract PDF text page-by-page, inject page markers for citation,
    and create structured chunks containing text, metadata, and unique IDs.
    """
    results = []

    try:
        doc = fitz.open(file_path)

        # Sanitize document name to create clean vector storage IDs
        safe_doc_id = re.sub(r"[^a-zA-Z0-9_-]", "_", document_name)

        for page_number, page in enumerate(doc, start=1):
            raw_text = page.get_text("text")
            cleaned = clean_text(raw_text)

            if not cleaned:
                continue

            words = cleaned.split()
            chunks = chunk_words(words)

            for chunk_number, chunk in enumerate(chunks, start=1):
                # Format text with page marker so agent source indexing works cleanly
                chunk_text_with_page = f"[PAGE {page_number}]\n{chunk}"
                
                unique_id = f"{safe_doc_id}_p{page_number}_c{chunk_number}"

                results.append(
                    {
                        "id": unique_id,
                        "text": chunk_text_with_page,
                        "metadata": {
                            "document": document_name,
                            "document_type": document_type,
                            "page": str(page_number),
                            "chunk": chunk_number
                        }
                    }
                )

        doc.close()

    except Exception as exc:
        raise RuntimeError(
            f"Failed to process {document_name}: {exc}"
        ) from exc

    return results


def process_pdf(
    file_path: str,
    document_name: str,
    document_type: str = "VCG Knowledge"
) -> List[Dict]:
    """
    Backwards-compatible entry point for Streamlit ingestion pipeline.
    """
    return extract_and_chunk_pdf(
        file_path=file_path,
        document_name=document_name,
        document_type=document_type
    )