"""
FastAPI REST API Server
Provides REST endpoints for frontend integration
"""

import os
import logging
from pathlib import Path
from typing import Optional, List
from datetime import datetime
import shutil

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, validator
from dotenv import load_dotenv

from database.client_manager import ClientManager
from agents.deadline_agent import DeadlineAgent
from agents.document_agent import DocumentAgent
from agents.smartcontext_agent import SmartContextAgent
from data_sources.document_loader import DocumentLoader
from data_sources.vector_store import VectorStore

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="RAG MCP Server API",
    description="REST API for legal document processing and client management",
    version="1.0.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",
        "https://*. ngrok.io",
        "https://lovable.dev",
        "https://*. lovable.dev",
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
client_manager = ClientManager()
deadline_agent = DeadlineAgent()
document_agent = DocumentAgent()
smartcontext_agent = SmartContextAgent()
document_loader = DocumentLoader()
vector_store = VectorStore()

# Pydantic models for request/response
class ClientCreate(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    company: Optional[str] = None

class ClientUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    active: Optional[bool] = None

class ClientResponse(BaseModel):
    id: str
    name: str
    email: str
    phone: Optional[str]
    company: Optional[str]
    active: bool
    created_at: str

class DeadlineStats(BaseModel):
    total: int
    overdue: int
    critical: int
    high: int
    medium: int
    low: int

class DocumentStats(BaseModel):
    total: int
    contract: int
    invoice: int
    email: int
    report: int
    memo: int
    legal: int
    other: int

# File upload validation
ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.txt', '.eml'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

def validate_file(file: UploadFile) -> None:
    """Validate uploaded file type and size"""
    # Check extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type {file_ext} not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Check size (approximate check using content-length header)
    # Note: For exact size, we'd need to read the entire file
    if file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File size exceeds maximum allowed size of {MAX_FILE_SIZE / 1024 / 1024}MB"
        )

def get_client_document_dir(client_id: str) -> Path:
    """Get or create document directory for a client"""
    base_dir = Path("./data/documents")
    client_dir = base_dir / f"client_{client_id}"
    client_dir.mkdir(parents=True, exist_ok=True)
    return client_dir

# API Endpoints

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "RAG MCP Server API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# Client Management Endpoints

@app.post("/api/clients", response_model=ClientResponse)
async def create_client(client: ClientCreate):
    """Create a new client"""
    try:
        logger.info(f"Creating client: {client.email}")
        result = await client_manager.create_client(
            name=client.name,
            email=client.email,
            phone=client.phone,
            company=client.company
        )
        logger.info(f"Client created: {result['id']}")
        return result
    except Exception as e:
        logger.error(f"Error creating client: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/clients", response_model=List[ClientResponse])
async def get_all_clients(active_only: bool = True):
    """Get all clients"""
    try:
        logger.info(f"Fetching clients (active_only={active_only})")
        clients = await client_manager.get_all_clients(active_only=active_only)
        return clients
    except Exception as e:
        logger.error(f"Error fetching clients: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/clients/{client_id}", response_model=ClientResponse)
async def get_client(client_id: str):
    """Get a specific client"""
    try:
        logger.info(f"Fetching client: {client_id}")
        client = await client_manager.get_client(client_id)
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        return client
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching client: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/clients/{client_id}", response_model=ClientResponse)
async def update_client(client_id: str, client_update: ClientUpdate):
    """Update a client"""
    try:
        logger.info(f"Updating client: {client_id}")
        # Convert to dict and remove None values
        update_data = {k: v for k, v in client_update.dict().items() if v is not None}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        result = await client_manager.update_client(client_id, update_data)
        logger.info(f"Client updated: {client_id}")
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating client: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/clients/{client_id}", response_model=ClientResponse)
async def delete_client(client_id: str):
    """Soft delete a client"""
    try:
        logger.info(f"Deleting client: {client_id}")
        result = await client_manager.delete_client(client_id)
        logger.info(f"Client deleted: {client_id}")
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting client: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Document Upload Endpoint

@app.post("/api/clients/{client_id}/documents")
async def upload_document(
    client_id: str,
    file: UploadFile = File(...)
):
    """
    Upload a document for a client.
    Automatically processes, classifies, and extracts deadlines.
    """
    try:
        logger.info(f"Uploading document for client {client_id}: {file.filename}")
        
        # Verify client exists
        client = await client_manager.get_client(client_id)
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        # Validate file
        validate_file(file)
        
        # Get client document directory
        client_dir = get_client_document_dir(client_id)
        
        # Save file
        file_path = client_dir / file.filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"File saved: {file_path}")
        
        # Load document
        doc = await document_loader.load_document(str(file_path))
        
        # Create chunks for vector store
        chunks = chunk_text(doc['text'])
        
        # Create metadata for chunks
        metadata = [
            {
                'filename': doc['filename'],
                'path': doc['path'],
                'type': doc['type'],
                'client_id': client_id,
                'chunk_index': i,
                'total_chunks': len(chunks)
            }
            for i in range(len(chunks))
        ]
        
        # Add to vector store
        chunk_count = await vector_store.add_documents(chunks, metadata)
        logger.info(f"Added {chunk_count} chunks to vector store")
        
        # Classify document
        classification_result = await document_agent.classify_document(
            document_id=doc['filename'],
            filename=doc['filename'],
            extracted_text=doc['text'],
            metadata={'path': doc['path'], 'type': doc['type']},
            client_id=client_id
        )
        
        # Extract deadlines
        deadline_result = await deadline_agent.extract_deadlines(
            text=doc['text'],
            source_id=f"document:{doc['filename']}",
            client_id=client_id
        )
        
        logger.info(f"Document processed successfully: {file.filename}")
        
        return {
            "success": True,
            "filename": doc['filename'],
            "client_id": client_id,
            "chunks_created": chunk_count,
            "classification": classification_result['classification'],
            "deadlines_extracted": deadline_result['count'],
            "deadlines": deadline_result['deadlines']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Data Retrieval Endpoints (filtered by client)

@app.get("/api/clients/{client_id}/documents")
async def get_client_documents(
    client_id: str,
    doc_type: Optional[str] = None,
    limit: int = 50
):
    """Get documents for a client"""
    try:
        logger.info(f"Fetching documents for client: {client_id}")
        
        # Verify client exists
        client = await client_manager.get_client(client_id)
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        documents = await document_agent.search_documents(
            doc_type=doc_type,
            limit=limit,
            client_id=client_id
        )
        
        return {
            "client_id": client_id,
            "count": len(documents),
            "documents": documents
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/clients/{client_id}/deadlines")
async def get_client_deadlines(
    client_id: str,
    risk_level: Optional[str] = None
):
    """Get deadlines for a client"""
    try:
        logger.info(f"Fetching deadlines for client: {client_id}")
        
        # Verify client exists
        client = await client_manager.get_client(client_id)
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        deadlines = await deadline_agent.get_deadlines_by_risk(
            risk_level=risk_level,
            client_id=client_id
        )
        
        return {
            "client_id": client_id,
            "count": len(deadlines),
            "deadlines": deadlines
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching deadlines: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/clients/{client_id}/deadlines/stats", response_model=DeadlineStats)
async def get_client_deadline_stats(client_id: str):
    """Get deadline statistics for a client"""
    try:
        logger.info(f"Fetching deadline stats for client: {client_id}")
        
        # Verify client exists
        client = await client_manager.get_client(client_id)
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        stats = await deadline_agent.get_stats(client_id=client_id)
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching deadline stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/clients/{client_id}/documents/classified")
async def get_classified_documents(
    client_id: str,
    doc_type: Optional[str] = None
):
    """Get classified documents for a client"""
    try:
        logger.info(f"Fetching classified documents for client: {client_id}")
        
        # Verify client exists
        client = await client_manager.get_client(client_id)
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        documents = await document_agent.search_documents(
            doc_type=doc_type,
            client_id=client_id
        )
        
        return {
            "client_id": client_id,
            "count": len(documents),
            "documents": documents
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching classified documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/clients/{client_id}/documents/stats", response_model=DocumentStats)
async def get_client_document_stats(client_id: str):
    """Get document statistics for a client"""
    try:
        logger.info(f"Fetching document stats for client: {client_id}")
        
        # Verify client exists
        client = await client_manager.get_client(client_id)
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        stats = await document_agent.get_document_stats(client_id=client_id)
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching document stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/clients/{client_id}/analysis")
async def get_client_analysis(
    client_id: str,
    analysis_type: Optional[str] = None,
    limit: int = 10
):
    """Get strategic analysis for a client"""
    try:
        logger.info(f"Fetching analysis for client: {client_id}")
        
        # Verify client exists
        client = await client_manager.get_client(client_id)
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        # Get analyses (using firm_id = "default" for now)
        analyses = await smartcontext_agent.get_recent_analyses(
            firm_id="default",
            analysis_type=analysis_type,
            limit=limit,
            client_id=client_id
        )
        
        return {
            "client_id": client_id,
            "count": len(analyses),
            "analyses": analyses
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Helper function for text chunking
def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """
    Split text into overlapping chunks for better context preservation.
    """
    chunks = []
    start = 0
    text_length = len(text)
    
    while start < text_length:
        end = start + chunk_size
        chunk = text[start:end]
        
        # Try to break at sentence boundary
        if end < text_length:
            last_period = chunk.rfind('. ')
            last_newline = chunk.rfind('\n\n')
            last_question = chunk.rfind('? ')
            last_exclamation = chunk.rfind('! ')
            
            break_point = max(last_period, last_newline, last_question, last_exclamation)
            
            if break_point > chunk_size * 0.5:
                chunk = chunk[:break_point + 1]
                end = start + break_point + 1
        
        chunks.append(chunk.strip())
        start = end - overlap
    
    return [c for c in chunks if c]

# Run the server
if __name__ == "__main__":
    import uvicorn
    
    logger.info("Starting RAG MCP Server API...")
    logger.info("API Documentation available at: http://localhost:8000/docs")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
