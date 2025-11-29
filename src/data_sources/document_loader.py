import os
from pathlib import Path
from typing import List, Dict
import PyPDF2
import docx
import aiofiles

class DocumentLoader:
    """Loads and extracts text from various document formats"""
    
    def __init__(self, documents_path: str = "./data/documents"):
        self.documents_path = Path(documents_path)
        # Create the directory if it doesn't exist
        self.documents_path.mkdir(parents=True, exist_ok=True)
        print(f"Document loader initialized. Looking for files in: {self.documents_path}")
    
    async def load_pdf(self, file_path: str) -> str:
        """Extract text from PDF file"""
        print(f"  Loading PDF: {Path(file_path).name}")
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page_num, page in enumerate(pdf_reader.pages, 1):
                text += page.extract_text()
                if page_num % 10 == 0:
                    print(f"    Processed {page_num}/{len(pdf_reader.pages)} pages")
        return text
    
    async def load_docx(self, file_path: str) -> str:
        """Extract text from Word document"""
        print(f"  Loading DOCX: {Path(file_path).name}")
        doc = docx.Document(file_path)
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        return text
    
    async def load_txt(self, file_path: str) -> str:
        """Load plain text file"""
        print(f"  Loading TXT: {Path(file_path).name}")
        async with aiofiles.open(file_path, 'r', encoding='utf-8') as file:
            text = await file.read()
        return text
    
    async def load_document(self, file_path: str) -> Dict:
        """Load any supported document type and return content + metadata"""
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Determine file type and load accordingly
        extension = path.suffix.lower()
        
        if extension == '.pdf':
            text = await self.load_pdf(str(path))
        elif extension == '.docx':
            text = await self.load_docx(str(path))
        elif extension == '.txt':
            text = await self.load_txt(str(path))
        else:
            raise ValueError(f"Unsupported file type: {extension}")
        
        return {
            'text': text,
            'filename': path.name,
            'path': str(path.absolute()),
            'type': extension,
            'size': len(text)
        }
    
    async def load_all_documents(self) -> List[Dict]:
        """Load all supported documents from the documents directory"""
        print(f"Scanning for documents in: {self.documents_path}")
        documents = []
        
        # Find all supported files recursively
        for file_path in self.documents_path.rglob('*'):
            if file_path.is_file() and file_path.suffix in ['.pdf', '.docx', '.txt']:
                try:
                    doc = await self.load_document(str(file_path))
                    documents.append(doc)
                    print(f"  ✓ Loaded: {doc['filename']} ({doc['size']:,} characters)")
                except Exception as e:
                    print(f"  ✗ Error loading {file_path.name}: {e}")
        
        print(f"✓ Loaded {len(documents)} documents total")
        return documents