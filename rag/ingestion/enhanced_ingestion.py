"""
Enhanced Ingestion Pipeline with Semantic Chunking

Focus: Semantic chunking by document structure instead of fixed character counts
Future: Table/figure detection when dependencies are added
"""

import os
from typing import List, Dict, Tuple, Any
from pathlib import Path
import re


class EnhancedIngestionPipeline:
    """
    Advanced document ingestion with structure-aware semantic chunking.
    
    Current Features:
    - Semantic chunking by paragraphs and sections
    - Section/header detection and extraction
    - Table detection (simple heuristic)
    - Figure reference detection
    - Metadata enrichment with context
    
    Future Features (when dependencies added):
    - pypdf for PDF table extraction
    - python-docx for DOCX structure preservation
    - python-pptx for slide-aware chunking
    - PIL + pytesseract for image OCR
    """
    
    def __init__(
        self,
        min_chunk_size: int = 300,
        max_chunk_size: int = 1000,
        semantic_chunking: bool = True
    ):
        """
        Initialize enhanced ingestion pipeline.
        
        Args:
            min_chunk_size: Minimum size for semantic chunks (chars)
            max_chunk_size: Maximum size for semantic chunks (chars)
            semantic_chunking: Use document structure for chunking vs fixed size
        """
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
        self.semantic_chunking = semantic_chunking
        
    def ingest(self, file_path: str, base_metadata: Dict[str, Any]) -> Tuple[List[str], List[Dict]]:
        """
        Ingest document with enhanced structure preservation.
        
        Returns:
            Tuple of (chunk_texts, chunk_metadatas) where each chunk has enriched metadata
        """
        file_ext = Path(file_path).suffix.lower()
        
        # Currently only TXT files supported with full enhancement
        # Others delegate to TXT extraction
        if file_ext == '.txt':
            return self._ingest_txt(file_path, base_metadata)
        else:
            print(f"[INFO] Enhanced ingestion for {file_ext} not yet implemented. Using basic text extraction.")
            return self._ingest_txt(file_path, base_metadata)
    
    def _ingest_txt(self, file_path: str, base_metadata: Dict) -> Tuple[List[str], List[Dict]]:
        """
        Enhanced TXT ingestion with semantic chunking and metadata enrichment.
        """
        chunks = []
        metadatas = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            
            # Semantic chunking by paragraphs/sections
            if self.semantic_chunking:
                chunk_texts = self._semantic_chunk(text)
            else:
                chunk_texts = self._fixed_chunk(text)
            
            # Enrich each chunk with metadata
            for i, chunk_text in enumerate(chunk_texts):
                if not chunk_text.strip():
                    continue
                
                metadata = base_metadata.copy()
                metadata.update({
                    'chunk_index': i,
                    'chunk_start': text.find(chunk_text),
                    'chunk_end': text.find(chunk_text) + len(chunk_text),
                    'chunk_type': self._classify_chunk_type(chunk_text),
                    'section': self._extract_section_name(chunk_text),
                    'has_table': self._detect_table_in_text(chunk_text),
                    'has_figure': self._detect_figure_reference(chunk_text),
                    'chunk_length': len(chunk_text)
                })
                
                chunks.append(chunk_text)
                metadatas.append(metadata)
        
        except Exception as e:
            print(f"[ERROR] TXT ingestion failed: {str(e)}")
            return [], []
        
        return chunks, metadatas
    
    def _semantic_chunk(self, text: str) -> List[str]:
        """
        Chunk text by semantic boundaries (sections, paragraphs).
        
        Strategy:
        1. Split by double newlines (paragraph boundaries)
        2. Combine paragraphs until max_chunk_size
        3. Ensure minimum chunk size for meaningful context
        4. Preserve section headers with their content
        """
        chunks = []
        
        # Split by double newlines (paragraphs)
        paragraphs = re.split(r'\n\s*\n', text)
        
        current_chunk = ""
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            # If adding this paragraph exceeds max size, save current chunk
            if len(current_chunk) + len(para) > self.max_chunk_size and len(current_chunk) >= self.min_chunk_size:
                chunks.append(current_chunk.strip())
                current_chunk = para
            else:
                # Add paragraph to current chunk
                current_chunk = current_chunk + "\n\n" + para if current_chunk else para
        
        # Add remaining chunk
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _fixed_chunk(self, text: str) -> List[str]:
        """
        Fallback to fixed-size chunking with overlap.
        """
        chunks = []
        overlap = 50
        
        for i in range(0, len(text), self.max_chunk_size - overlap):
            chunk = text[i:i + self.max_chunk_size]
            if chunk.strip():
                chunks.append(chunk)
        
        return chunks
    
    def _classify_chunk_type(self, text: str) -> str:
        """
        Classify chunk type based on content analysis.
        """
        text_lower = text.lower()
        
        # Check if it's a section header
        lines = text.split('\n')
        first_line = lines[0].strip() if lines else ""
        
        if first_line.startswith('#') or (len(first_line) < 100 and len(lines) == 1):
            return 'section_header'
        
        # Check if it contains a table
        if self._detect_table_in_text(text):
            return 'table'
        
        # Check if it's a list
        if text.count('\n-') > 3 or text.count('\n*') > 3 or text.count('\n1.') > 2:
            return 'list'
        
        # Default to text
        return 'text'
    
    def _detect_table_in_text(self, text: str) -> bool:
        """
        Detect if text contains a table using simple heuristics.
        """
        # Look for multiple pipe characters (markdown tables)
        pipe_count = text.count('|')
        if pipe_count > 5:
            # Check if there's a header separator line
            if '|---' in text or '|-' in text:
                return True
        
        # Look for aligned whitespace (tab-separated data)
        tab_count = text.count('\t')
        if tab_count > 3:
            return True
        
        # Look for [TABLE] markers
        if '[TABLE]' in text.upper():
            return True
        
        return False
    
    def _detect_figure_reference(self, text: str) -> bool:
        """
        Detect if text references a figure or image.
        """
        patterns = [
            r'Figure \d+',
            r'Fig\. \d+',
            r'Image \d+',
            r'\[IMAGE\]',
            r'\[FIGURE\]',
            r'see .* diagram',
            r'shown in .* chart'
        ]
        
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        return False
    
    def _extract_section_name(self, text: str) -> str:
        """
        Extract section name from text.
        
        Strategy:
        1. Check if first line is a header (starts with #, all caps, or short)
        2. Return that as section name
        3. Otherwise return "Content"
        """
        lines = text.split('\n')
        if not lines:
            return "Unknown"
        
        first_line = lines[0].strip()
        
        # Markdown header
        if first_line.startswith('#'):
            return first_line.lstrip('#').strip()
        
        # All caps header
        if first_line.isupper() and len(first_line) < 100:
            return first_line
        
        # Short line that might be a header
        if len(first_line) < 80 and first_line.endswith(':'):
            return first_line.rstrip(':')
        
        # Look for common section indicators
        section_keywords = ['introduction', 'overview', 'summary', 'conclusion', 'background', 
                          'methods', 'results', 'discussion', 'references', 'appendix']
        
        for keyword in section_keywords:
            if keyword in first_line.lower():
                return first_line
        
        return "Content"
