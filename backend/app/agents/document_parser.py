"""
Document Parser Agent - Extracts text from PDF/DOCX files
"""
import logging
from typing import Dict, Any, Optional
import pdfplumber
from docx import Document
import io

from app.services.storage_factory import storage as storage_service

logger = logging.getLogger(__name__)


class DocumentParserAgent:
    """Agent for parsing document files and extracting raw text"""
    
    def __init__(self):
        self.storage_service = storage_service
    
    async def parse_document(self, blob_url: str) -> Dict[str, Any]:
        """
        Parse a document and extract text
        
        Args:
            blob_url: URL of the blob storage file
            
        Returns:
            Dictionary containing parsed text and metadata
        """
        logger.info(f"Parsing document from: {blob_url}")
        
        try:
            # Download file
            file_content = await self.storage_service.download_file(blob_url)
            
            # Determine file type from URL
            if blob_url.endswith('.pdf') or 'pdf' in blob_url.lower():
                result = await self._parse_pdf(file_content)
            elif blob_url.endswith('.docx') or 'docx' in blob_url.lower():
                result = await self._parse_docx(file_content)
            else:
                raise ValueError(f"Unsupported file type: {blob_url}")
            
            # Log with appropriate metric
            if result.get('page_count'):
                logger.info(f"Parsed document: {result['page_count']} pages, {len(result['full_text'])} characters")
            elif result.get('paragraph_count'):
                logger.info(f"Parsed document: {result['paragraph_count']} paragraphs, {len(result['full_text'])} characters")
            else:
                logger.info(f"Parsed document: {len(result['full_text'])} characters")
            
            return result
            
        except Exception as e:
            logger.error(f"Error parsing document: {e}", exc_info=True)
            raise
    
    async def _parse_pdf(self, file_content: bytes) -> Dict[str, Any]:
        """Parse PDF file using pdfplumber"""
        try:
            pdf_file = io.BytesIO(file_content)
            
            pages = []
            full_text = ""
            total_pages = 0
            
            with pdfplumber.open(pdf_file) as pdf:
                total_pages = len(pdf.pages)
                
                for page_num, page in enumerate(pdf.pages, start=1):
                    # Extract text
                    text = page.extract_text() or ""
                    
                    # Also extract tables if present
                    tables = page.extract_tables()
                    tables_text = ""
                    if tables:
                        for table in tables:
                            # Convert table to text
                            table_str = "\n".join([
                                " | ".join([str(cell) if cell else "" for cell in row])
                                for row in table
                            ])
                            tables_text += "\n\n" + table_str + "\n\n"
                    
                    page_text = text + tables_text
                    
                    pages.append({
                        "page_number": page_num,
                        "text": page_text
                    })
                    full_text += f"\n\n--- Page {page_num} ---\n\n{page_text}"
            
            return {
                "full_text": full_text.strip(),
                "pages": pages,
                "page_count": total_pages,
                "file_type": "pdf",
                "metadata": {
                    "parser": "pdfplumber"
                }
            }
            
        except Exception as e:
            logger.error(f"Error parsing PDF: {e}")
            raise
    
    async def _parse_docx(self, file_content: bytes) -> Dict[str, Any]:
        """Parse DOCX file"""
        try:
            docx_file = io.BytesIO(file_content)
            doc = Document(docx_file)
            
            paragraphs = []
            full_text = ""
            
            for i, para in enumerate(doc.paragraphs):
                if para.text.strip():
                    paragraphs.append({
                        "index": i,
                        "text": para.text
                    })
                    full_text += para.text + "\n\n"
            
            # Also extract tables
            tables_text = []
            for table in doc.tables:
                table_text = "\n".join([
                    " | ".join([cell.text for cell in row.cells])
                    for row in table.rows
                ])
                tables_text.append(table_text)
                full_text += "\n\n" + table_text + "\n\n"
            
            return {
                "full_text": full_text.strip(),
                "paragraphs": paragraphs,
                "tables": tables_text,
                "paragraph_count": len(paragraphs),
                "table_count": len(doc.tables),
                "file_type": "docx",
                "metadata": {}
            }
            
        except Exception as e:
            logger.error(f"Error parsing DOCX: {e}")
            raise
    
    def chunk_text(
        self,
        text: str,
        max_chunk_size: int = 1000,
        overlap: int = 200,
    ) -> list:
        """
        Split text into overlapping chunks for downstream AI processing.

        Each chunk is represented as a dict so callers can store additional
        metadata alongside the text without changing this method's signature.

        Args:
            text: Full document text.
            max_chunk_size: Maximum characters per chunk (default 1000).
            overlap: Characters shared between adjacent chunks (default 200).

        Returns:
            List of dicts: [{"chunk_index": int, "chunk_text": str}, ...]
        """
        if not text:
            return []

        if max_chunk_size <= overlap:
            raise ValueError("max_chunk_size must be greater than overlap")

        chunks = []
        start = 0
        chunk_index = 0

        while start < len(text):
            end = start + max_chunk_size
            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append({"chunk_index": chunk_index, "chunk_text": chunk_text})
                chunk_index += 1
            # Advance by (max_chunk_size - overlap) so consecutive chunks share `overlap` chars
            start += max_chunk_size - overlap

        logger.info(f"Created {len(chunks)} chunks from {len(text)} characters")
        return chunks

    def extract_paragraphs(self, parse_result: dict) -> list:
        """
        Normalise paragraph output from both _parse_pdf and _parse_docx into a
        flat list of non-empty paragraph strings.

        Args:
            parse_result: Return value of parse_document().

        Returns:
            Ordered list of non-empty paragraph strings.
        """
        paragraphs: list = []

        if parse_result.get("file_type") == "pdf":
            for page in parse_result.get("pages", []):
                for line in page.get("text", "").splitlines():
                    stripped = line.strip()
                    if stripped:
                        paragraphs.append(stripped)
        else:
            # DOCX
            for item in parse_result.get("paragraphs", []):
                text = item.get("text", "").strip() if isinstance(item, dict) else str(item).strip()
                if text:
                    paragraphs.append(text)

        return paragraphs
