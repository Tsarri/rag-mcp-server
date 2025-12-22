"""
FastAPI REST API Server
Provides REST endpoints for frontend integration
"""

import os
import logging
from pathlib import Path
from typing import Optional, List
from datetime import datetime, timezone
import shutil

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, validator
from dotenv import load_dotenv
from supabase import create_client, Client

from database.client_manager import ClientManager
from agents.deadline_agent import DeadlineAgent
from agents.document_agent import DocumentAgent
from agents.smartcontext_agent import SmartContextAgent
from agents.gemini_preprocessor import GeminiPreprocessor
from agents.gemini_validator import GeminiValidator
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
gemini_preprocessor = GeminiPreprocessor()
gemini_validator = GeminiValidator()
document_loader = DocumentLoader()
vector_store = VectorStore()

# Initialize Supabase client for direct DB access
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_KEY')
if not supabase_url or not supabase_key:
    raise ValueError("Missing Supabase credentials (SUPABASE_URL, SUPABASE_KEY)")
supabase: Client = create_client(supabase_url, supabase_key)

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

class UrgentDeadline(BaseModel):
    id: str
    date: str
    description: str
    working_days_remaining: int
    risk_level: str
    client_id: Optional[str]
    client_name: Optional[str]
    client_email: Optional[str]

class UrgentDeadlinesResponse(BaseModel):
    count: int
    deadlines: List[UrgentDeadline]

class DeletionSummary(BaseModel):
    documents_deleted: int
    deadlines_deleted: int
    validations_deleted: int
    extractions_deleted: int
    files_deleted: int

class PermanentDeleteResponse(BaseModel):
    success: bool
    message: str
    client_id: str
    deletion_summary: DeletionSummary

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
    """Soft delete a client (sets active=false)"""
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

@app.delete("/api/clients/{client_id}/permanent", response_model=PermanentDeleteResponse)
async def delete_client_permanent(client_id: str):
    """
    Permanently delete a client and ALL associated data:
    1. Get all documents for the client
    2. Get all deadlines for the client
    3. Delete validations for all deadlines
    4. Delete validations for all document classifications
    5. Delete all gemini extractions
    6. Delete all deadlines
    7. Delete all documents from database
    8. Delete all local files and client directory
    9. Delete client record
    """
    try:
        logger.info(f"Permanently deleting client {client_id} and all associated data")
        
        # Verify client exists
        client = await client_manager.get_client(client_id)
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        # Track deletion counts for response
        deletion_summary = {
            "documents_deleted": 0,
            "deadlines_deleted": 0,
            "validations_deleted": 0,
            "extractions_deleted": 0,
            "files_deleted": 0
        }
        
        # 1. Get all documents for this client
        try:
            docs_response = supabase.table('documents') \
                .select('document_id') \
                .eq('client_id', client_id) \
                .execute()
            
            document_ids = [doc['document_id'] for doc in docs_response.data] if docs_response.data else []
            deletion_summary["documents_deleted"] = len(document_ids)
            logger.info(f"Found {len(document_ids)} documents to delete")
        except Exception as e:
            logger.warning(f"Error fetching documents: {e}")
            document_ids = []
        
        # 2. Get all deadlines for this client (for validation cleanup)
        try:
            deadlines_response = supabase.table('deadlines') \
                .select('id') \
                .eq('client_id', client_id) \
                .execute()
            
            deadline_ids = [d['id'] for d in deadlines_response.data] if deadlines_response.data else []
            deletion_summary["deadlines_deleted"] = len(deadline_ids)
            logger.info(f"Found {len(deadline_ids)} deadlines to delete")
        except Exception as e:
            logger.warning(f"Error fetching deadlines: {e}")
            deadline_ids = []
        
        # 3. Delete all validations for deadlines (bulk deletion)
        if deadline_ids:
            try:
                # Use bulk deletion by matching any deadline_id in the list
                validations_response = supabase.table('validations') \
                    .delete() \
                    .eq('validation_type', 'deadline') \
                    .in_('entity_id', deadline_ids) \
                    .execute()
                validations_count = len(validations_response.data) if validations_response.data else 0
                logger.info(f"Deleted {validations_count} validations for {len(deadline_ids)} deadlines")
                deletion_summary["validations_deleted"] += validations_count
            except Exception as e:
                logger.warning(f"Error deleting deadline validations: {e}")
        
        # 4. Delete all validations for document classifications (bulk deletion)
        if document_ids:
            try:
                # Use bulk deletion by matching any document_id in the list
                validations_response = supabase.table('validations') \
                    .delete() \
                    .eq('validation_type', 'classification') \
                    .in_('entity_id', document_ids) \
                    .execute()
                validations_count = len(validations_response.data) if validations_response.data else 0
                logger.info(f"Deleted {validations_count} validations for {len(document_ids)} documents")
                deletion_summary["validations_deleted"] += validations_count
            except Exception as e:
                logger.warning(f"Error deleting classification validations: {e}")
        
        # 5. Delete all gemini extractions
        try:
            extractions_response = supabase.table('gemini_extractions') \
                .delete() \
                .eq('client_id', client_id) \
                .execute()
            extraction_count = len(extractions_response.data) if extractions_response.data else 0
            deletion_summary["extractions_deleted"] = extraction_count
            logger.info(f"Deleted {extraction_count} gemini extractions")
        except Exception as e:
            logger.warning(f"Error deleting gemini extractions: {e}")
        
        # 6. Delete all deadlines
        try:
            supabase.table('deadlines') \
                .delete() \
                .eq('client_id', client_id) \
                .execute()
            logger.info(f"Deleted {len(deadline_ids)} deadlines")
        except Exception as e:
            logger.warning(f"Error deleting deadlines: {e}")
        
        # 7. Delete all documents from database
        try:
            supabase.table('documents') \
                .delete() \
                .eq('client_id', client_id) \
                .execute()
            logger.info(f"Deleted {len(document_ids)} document records")
        except Exception as e:
            logger.warning(f"Error deleting documents: {e}")
        
        # 8. Delete all local files and client directory
        try:
            client_dir = get_client_document_dir(client_id)
            if client_dir.exists():
                file_count = sum(1 for _ in client_dir.iterdir())
                shutil.rmtree(client_dir)
                deletion_summary["files_deleted"] = file_count
                logger.info(f"Deleted client directory with {file_count} files: {client_dir}")
            else:
                logger.info(f"No local directory found for client: {client_id}")
        except Exception as e:
            logger.warning(f"Error deleting client directory: {e}")
        
        # 9. Delete client record
        try:
            supabase.table('clients') \
                .delete() \
                .eq('id', client_id) \
                .execute()
            logger.info(f"Deleted client record: {client_id}")
        except Exception as e:
            logger.error(f"Error deleting client record: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to delete client: {str(e)}")
        
        logger.info(f"Successfully deleted client {client_id} and all associated data")
        
        return {
            "success": True,
            "message": "Client and all associated data permanently deleted",
            "client_id": client_id,
            "deletion_summary": deletion_summary
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error permanently deleting client: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete client: {str(e)}")

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
        
        # STEP 1: Gemini Preprocessing
        gemini_extraction = await gemini_preprocessor.extract_structured_data(
            text=doc['text'],
            filename=doc['filename']
        )
        
        # Store Gemini extraction in database
        extraction_id = None
        if gemini_extraction['success']:
            try:
                extraction_record = supabase.table('gemini_extractions').insert({
                    'client_id': client_id,
                    'document_id': doc['filename'],
                    'extracted_data': gemini_extraction['data'],
                    'model_version': 'gemini-1.5-pro'
                }).execute()
                
                extraction_id = extraction_record.data[0]['id'] if extraction_record.data else None
                logger.info(f"Stored Gemini extraction: {extraction_id}")
            except Exception as e:
                logger.error(f"Failed to store Gemini extraction: {str(e)}")
        
        # STEP 2: Claude Processing with Gemini Context
        gemini_context = gemini_extraction['data'] if gemini_extraction['success'] else None
        
        # Classify document with Gemini context
        classification_result = await document_agent.classify_document(
            document_id=doc['filename'],
            filename=doc['filename'],
            extracted_text=doc['text'],
            metadata={'path': doc['path'], 'type': doc['type']},
            client_id=client_id,
            gemini_context=gemini_context
        )
        
        # Extract deadlines with Gemini context
        deadline_result = await deadline_agent.extract_deadlines(
            text=doc['text'],
            source_id=f"document:{doc['filename']}",
            client_id=client_id,
            gemini_context=gemini_context
        )
        
        # STEP 3: Gemini Validation
        classification_validation = None
        deadline_validation = None
        
        # Validate classification
        classification_validation = await gemini_validator.validate_classification(
            claude_output=classification_result['classification'],
            original_text=doc['text'],
            gemini_extraction=gemini_context
        )
        
        # Store classification validation
        try:
            supabase.table('validations').insert({
                'validation_type': 'classification',
                'entity_id': doc['filename'],
                'client_id': client_id,
                'extraction_id': extraction_id,
                'validation_status': classification_validation['validation_status'],
                'confidence_score': classification_validation['confidence_score'],
                'feedback': classification_validation['feedback'],
                'verified_items': classification_validation['verified_items'],
                'discrepancies': classification_validation['discrepancies'],
                'missing_information': classification_validation['missing_information']
            }).execute()
            logger.info("Stored classification validation")
        except Exception as e:
            logger.error(f"Failed to store classification validation: {str(e)}")
        
        # Validate deadlines
        deadline_validation = await gemini_validator.validate_deadlines(
            claude_deadlines=deadline_result['deadlines'],
            original_text=doc['text'],
            gemini_extraction=gemini_context
        )
        
        # Store individual validation for EACH deadline with its actual ID
        # Note: The validation is performed on all deadlines collectively, but we store
        # the same validation result for each deadline ID. This allows the frontend to
        # query validation by individual deadline ID (e.g., /api/validations/deadline/{deadline_id})
        try:
            for deadline in deadline_result['deadlines']:
                deadline_id = deadline.get('id')
                if deadline_id:
                    supabase.table('validations').insert({
                        'validation_type': 'deadline',
                        'entity_id': deadline_id,  # Use actual deadline ID
                        'client_id': client_id,
                        'extraction_id': extraction_id,
                        'validation_status': deadline_validation['validation_status'],
                        'confidence_score': deadline_validation['confidence_score'],
                        'feedback': deadline_validation['feedback'],
                        'verified_items': deadline_validation['verified_items'],
                        'discrepancies': deadline_validation['discrepancies'],
                        'missing_information': deadline_validation['missing_information']
                    }).execute()
                    logger.info(f"Stored deadline validation for: {deadline_id}")
                else:
                    logger.warning(f"Deadline missing ID, cannot store validation: {deadline}")
        except Exception as e:
            logger.error(f"Failed to store deadline validations: {str(e)}")
        
        logger.info(f"Document processed successfully: {file.filename}")
        
        return {
            "success": True,
            "document_id": doc['filename'],  # Frontend requires document_id for deletion operations
            "filename": doc['filename'],
            "client_id": client_id,
            "chunks_created": chunk_count,
            "classification": classification_result['classification'],
            "deadlines_extracted": deadline_result['count'],
            "deadlines": deadline_result['deadlines'],
            "gemini_extraction_id": extraction_id,
            "classification_validation": classification_validation,
            "deadline_validation": deadline_validation
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

@app.delete("/api/clients/{client_id}/documents/{document_id}")
async def delete_client_document(client_id: str, document_id: str):
    """
    Delete a document completely:
    - Remove validations (for deadlines and classification)
    - Remove associated deadlines (linked via source_id pattern)
    - Remove Gemini extractions
    - Remove from documents table
    - Delete actual file from local storage
    """
    try:
        logger.info(f"Deleting document {document_id} for client {client_id}")
        
        # Verify client exists
        client = await client_manager.get_client(client_id)
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        # 1. Get document info (to get filename for file deletion)
        doc_response = supabase.table('documents') \
            .select('*') \
            .eq('document_id', document_id) \
            .eq('client_id', client_id) \
            .execute()
        
        if not doc_response.data or len(doc_response.data) == 0:
            raise HTTPException(status_code=404, detail="Document not found")
        
        document = doc_response.data[0]
        filename = document.get('filename')
        
        # 2. Get deadline IDs before deleting them (for validation cleanup)
        deadline_ids = []
        source_id_pattern = f"document:{document_id}"
        try:
            deadline_response = supabase.table('deadlines') \
                .select('id') \
                .eq('source_id', source_id_pattern) \
                .eq('client_id', client_id) \
                .execute()
            
            deadline_ids = [d['id'] for d in deadline_response.data] if deadline_response.data else []
            logger.info(f"Found {len(deadline_ids)} deadlines to clean up")
        except Exception as e:
            logger.warning(f"Could not fetch deadline IDs: {e}")
        
        # 3. Delete validations for all deadlines
        if deadline_ids:
            try:
                for deadline_id in deadline_ids:
                    supabase.table('validations') \
                        .delete() \
                        .eq('validation_type', 'deadline') \
                        .eq('entity_id', deadline_id) \
                        .eq('client_id', client_id) \
                        .execute()
                logger.info(f"Deleted deadline validations for {len(deadline_ids)} deadlines")
            except Exception as validation_error:
                logger.warning(f"Error deleting deadline validations: {validation_error}")
        
        # 4. Delete classification validation for the document
        try:
            supabase.table('validations') \
                .delete() \
                .eq('validation_type', 'classification') \
                .eq('entity_id', document_id) \
                .eq('client_id', client_id) \
                .execute()
            logger.info(f"Deleted classification validation for document: {document_id}")
        except Exception as validation_error:
            logger.warning(f"Error deleting classification validation: {validation_error}")
        
        # 5. Delete Gemini extractions for the document
        try:
            supabase.table('gemini_extractions') \
                .delete() \
                .eq('document_id', document_id) \
                .eq('client_id', client_id) \
                .execute()
            logger.info(f"Deleted Gemini extractions for document: {document_id}")
        except Exception as extraction_error:
            logger.warning(f"Error deleting Gemini extractions: {extraction_error}")
        
        # 6. Delete associated deadlines
        try:
            supabase.table('deadlines') \
                .delete() \
                .eq('source_id', source_id_pattern) \
                .eq('client_id', client_id) \
                .execute()
            logger.info(f"Deleted {len(deadline_ids)} deadlines for document: {document_id}")
        except Exception as deadline_error:
            logger.warning(f"Error deleting deadlines: {deadline_error}")
        
        # 7. Delete from documents table
        supabase.table('documents') \
            .delete() \
            .eq('document_id', document_id) \
            .eq('client_id', client_id) \
            .execute()
        
        logger.info(f"Deleted document record from database: {document_id}")
        
        # 8. Delete actual file from local storage
        if filename:
            try:
                client_dir = get_client_document_dir(client_id)
                file_path = client_dir / filename
                
                if file_path.exists():
                    file_path.unlink()
                    logger.info(f"Deleted file from storage: {file_path}")
                else:
                    logger.warning(f"File not found in storage: {file_path}")
            except Exception as storage_error:
                # Log but don't fail if file doesn't exist in storage
                logger.warning(f"Could not delete file from storage: {storage_error}")
        
        return {
            "success": True,
            "message": "Document and all related data deleted successfully",
            "document_id": document_id,
            "deadlines_deleted": len(deadline_ids),
            "validations_deleted": len(deadline_ids) + 1  # deadline validations + classification
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")

@app.get("/api/clients/{client_id}/deadlines")
async def get_client_deadlines(
    client_id: str,
    risk_level: Optional[str] = None,
    completed: Optional[str] = "false"
):
    """Get deadlines for a client"""
    try:
        logger.info(f"Fetching deadlines for client: {client_id}, completed filter: {completed}")
        
        # Verify client exists
        client = await client_manager.get_client(client_id)
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        # Build query
        query = supabase.table('deadlines').select('*').eq('client_id', client_id)
        
        # Apply completed filter
        if completed == "true":
            query = query.eq('completed', True)
        elif completed == "false":
            query = query.eq('completed', False)
        # If "all", don't filter by completed status
        
        # Apply risk level filter if provided
        if risk_level:
            query = query.eq('risk_level', risk_level)
        
        # Order by date
        query = query.order('date', desc=False)
        
        response = query.execute()
        deadlines = response.data
        
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

@app.patch("/api/clients/{client_id}/deadlines/{deadline_id}/complete")
async def mark_deadline_complete(client_id: str, deadline_id: str):
    """Mark a deadline as completed"""
    try:
        logger.info(f"Marking deadline {deadline_id} as completed for client {client_id}")
        
        # Verify client exists
        client = await client_manager.get_client(client_id)
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        # Verify deadline exists and belongs to client
        deadline_check = supabase.table('deadlines')\
            .select('*')\
            .eq('id', deadline_id)\
            .eq('client_id', client_id)\
            .execute()
        
        if not deadline_check.data:
            raise HTTPException(status_code=404, detail="Deadline not found")
        
        # Update deadline to completed
        update_response = supabase.table('deadlines')\
            .update({
                'completed': True,
                'completed_at': datetime.now(timezone.utc).isoformat()
            })\
            .eq('id', deadline_id)\
            .execute()
        
        if not update_response.data:
            raise HTTPException(status_code=500, detail="Failed to mark deadline as completed")
        
        return {
            "success": True,
            "deadline_id": deadline_id,
            "completed": True,
            "message": "Deadline marked as completed"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking deadline complete: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.patch("/api/clients/{client_id}/deadlines/{deadline_id}/uncomplete")
async def mark_deadline_uncomplete(client_id: str, deadline_id: str):
    """Restore a completed deadline back to active status"""
    try:
        logger.info(f"Restoring deadline {deadline_id} to active for client {client_id}")
        
        # Verify client exists
        client = await client_manager.get_client(client_id)
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        # Verify deadline exists and belongs to client
        deadline_check = supabase.table('deadlines')\
            .select('*')\
            .eq('id', deadline_id)\
            .eq('client_id', client_id)\
            .execute()
        
        if not deadline_check.data:
            raise HTTPException(status_code=404, detail="Deadline not found")
        
        # Update deadline to not completed
        update_response = supabase.table('deadlines')\
            .update({
                'completed': False,
                'completed_at': None
            })\
            .eq('id', deadline_id)\
            .execute()
        
        if not update_response.data:
            raise HTTPException(status_code=500, detail="Failed to restore deadline")
        
        return {
            "success": True,
            "deadline_id": deadline_id,
            "completed": False,
            "message": "Deadline restored to active"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error restoring deadline: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/urgent-deadlines", response_model=UrgentDeadlinesResponse)
async def get_urgent_deadlines(limit: int = 10):
    """Get the most urgent deadlines across all clients"""
    try:
        logger.info(f"Fetching top {limit} urgent deadlines across all clients")
        
        # Build query with proper risk level sorting
        # Supabase doesn't support CASE in ORDER BY, so we'll fetch and sort in Python
        # Fetch 3x limit to ensure we have enough after sorting by risk level
        query = supabase.table('deadlines')\
            .select('*, clients(name, email)')\
            .eq('completed', False)\
            .limit(max(limit * 3, 50))  # At least 50 for small limit values
        
        response = query.execute()
        deadlines = response.data
        
        # Sort in Python to ensure correct risk level priority
        risk_priority = {
            'overdue': 1,
            'critical': 2,
            'high': 3,
            'medium': 4,
            'low': 5
        }
        
        sorted_deadlines = sorted(
            deadlines,
            key=lambda d: (
                risk_priority.get(d.get('risk_level', ''), 999),
                d.get('date', '')
            )
        )[:limit]
        
        # Transform to include client info
        result = []
        for dl in sorted_deadlines:
            # Extract client info safely
            client_info = dl.get('clients') or {}
            if not isinstance(client_info, dict):
                client_info = {}
            
            result.append({
                'id': dl['id'],
                'date': dl['date'],
                'description': dl.get('description', ''),
                'working_days_remaining': dl.get('working_days_remaining', 0),
                'risk_level': dl.get('risk_level', 'low'),
                'client_id': dl.get('client_id'),
                'client_name': client_info.get('name'),
                'client_email': client_info.get('email')
            })
        
        return {
            'count': len(result),
            'deadlines': result
        }
        
    except Exception as e:
        logger.error(f"Error fetching urgent deadlines: {str(e)}")
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
@app.get("/api/validations/{validation_type}/{entity_id}")
async def get_validation(validation_type: str, entity_id: str):
    """
    Get the latest validation for a specific entity.
    
    Args:
        validation_type: Type of validation ('classification' or 'deadline')
        entity_id: ID of the entity being validated (document_id, extraction_id, etc.)
    
    Returns:
        Latest validation record for the specified entity
    """
    try:
        logger.info(f"Fetching {validation_type} validation for entity: {entity_id}")
        
        # Remove strict validation type check - let database filter
        # This allows for future validation types without code changes
        
        # Query validations table for the latest validation
        response = supabase.table('validations')\
            .select('*')\
            .eq('validation_type', validation_type)\
            .eq('entity_id', entity_id)\
            .order('created_at', desc=True)\
            .limit(1)\
            .execute()
        
        logger.info(f"Validation query returned {len(response.data)} results")
        
        if not response.data:
            # Return default pending validation instead of 404 error
            # This prevents NaN errors in the frontend
            logger.info(f"No {validation_type} validation found for entity: {entity_id}, returning pending status")
            return {
                "success": True,
                "validation": {
                    "validation_status": "pending",
                    "confidence_score": 0.0,
                    "feedback": "Validation not yet available or processing",
                    "verified_items": [],
                    "discrepancies": [],
                    "missing_information": [],
                    "created_at": None
                }
            }
        
        validation = response.data[0]
        
        return {
            "success": True,
            "validation": validation
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching validation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

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
