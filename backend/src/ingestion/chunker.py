from typing import List, Dict, Any
import re
import tiktoken
from sentence_transformers import SentenceTransformer


class IntelligentChunker:
    """Intelligent content chunking with semantic awareness"""
    
    def __init__(self, 
                 chunk_size: int = 500, 
                 chunk_overlap: int = 100,
                 min_chunk_size: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size
        
        # Initialize tokenizer for token counting
        try:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")  # GPT-4 tokenizer
        except:
            self.tokenizer = None
    
    def chunk_content(self, 
                     content: str, 
                     source_type: str = "text",
                     metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Chunk content intelligently based on source type"""
        
        if not content or not content.strip():
            return []
        
        metadata = metadata or {}
        
        # Choose chunking strategy based on source type
        if source_type == "audio":
            return self._chunk_audio_transcript(content, metadata)
        elif source_type in ["pdf", "text"]:
            return self._chunk_document(content, metadata)
        elif source_type == "web":
            return self._chunk_web_content(content, metadata)
        elif source_type == "image":
            return self._chunk_ocr_text(content, metadata)
        else:
            return self._chunk_generic(content, metadata)
    
    def _chunk_audio_transcript(self, content: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Chunk audio transcript with speaker awareness"""
        
        chunks = []
        
        # Try to split by speaker changes or time markers
        # Look for patterns like "Speaker 1:", "[00:01:23]", etc.
        speaker_pattern = r'(Speaker \d+:|[A-Z][a-z]+ \d*:|\[\d{2}:\d{2}:\d{2}\])'
        
        if re.search(speaker_pattern, content):
            # Split by speaker/time markers
            segments = re.split(speaker_pattern, content)
            current_chunk = ""
            
            for i, segment in enumerate(segments):
                if not segment.strip():
                    continue
                
                if re.match(speaker_pattern, segment):
                    # This is a marker, start new chunk if current is large enough
                    if current_chunk and self._count_tokens(current_chunk) >= self.min_chunk_size:
                        chunks.append(self._create_chunk(current_chunk, metadata, len(chunks)))
                        current_chunk = segment
                    else:
                        current_chunk += segment
                else:
                    # This is content
                    current_chunk += segment
                    
                    # Check if chunk is getting too large
                    if self._count_tokens(current_chunk) >= self.chunk_size:
                        chunks.append(self._create_chunk(current_chunk, metadata, len(chunks)))
                        current_chunk = ""
            
            # Add remaining content
            if current_chunk.strip():
                chunks.append(self._create_chunk(current_chunk, metadata, len(chunks)))
        else:
            # No clear structure, use sentence-based chunking
            chunks = self._chunk_by_sentences(content, metadata)
        
        return chunks
    
    def _chunk_document(self, content: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Chunk document content with structure awareness"""
        
        # Try to identify document structure
        # Look for headers, sections, etc.
        header_patterns = [
            r'^#{1,6}\s+.+$',  # Markdown headers
            r'^\d+\.\s+.+$',   # Numbered sections
            r'^[A-Z][A-Z\s]+$', # ALL CAPS headers
            r'^\s*[A-Z][^.!?]*:$'  # Section headers ending with colon
        ]
        
        lines = content.split('\n')
        sections = []
        current_section = []
        
        for line in lines:
            is_header = any(re.match(pattern, line.strip(), re.MULTILINE) for pattern in header_patterns)
            
            if is_header and current_section:
                # Start new section
                sections.append('\n'.join(current_section))
                current_section = [line]
            else:
                current_section.append(line)
        
        # Add final section
        if current_section:
            sections.append('\n'.join(current_section))
        
        # Chunk each section
        chunks = []
        for section in sections:
            if section.strip():
                section_chunks = self._chunk_by_sentences(section, metadata)
                chunks.extend(section_chunks)
        
        return chunks
    
    def _chunk_web_content(self, content: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Chunk web content with paragraph awareness"""
        
        # Split by double newlines (paragraphs)
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        
        chunks = []
        current_chunk = ""
        
        for paragraph in paragraphs:
            # Check if adding this paragraph would exceed chunk size
            test_chunk = current_chunk + "\n\n" + paragraph if current_chunk else paragraph
            
            if self._count_tokens(test_chunk) <= self.chunk_size:
                current_chunk = test_chunk
            else:
                # Save current chunk and start new one
                if current_chunk:
                    chunks.append(self._create_chunk(current_chunk, metadata, len(chunks)))
                
                # If single paragraph is too large, split it
                if self._count_tokens(paragraph) > self.chunk_size:
                    para_chunks = self._chunk_by_sentences(paragraph, metadata)
                    chunks.extend(para_chunks)
                    current_chunk = ""
                else:
                    current_chunk = paragraph
        
        # Add remaining content
        if current_chunk:
            chunks.append(self._create_chunk(current_chunk, metadata, len(chunks)))
        
        return chunks
    
    def _chunk_ocr_text(self, content: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Chunk OCR text (often noisy)"""
        
        # OCR text is often fragmented, so use more conservative chunking
        return self._chunk_by_sentences(content, metadata)
    
    def _chunk_generic(self, content: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generic chunking strategy"""
        
        return self._chunk_by_sentences(content, metadata)
    
    def _chunk_by_sentences(self, content: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Chunk content by sentences with overlap"""
        
        # Split into sentences
        sentences = self._split_sentences(content)
        
        if not sentences:
            return []
        
        chunks = []
        current_chunk = []
        current_tokens = 0
        
        for sentence in sentences:
            sentence_tokens = self._count_tokens(sentence)
            
            # If adding this sentence would exceed chunk size
            if current_tokens + sentence_tokens > self.chunk_size and current_chunk:
                # Create chunk
                chunk_text = ' '.join(current_chunk)
                chunks.append(self._create_chunk(chunk_text, metadata, len(chunks)))
                
                # Start new chunk with overlap
                overlap_sentences = self._get_overlap_sentences(current_chunk)
                current_chunk = overlap_sentences + [sentence]
                current_tokens = sum(self._count_tokens(s) for s in current_chunk)
            else:
                current_chunk.append(sentence)
                current_tokens += sentence_tokens
        
        # Add remaining sentences
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            if self._count_tokens(chunk_text) >= self.min_chunk_size:
                chunks.append(self._create_chunk(chunk_text, metadata, len(chunks)))
        
        return chunks
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        
        # Simple sentence splitting (could be improved with spaCy/NLTK)
        sentence_endings = r'[.!?]+\s+'
        sentences = re.split(sentence_endings, text)
        
        # Clean and filter sentences
        sentences = [s.strip() for s in sentences if s.strip()]
        
        return sentences
    
    def _get_overlap_sentences(self, sentences: List[str]) -> List[str]:
        """Get sentences for overlap"""
        
        overlap_tokens = 0
        overlap_sentences = []
        
        # Take sentences from the end until we reach overlap size
        for sentence in reversed(sentences):
            sentence_tokens = self._count_tokens(sentence)
            if overlap_tokens + sentence_tokens <= self.chunk_overlap:
                overlap_sentences.insert(0, sentence)
                overlap_tokens += sentence_tokens
            else:
                break
        
        return overlap_sentences
    
    def _count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        
        if self.tokenizer:
            return len(self.tokenizer.encode(text))
        else:
            # Fallback: approximate token count
            return len(text.split()) * 1.3  # Rough approximation
    
    def _create_chunk(self, content: str, metadata: Dict[str, Any], index: int) -> Dict[str, Any]:
        """Create a chunk dictionary"""
        
        return {
            "content": content.strip(),
            "token_count": int(self._count_tokens(content)),
            "metadata": {
                **metadata,
                "chunk_index": index,
                "chunk_length": len(content),
            }
        }