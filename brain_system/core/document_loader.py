
import os
from typing import List


class DocumentLoader:
    """Loads and chunks text/PDF documents for persona extraction."""

    SUPPORTED_EXTENSIONS = [".txt", ".pdf"]

    @staticmethod
    def load(filepath: str) -> str:
        """
        Load a document and return its full text content.
        Supports .txt and .pdf files.
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Document not found: {filepath}")

        ext = os.path.splitext(filepath)[1].lower()

        if ext == ".txt":
            return DocumentLoader._load_txt(filepath)
        elif ext == ".pdf":
            return DocumentLoader._load_pdf(filepath)
        else:
            raise ValueError(
                f"Unsupported file type: {ext}. "
                f"Supported: {DocumentLoader.SUPPORTED_EXTENSIONS}"
            )

    @staticmethod
    def _load_txt(filepath: str) -> str:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()

    @staticmethod
    def _load_pdf(filepath: str) -> str:
        try:
            import PyPDF2
        except ImportError:
            raise ImportError(
                "PyPDF2 is required for PDF support. "
                "Install it with: pip install PyPDF2"
            )

        text_parts = []
        with open(filepath, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)

        return "\n".join(text_parts)

    @staticmethod
    def chunk_text(text: str, chunk_size: int = 4000, overlap: int = 200) -> List[str]:
        """
        Split text into overlapping chunks for processing.
        Useful when the document exceeds model context limits.
        """
        if len(text) <= chunk_size:
            return [text]

        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            start = end - overlap

        return chunks
