"""
ingestion_pipeline.py

Handles document ingestion, chunking, OCR, and metadata extraction for RAG.
"""
import os
from typing import List, Dict, Any

SUPPORTED_EXTENSIONS = ['.pdf', '.docx', '.pptx', '.txt', '.png', '.jpg', '.jpeg']

class DocumentChunk:
    def __init__(self, text: str, metadata: Dict[str, Any]):
        self.text = text
        self.metadata = metadata


import shutil

class IngestionPipeline:
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50, output_dir: str = "../data/ingested"):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.output_dir = output_dir

    def ingest(self, file_path: str, metadata: Dict[str, Any]) -> List[DocumentChunk]:
        ext = os.path.splitext(file_path)[1].lower()
        # Add .md to supported extensions
        if ext not in SUPPORTED_EXTENSIONS and ext != '.md':
            raise ValueError(f"Unsupported file type: {ext}")

        # Prepare output directory for this document
        doc_id = os.path.splitext(os.path.basename(file_path))[0]
        doc_dir = os.path.join(self.output_dir, doc_id)
        os.makedirs(doc_dir, exist_ok=True)

        # Store original document
        shutil.copy2(file_path, os.path.join(doc_dir, os.path.basename(file_path)))

        # Extract text and images
        if ext == '.pdf':
            text = self._extract_pdf(file_path)
            images = [] # TODO: extract images from PDF
        elif ext == '.docx':
            text = self._extract_docx(file_path)
            images = [] # TODO: extract images from DOCX
        elif ext == '.pptx':
            text = self._extract_pptx(file_path)
            images = [] # TODO: extract images from PPTX
        elif ext in ['.txt', '.md']:
            text = self._extract_txt(file_path)
            images = []
        elif ext in ['.png', '.jpg', '.jpeg']:
            text = self._extract_image_ocr(file_path)
            images = [file_path]
        else:
            text = ""
            images = []

        # Store extracted images (if any)
        image_paths = []
        for img_path in images:
            if os.path.exists(img_path):
                dest = os.path.join(doc_dir, os.path.basename(img_path))
                shutil.copy2(img_path, dest)
                image_paths.append(dest)

        # Chunk text
        chunks = self._chunk_text(text, metadata)

        # Store chunks as text files
        chunks_dir = os.path.join(doc_dir, "chunks")
        os.makedirs(chunks_dir, exist_ok=True)
        for i, chunk in enumerate(chunks):
            chunk_file = os.path.join(chunks_dir, f"chunk_{i+1}.txt")
            with open(chunk_file, "w", encoding="utf-8") as f:
                f.write(chunk.text)

        # Store summary (placeholder)
        summary_file = os.path.join(doc_dir, "summary.txt")
        with open(summary_file, "w", encoding="utf-8") as f:
            f.write("[TODO] Add summary generation here.")

        # Return chunk texts and metadata for embedding and vector DB storage
        chunk_texts = [chunk.text for chunk in chunks]
        chunk_metadatas = [chunk.metadata for chunk in chunks]
        return chunk_texts, chunk_metadatas

    def _extract_pdf(self, file_path: str) -> str:
        # TODO: Implement PDF text extraction (e.g., PyPDF2, pdfplumber)
        return ""

    def _extract_docx(self, file_path: str) -> str:
        # TODO: Implement DOCX text extraction (e.g., python-docx)
        return ""

    def _extract_pptx(self, file_path: str) -> str:
        # TODO: Implement PPTX text extraction (e.g., python-pptx)
        return ""

    def _extract_txt(self, file_path: str) -> str:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

    def _extract_image_ocr(self, file_path: str) -> str:
        # TODO: Implement OCR (e.g., pytesseract)
        return ""

    def _chunk_text(self, text: str, metadata: Dict[str, Any]) -> List[DocumentChunk]:
        chunks = []
        start = 0
        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            chunk_text = text[start:end]
            chunk_metadata = metadata.copy()
            chunk_metadata['chunk_start'] = start
            chunk_metadata['chunk_end'] = end
            chunks.append(DocumentChunk(chunk_text, chunk_metadata))
            start += self.chunk_size - self.chunk_overlap
        return chunks
