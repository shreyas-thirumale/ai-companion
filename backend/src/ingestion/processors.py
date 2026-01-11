from abc import ABC, abstractmethod
from typing import Dict, Any
import os
import requests
from bs4 import BeautifulSoup
import PyPDF2
import docx
import whisper
import pytesseract
from PIL import Image

from src.config import settings


class BaseProcessor(ABC):
    """Base class for content processors"""
    
    @abstractmethod
    def process(self, source_path: str) -> Dict[str, Any]:
        """Process content and return structured data"""
        pass


class AudioProcessor(BaseProcessor):
    """Process audio files using Whisper"""
    
    def __init__(self):
        self.model = whisper.load_model("base")
    
    def process(self, source_path: str) -> Dict[str, Any]:
        """Transcribe audio file"""
        
        if not os.path.exists(source_path):
            raise FileNotFoundError(f"Audio file not found: {source_path}")
        
        # Transcribe using Whisper
        result = self.model.transcribe(source_path)
        
        # Extract metadata
        metadata = {
            "duration": result.get("duration", 0),
            "language": result.get("language", "unknown"),
            "segments": len(result.get("segments", [])),
            "original_file": os.path.basename(source_path)
        }
        
        return {
            "content": result["text"],
            "title": os.path.splitext(os.path.basename(source_path))[0],
            "metadata": metadata
        }


class DocumentProcessor(BaseProcessor):
    """Process PDF and Word documents"""
    
    def process(self, source_path: str) -> Dict[str, Any]:
        """Extract text from document"""
        
        if not os.path.exists(source_path):
            raise FileNotFoundError(f"Document not found: {source_path}")
        
        file_ext = os.path.splitext(source_path)[1].lower()
        
        if file_ext == '.pdf':
            return self._process_pdf(source_path)
        elif file_ext == '.docx':
            return self._process_docx(source_path)
        else:
            raise ValueError(f"Unsupported document type: {file_ext}")
    
    def _process_pdf(self, source_path: str) -> Dict[str, Any]:
        """Process PDF file"""
        
        with open(source_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            
            # Extract text
            text_content = []
            for page in reader.pages:
                text_content.append(page.extract_text())
            
            content = "\n\n".join(text_content)
            
            # Extract metadata
            metadata = {
                "pages": len(reader.pages),
                "original_file": os.path.basename(source_path)
            }
            
            # Try to get PDF metadata
            if reader.metadata:
                metadata.update({
                    "pdf_title": reader.metadata.get("/Title", ""),
                    "pdf_author": reader.metadata.get("/Author", ""),
                    "pdf_creator": reader.metadata.get("/Creator", ""),
                    "pdf_producer": reader.metadata.get("/Producer", "")
                })
            
            return {
                "content": content,
                "title": metadata.get("pdf_title") or os.path.splitext(os.path.basename(source_path))[0],
                "author": metadata.get("pdf_author"),
                "metadata": metadata
            }
    
    def _process_docx(self, source_path: str) -> Dict[str, Any]:
        """Process Word document"""
        
        doc = docx.Document(source_path)
        
        # Extract text
        paragraphs = [paragraph.text for paragraph in doc.paragraphs if paragraph.text.strip()]
        content = "\n\n".join(paragraphs)
        
        # Extract metadata
        metadata = {
            "paragraphs": len(paragraphs),
            "original_file": os.path.basename(source_path)
        }
        
        # Try to get document properties
        if hasattr(doc.core_properties, 'title'):
            metadata["doc_title"] = doc.core_properties.title
        if hasattr(doc.core_properties, 'author'):
            metadata["doc_author"] = doc.core_properties.author
        
        return {
            "content": content,
            "title": metadata.get("doc_title") or os.path.splitext(os.path.basename(source_path))[0],
            "author": metadata.get("doc_author"),
            "metadata": metadata
        }


class TextProcessor(BaseProcessor):
    """Process plain text files"""
    
    def process(self, source_path: str) -> Dict[str, Any]:
        """Read and process text file"""
        
        if not os.path.exists(source_path):
            raise FileNotFoundError(f"Text file not found: {source_path}")
        
        # Try different encodings
        encodings = ['utf-8', 'utf-16', 'latin-1', 'cp1252']
        content = None
        
        for encoding in encodings:
            try:
                with open(source_path, 'r', encoding=encoding) as file:
                    content = file.read()
                break
            except UnicodeDecodeError:
                continue
        
        if content is None:
            raise ValueError("Could not decode text file with any supported encoding")
        
        # Extract metadata
        metadata = {
            "file_size": os.path.getsize(source_path),
            "line_count": len(content.splitlines()),
            "character_count": len(content),
            "original_file": os.path.basename(source_path)
        }
        
        return {
            "content": content,
            "title": os.path.splitext(os.path.basename(source_path))[0],
            "metadata": metadata
        }


class WebProcessor(BaseProcessor):
    """Process web content from URLs"""
    
    def process(self, source_path: str) -> Dict[str, Any]:
        """Scrape and process web content"""
        
        # source_path is actually a URL for web content
        url = source_path
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Extract title
            title = soup.find('title')
            title_text = title.get_text().strip() if title else url
            
            # Extract main content
            # Try to find main content areas
            content_selectors = [
                'main', 'article', '.content', '#content', 
                '.post-content', '.entry-content', '.article-content'
            ]
            
            content_element = None
            for selector in content_selectors:
                content_element = soup.select_one(selector)
                if content_element:
                    break
            
            # Fallback to body if no main content found
            if not content_element:
                content_element = soup.find('body')
            
            # Extract text
            if content_element:
                content = content_element.get_text(separator='\n', strip=True)
            else:
                content = soup.get_text(separator='\n', strip=True)
            
            # Clean up content
            lines = [line.strip() for line in content.splitlines() if line.strip()]
            content = '\n'.join(lines)
            
            # Extract metadata
            metadata = {
                "url": url,
                "title_tag": title_text,
                "content_length": len(content),
                "response_status": response.status_code,
                "content_type": response.headers.get('content-type', ''),
            }
            
            # Try to extract meta description
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc:
                metadata["description"] = meta_desc.get('content', '')
            
            return {
                "content": content,
                "title": title_text,
                "metadata": metadata
            }
            
        except requests.RequestException as e:
            raise ValueError(f"Failed to fetch URL {url}: {str(e)}")
        except Exception as e:
            raise ValueError(f"Failed to process web content: {str(e)}")


class ImageProcessor(BaseProcessor):
    """Process images with OCR"""
    
    def process(self, source_path: str) -> Dict[str, Any]:
        """Extract text from image using OCR"""
        
        if not os.path.exists(source_path):
            raise FileNotFoundError(f"Image file not found: {source_path}")
        
        try:
            # Open image
            image = Image.open(source_path)
            
            # Extract text using OCR
            ocr_text = pytesseract.image_to_string(image)
            
            # Get image info
            width, height = image.size
            format_name = image.format
            mode = image.mode
            
            # Extract metadata
            metadata = {
                "width": width,
                "height": height,
                "format": format_name,
                "mode": mode,
                "file_size": os.path.getsize(source_path),
                "original_file": os.path.basename(source_path)
            }
            
            # Try to get EXIF data
            if hasattr(image, '_getexif'):
                exif = image._getexif()
                if exif:
                    metadata["exif"] = {k: v for k, v in exif.items() if isinstance(v, (str, int, float))}
            
            return {
                "content": ocr_text.strip(),
                "title": os.path.splitext(os.path.basename(source_path))[0],
                "metadata": metadata
            }
            
        except Exception as e:
            raise ValueError(f"Failed to process image: {str(e)}")