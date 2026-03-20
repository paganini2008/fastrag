"""
LlamaIndex-backed document parser.

Implements the same ParseResult/ParsedPage interface as parsers.service.DocumentParser
so it can be swapped in via the DI container without changing any call sites.
"""
import logging
import tempfile
from pathlib import Path
from .service import ParseResult, ParsedPage

logger = logging.getLogger(__name__)

_MIME_TO_EXT = {
    "application/pdf": ".pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "application/msword": ".doc",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
    "application/vnd.ms-excel": ".xls",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": ".pptx",
    "application/vnd.ms-powerpoint": ".ppt",
    "text/html": ".html",
    "text/markdown": ".md",
    "text/plain": ".txt",
}


class LlamaIndexParser:
    """
    Uses LlamaIndex file readers to extract text from documents.

    Supported formats: PDF, DOCX, XLSX, PPTX, HTML, Markdown, TXT.
    Falls back to plain-text decode for unknown types.
    """

    def parse_bytes(self, data: bytes, mime_type: str, filename: str = "") -> ParseResult:
        candidate = ("." + filename.rsplit(".", 1)[-1].lower()) if "." in filename else ""
        ext = candidate if candidate in _MIME_TO_EXT.values() else _MIME_TO_EXT.get(mime_type, ".txt")

        # Write bytes to a temp file — LlamaIndex readers need a real path
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir) / f"doc{ext}"
            tmp_path.write_bytes(data)
            return self._load_with_llamaindex(tmp_path, ext, mime_type, filename)

    def _load_with_llamaindex(self, path: Path, ext: str, mime_type: str, filename: str) -> ParseResult:
        if ext in (".html", ".htm"):
            return self._parse_html(path)

        try:
            docs = self._get_reader(ext).load_data(path)
        except Exception as e:
            logger.warning(f"LlamaIndex reader failed for {filename!r} ({ext}): {e}; falling back to text")
            docs = []

        if not docs:
            text = path.read_text(errors="ignore")
            pages = [ParsedPage(page=1, text=text)]
            return ParseResult(
                text=text, pages=pages, page_count=1, word_count=len(text.split())
            )

        pages = []
        full_parts = []
        for i, doc in enumerate(docs):
            text = doc.text or ""
            page_num = int(doc.metadata.get("page_label", i + 1)) if doc.metadata else i + 1
            pages.append(ParsedPage(page=page_num, text=text, meta=doc.metadata or {}))
            full_parts.append(text)

        full_text = "\n\n".join(full_parts)
        return ParseResult(
            text=full_text,
            pages=pages,
            page_count=len(pages),
            word_count=len(full_text.split()),
        )

    def _parse_html(self, path: Path) -> ParseResult:
        import re
        from bs4 import BeautifulSoup
        html = path.read_text(errors="ignore")
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        raw = soup.get_text(separator="\n", strip=True)
        # Remove control characters that break JSON serialization
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", raw)
        pages = [ParsedPage(page=1, text=text)]
        return ParseResult(text=text, pages=pages, page_count=1, word_count=len(text.split()))

    def _get_reader(self, ext: str):
        from llama_index.readers.file import (
            PDFReader,
            DocxReader,
            PptxReader,
            PandasExcelReader,
            HTMLTagReader,
            MarkdownReader,
            FlatReader,
        )

        mapping = {
            ".pdf": PDFReader,
            ".docx": DocxReader,
            ".doc": DocxReader,
            ".pptx": PptxReader,
            ".ppt": PptxReader,
            ".xlsx": PandasExcelReader,
            ".xls": PandasExcelReader,
            ".html": HTMLTagReader,
            ".htm": HTMLTagReader,
            ".md": MarkdownReader,
            ".markdown": MarkdownReader,
        }
        reader_cls = mapping.get(ext, FlatReader)
        return reader_cls()
