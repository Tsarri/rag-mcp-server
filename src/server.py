from mcp.server import Server
from mcp.types import Tool, TextContent
import mcp.server.stdio
from data_sources.vector_store import VectorStore
from data_sources.document_loader import DocumentLoader
from dotenv import load_dotenv
from typing import List
from agents.deadline_agent import DeadlineAgent
from agents.document_agent import DocumentAgent
from agents.smartcontext_agent import SmartContextAgent
from agents.gemini_preprocessor import GeminiPreprocessor
from agents.gemini_validator import GeminiValidator
import os

# Load environment variables from .env file
load_dotenv()

# Initialize the MCP server
server = Server("rag-data-server")

# Initialize data sources
print("\n" + "="*60)
print("Initializing RAG MCP Server with Supabase")
print("="*60)
vector_store = VectorStore()
document_loader = DocumentLoader()
deadline_agent = DeadlineAgent()
document_agent = DocumentAgent()
smartcontext_agent = SmartContextAgent()
print("="*60)
print("Server ready to accept connections")
print("="*60 + "\n")

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """
    Split text into overlapping chunks for better context preservation.
    
    Args:
        text: The text to split
        chunk_size: Target size of each chunk in characters
        overlap: Number of characters to overlap between chunks
    
    Returns:
        List of text chunks
    """
    chunks = []
    start = 0
    text_length = len(text)
    
    while start < text_length:
        # Get chunk
        end = start + chunk_size
        chunk = text[start:end]
        
        # Try to break at sentence or paragraph boundary
        if end < text_length:
            # Look for good break points
            last_period = chunk.rfind('. ')
            last_newline = chunk.rfind('\n\n')
            last_question = chunk.rfind('? ')
            last_exclamation = chunk.rfind('! ')
            
            break_point = max(last_period, last_newline, last_question, last_exclamation)
            
            # Only break if we're past halfway through the chunk
            if break_point > chunk_size * 0.5:
                chunk = chunk[:break_point + 1]
                end = start + break_point + 1
        
        chunks.append(chunk.strip())
        start = end - overlap  # Overlap for context continuity
    
    return [c for c in chunks if c]  # Remove empty chunks

@server.list_tools()
async def list_tools() -> list[Tool]:
    """Define all tools available to RAG agents"""
    return [
        Tool(
            name="search_documents",
            description="Search through indexed documents using semantic similarity. Returns the most relevant document chunks for a given query. This uses AI embeddings to find contextually similar content, not just keyword matches.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query or question to find relevant documents for"
                    },
                    "num_results": {
                        "type": "number",
                        "description": "Number of results to return (default: 5, max: 20)",
                        "default": 5
                    },
                    "similarity_threshold": {
                        "type": "number",
                        "description": "Minimum similarity score from 0-1 (default: 0.1). Higher values return only very similar results.",
                        "default": 0.1
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="index_document",
            description="Add a new document to the Supabase vector database. The document will be split into chunks, converted to embeddings, stored for semantic searches, AND automatically classified by document type with entity extraction.",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Absolute or relative path to the document file"
                    },
                    "chunk_size": {
                        "type": "number",
                        "description": "Approximate number of characters per chunk (default: 1000)",
                        "default": 1000
                    },
                    "extract_deadlines": {
                        "type": "boolean",
                        "description": "Automatically extract deadlines from the document (default: true)",
                        "default": True
                    },
                    "classify_document": {
                        "type": "boolean",
                        "description": "Automatically classify document type and extract entities (default: true)",
                        "default": True
                    }
                },
                "required": ["file_path"]
            }
        ),
        Tool(
            name="get_database_stats",
            description="Get statistics about the Supabase vector database including total number of indexed document chunks and database configuration.",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="clear_database",
            description="Delete ALL documents from the Supabase database. WARNING: This action cannot be undone! Use only for testing or complete database resets.",
            inputSchema={
                "type": "object",
                "properties": {
                    "confirm": {
                        "type": "boolean",
                        "description": "Must be set to true to confirm you want to delete all documents"
                    }
                },
                "required": ["confirm"]
            }
        ),
        Tool(
            name="extract_deadlines",
            description="Extract deadlines and due dates from any text using AI. Automatically calculates working days remaining and assigns risk levels. Use this for emails, meeting notes, project plans, or any text containing time-sensitive information.",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Text to analyze for deadlines"
                    },
                    "source_id": {
                        "type": "string",
                        "description": "Optional identifier for tracking (e.g., 'email-123', 'meeting-notes-2024-11')",
                        "default": None
                    }
                },
                "required": ["text"]
            }
        ),
        Tool(
            name="get_deadlines_by_risk",
            description="Retrieve all stored deadlines filtered by risk level. Risk levels: overdue (past deadline), critical (≤2 days), high (3-5 days), medium (6-10 days), low (>10 days).",
            inputSchema={
                "type": "object",
                "properties": {
                    "risk_level": {
                        "type": "string",
                        "description": "Filter by risk level or leave empty for all deadlines",
                        "enum": ["overdue", "critical", "high", "medium", "low", ""],
                        "default": ""
                    }
                }
            }
        ),
        Tool(
            name="get_upcoming_deadlines",
            description="Get all deadlines occurring within the next N days.",
            inputSchema={
                "type": "object",
                "properties": {
                    "days": {
                        "type": "number",
                        "description": "Number of days to look ahead (default: 7)",
                        "default": 7
                    }
                }
            }
        ),
	Tool(
            name="search_documents_by_type",
            description="Search documents by type, matter ID, or text query. Returns classified documents with metadata.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Text to search in filenames and summaries",
                        "default": None
                    },
                    "doc_type": {
                        "type": "string",
                        "description": "Filter by document type",
                        "enum": ["contract", "invoice", "email", "report", "memo", "legal", "other", ""],
                        "default": ""
                    },
                    "matter_id": {
                        "type": "string",
                        "description": "Filter by matter/case ID",
                        "default": None
                    },
                    "limit": {
                        "type": "number",
                        "description": "Maximum results (default: 50)",
                        "default": 50
                    }
                }
            }
        ),
        Tool(
            name="get_document_stats",
            description="Get statistics about classified documents including counts by type.",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
	Tool(
            name="analyze_deadline_risk",
            description="Perform strategic analysis of deadline risk based on current deadline statistics. Provides insights, action items, and risk assessment.",
            inputSchema={
                "type": "object",
                "properties": {
                    "firm_id": {
                        "type": "string",
                        "description": "Identifier for the firm/user (default: 'default')",
                        "default": "default"
                    }
                }
            }
        ),
        Tool(
            name="analyze_caseload_health",
            description="Analyze workload distribution and capacity. Requires caseload data input.",
            inputSchema={
                "type": "object",
                "properties": {
                    "firm_id": {
                        "type": "string",
                        "description": "Identifier for the firm/user (default: 'default')",
                        "default": "default"
                    },
                    "total_cases": {
                        "type": "number",
                        "description": "Total number of active cases"
                    },
                    "active_attorneys": {
                        "type": "number",
                        "description": "Number of active attorneys"
                    },
                    "avg_case_duration_days": {
                        "type": "number",
                        "description": "Average case duration in days",
                        "default": 120
                    }
                },
                "required": ["total_cases", "active_attorneys"]
            }
        ),
        Tool(
            name="get_strategic_insights",
            description="Get recent strategic analyses and insights for the firm.",
            inputSchema={
                "type": "object",
                "properties": {
                    "firm_id": {
                        "type": "string",
                        "description": "Identifier for the firm/user (default: 'default')",
                        "default": "default"
                    },
                    "analysis_type": {
                        "type": "string",
                        "description": "Filter by analysis type",
                        "enum": ["deadline_risk", "caseload_health", "profitability_trends", ""],
                        "default": ""
                    },
                    "limit": {
                        "type": "number",
                        "description": "Maximum number of analyses to return (default: 10)",
                        "default": 10
                    }
                }
            }
        ),
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls from RAG agents"""
    
    if name == "search_documents":
        # Perform semantic search
        query = arguments["query"]
        num_results = min(arguments.get("num_results", 5), 20)  # Cap at 20
        similarity_threshold = arguments.get("similarity_threshold", 0.1)
        
        results = await vector_store.search(
            query, 
            n_results=num_results,
            similarity_threshold=similarity_threshold
        )
        
        if not results:
            return [TextContent(
                type="text",
                text=f"No documents found matching '{query}' with similarity threshold {similarity_threshold}.\n\n"
                     "Try:\n"
                     "- Lowering the similarity_threshold (e.g., 0.05)\n"
                     "- Using different search terms\n"
                     "- Indexing more documents first"
            )]
        
        # Format results for the agent
        response = f"# Search Results: '{query}'\n\n"
        response += f"Found {len(results)} relevant document chunks\n"
        response += f"Similarity threshold: {similarity_threshold}\n\n"
        
        for i, result in enumerate(results, 1):
            response += f"## Result {i} | Similarity: {result['similarity']:.1%}\n\n"
            response += f"{result['document']}\n\n"
            
            if result['metadata']:
                response += "**Source:**\n"
                for key, value in result['metadata'].items():
                    if key != 'chunk_index':  # Don't show internal chunk index
                        response += f"- {key}: {value}\n"
            
            response += "\n---\n\n"
        
        return [TextContent(type="text", text=response)]
    
    elif name == "index_document":
        # Load and index a single document WITH deadline extraction
        file_path = arguments["file_path"]
        chunk_size = arguments.get("chunk_size", 1000)
        extract_deadlines_flag = arguments.get("extract_deadlines", True)
        
        try:
            print(f"\n→ Indexing document: {file_path}")
            doc = await document_loader.load_document(file_path)
            
            # Split document into chunks with overlap
            chunks = chunk_text(doc['text'], chunk_size=chunk_size)
            
            if not chunks:
                return [TextContent(
                    type="text",
                    text=f"❌ No content could be extracted from {doc['filename']}"
                )]
            
            # Create metadata for each chunk
            metadata = [
                {
                    'filename': doc['filename'],
                    'path': doc['path'],
                    'type': doc['type'],
                    'chunk_index': i,
                    'total_chunks': len(chunks)
                }
                for i in range(len(chunks))
            ]
            
            # Add to Supabase vector store
            count = await vector_store.add_documents(chunks, metadata)
            
            # Build response
            response_text = f"✅ Successfully indexed: **{doc['filename']}**\n\n"
            response_text += f"**Vector Database:**\n"
            response_text += f"- Total characters: {len(doc['text']):,}\n"
            response_text += f"- Chunks created: {count}\n"
            response_text += f"- Average chunk size: {len(doc['text']) // count:,} characters\n"
            response_text += f"- Document type: {doc['type']}\n\n"
            
            # Step 1: Gemini Preprocessing (if enabled)
            gemini_context = None
            gemini_preprocessor = GeminiPreprocessor()
            try:
                gemini_extraction = await gemini_preprocessor.extract_structured_data(
                    text=doc['text'],
                    filename=doc['filename']
                )
                if gemini_extraction['success']:
                    gemini_context = gemini_extraction['data']
            except Exception as e:
                print(f"⚠️ Gemini preprocessing skipped: {str(e)}")
            
            # Step 2: Classify document with Gemini context
            classify_flag = arguments.get("classify_document", True)
            classification_validation = None
            if classify_flag:
                print(f"→ Classifying document...")
                try:
                    classification_result = await document_agent.classify_document(
                        document_id=doc['filename'],
                        filename=doc['filename'],
                        extracted_text=doc['text'],
                        metadata={'path': doc['path'], 'type': doc['type']},
                        gemini_context=gemini_context
                    )
                    
                    classification = classification_result['classification']
                    
                    # Step 3: Validate classification with Gemini
                    try:
                        gemini_validator = GeminiValidator()
                        classification_validation = await gemini_validator.validate_classification(
                            claude_output=classification,
                            original_text=doc['text'],
                            gemini_extraction=gemini_context
                        )
                    except Exception as e:
                        print(f"⚠️ Gemini validation skipped: {str(e)}")
                    
                    response_text += f"---\n\n**📄 Document Classification:**\n\n"
                    response_text += f"- **Type:** {classification['doc_type']}\n"
                    response_text += f"- **Confidence:** {classification['confidence']:.0%}\n"
                    
                    if classification.get('matter_id'):
                        response_text += f"- **Matter ID:** {classification['matter_id']}\n"
                    
                    if classification.get('summary'):
                        response_text += f"- **Summary:** {classification['summary']}\n"
                    
                    if classification.get('tags'):
                        response_text += f"- **Tags:** {', '.join(classification['tags'])}\n"
                    
                    # Show entities
                    entities = classification.get('key_entities', {})
                    if any(entities.values()):
                        response_text += f"\n**Entities Extracted:**\n"
                        
                        if entities.get('people'):
                            response_text += f"- People: {', '.join(entities['people'])}\n"
                        
                        if entities.get('organizations'):
                            response_text += f"- Organizations: {', '.join(entities['organizations'])}\n"
                        
                        if entities.get('dates'):
                            response_text += f"- Dates: {', '.join(entities['dates'])}\n"
                        
                        if entities.get('amounts'):
                            response_text += f"- Amounts: {', '.join(entities['amounts'])}\n"
                    
                    # Add validation results
                    if classification_validation:
                        status_emoji = {
                            'validated': '✅',
                            'warning': '⚠️',
                            'error': '❌'
                        }.get(classification_validation['validation_status'], '❓')
                        
                        confidence = classification_validation['confidence_score']
                        response_text += f"\n{status_emoji} **Gemini Validation: {classification_validation['validation_status'].upper()} ({confidence:.0%} confidence)**\n"
                        response_text += f"└─ {classification_validation['feedback']}\n"
                
                except Exception as e:
                    response_text += f"\n⚠️ Could not classify document: {str(e)}\n"
            
            # Extract deadlines from the document
            if extract_deadlines_flag:
                print(f"→ Extracting deadlines from document...")
                deadline_validation = None
                try:
                    deadline_result = await deadline_agent.extract_deadlines(
                        text=doc['text'],
                        source_id=f"document:{doc['filename']}",
                        gemini_context=gemini_context
                    )
                    
                    # Validate deadlines with Gemini
                    try:
                        gemini_validator = GeminiValidator()
                        deadline_validation = await gemini_validator.validate_deadlines(
                            claude_deadlines=deadline_result['deadlines'],
                            original_text=doc['text'],
                            gemini_extraction=gemini_context
                        )
                    except Exception as e:
                        print(f"⚠️ Gemini deadline validation skipped: {str(e)}")
                    
                    if deadline_result['count'] > 0:
                        response_text += f"---\n\n**📅 Deadlines Extracted: {deadline_result['count']}**\n\n"
                        
                        for i, deadline in enumerate(deadline_result['deadlines'], 1):
                            risk_emoji = {
                                'overdue': '🔴',
                                'critical': '🟠',
                                'high': '🟡',
                                'medium': '🔵',
                                'low': '🟢'
                            }.get(deadline['risk_level'], '⚪')
                            
                            response_text += f"{i}. {risk_emoji} **{deadline['date']}** - {deadline['description']}\n"
                            response_text += f"   └─ {deadline['working_days_remaining']} working days · {deadline['risk_level'].upper()}\n\n"
                        
                        # Add deadline validation results
                        if deadline_validation:
                            status_emoji = {
                                'validated': '✅',
                                'warning': '⚠️',
                                'error': '❌'
                            }.get(deadline_validation['validation_status'], '❓')
                            
                            confidence = deadline_validation['confidence_score']
                            response_text += f"{status_emoji} **Gemini Validation: {deadline_validation['validation_status'].upper()} ({confidence:.0%} confidence)**\n"
                            response_text += f"└─ {deadline_validation['feedback']}\n"
                    else:
                        response_text += f"---\n\n*No deadlines found in this document.*\n"
                
                except Exception as e:
                    response_text += f"\n⚠️ Could not extract deadlines: {str(e)}\n"
            
            return [TextContent(type="text", text=response_text)]
        
        except FileNotFoundError as e:
            return [TextContent(
                type="text",
                text=f"❌ File not found: {file_path}\n\nMake sure the path is correct and the file exists."
            )]
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"❌ Error indexing document: {str(e)}"
            )]
    
    elif name == "index_all_documents":
        # Load and index all documents
        chunk_size = arguments.get("chunk_size", 1000)
        
        try:
            print("\n→ Starting batch document indexing")
            documents = await document_loader.load_all_documents()
            
            if not documents:
                return [TextContent(
                    type="text",
                    text="❌ No documents found in data/documents directory.\n\n"
                         "Add some PDF, DOCX, or TXT files to that directory first."
                )]
            
            total_chunks = 0
            results_summary = []
            
            for doc in documents:
                chunks = chunk_text(doc['text'], chunk_size=chunk_size)
                
                if not chunks:
                    results_summary.append(f"⚠️  {doc['filename']}: No content extracted")
                    continue
                
                metadata = [
                    {
                        'filename': doc['filename'],
                        'path': doc['path'],
                        'type': doc['type'],
                        'chunk_index': i,
                        'total_chunks': len(chunks)
                    }
                    for i in range(len(chunks))
                ]
                
                count = await vector_store.add_documents(chunks, metadata)
                total_chunks += count
                results_summary.append(f"✓ {doc['filename']}: {count} chunks ({len(doc['text']):,} chars)")
            
            response = f"✅ Batch indexing complete!\n\n"
            response += f"**Summary:**\n"
            response += f"- Documents processed: {len(documents)}\n"
            response += f"- Total chunks created: {total_chunks}\n"
            response += f"- Average chunks per document: {total_chunks // len(documents)}\n\n"
            response += "**Details:**\n" + "\n".join(results_summary)
            
            return [TextContent(type="text", text=response)]
        
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"❌ Error during batch indexing: {str(e)}"
            )]
    
    elif name == "get_database_stats":
        # Get database statistics
        try:
            count = await vector_store.get_document_count()
            
            response = f"# Supabase Vector Database Statistics\n\n"
            response += f"**Document Chunks:** {count:,}\n"
            response += f"**Database Type:** PostgreSQL with pgvector extension\n"
            response += f"**Embedding Model:** all-MiniLM-L6-v2\n"
            response += f"**Vector Dimensions:** 384\n"
            response += f"**Similarity Metric:** Cosine similarity\n\n"
            
            if count == 0:
                response += "⚠️  Database is empty. Use 'index_document' or 'index_all_documents' to add content."
            else:
                response += "✓ Database is ready for semantic search"
            
            return [TextContent(type="text", text=response)]
        
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"❌ Error getting database stats: {str(e)}"
            )]
    
    elif name == "clear_database":
        # Clear all documents
        if not arguments.get("confirm", False):
            return [TextContent(
                type="text",
                text="⚠️ Database clear cancelled.\n\n"
                     "To confirm deletion of ALL documents, set 'confirm' to true.\n"
                     "This action cannot be undone!"
            )]
        
        try:
            count = await vector_store.clear_all_documents()
            return [TextContent(
                type="text",
                text=f"✅ Database cleared successfully\n\n"
                     f"Deleted {count:,} document chunks from Supabase."
            )]
        
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"❌ Error clearing database: {str(e)}"
            )]
    
    elif name == "extract_deadlines":
        # Extract deadlines from provided text
        text = arguments["text"]
        source_id = arguments.get("source_id")
        
        try:
            print(f"\n→ Extracting deadlines from text (length: {len(text)} chars)...")
            
            result = await deadline_agent.extract_deadlines(text, source_id)
            
            if result['count'] == 0:
                return [TextContent(
                    type="text",
                    text="No deadlines found in the provided text."
                )]
            
            # Format response
            response = f"✅ Extracted {result['count']} deadline(s)\n\n"
            response += f"**Extraction ID:** `{result['extraction_id']}`\n\n"
            
            for i, deadline in enumerate(result['deadlines'], 1):
                risk_emoji = {
                    'overdue': '🔴',
                    'critical': '🟠',
                    'high': '🟡',
                    'medium': '🔵',
                    'low': '🟢'
                }.get(deadline['risk_level'], '⚪')
                
                response += f"## {i}. {deadline['description']}\n"
                response += f"{risk_emoji} **Date:** {deadline['date']}\n"
                response += f"**Working Days:** {deadline['working_days_remaining']}\n"
                response += f"**Risk:** {deadline['risk_level'].upper()}\n\n"
            
            return [TextContent(type="text", text=response)]
        
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"❌ Error extracting deadlines: {str(e)}"
            )]

    elif name == "get_deadlines_by_risk":
        # Get deadlines filtered by risk level
        risk_level = arguments.get("risk_level", "").lower()
        risk_level = risk_level if risk_level else None
        
        try:
            print(f"\n→ Fetching deadlines (risk filter: {risk_level or 'all'})...")
            
            deadlines = await deadline_agent.get_deadlines_by_risk(risk_level)
            
            if not deadlines:
                filter_text = f" with risk level '{risk_level}'" if risk_level else ""
                return [TextContent(
                    type="text",
                    text=f"No deadlines found{filter_text}."
                )]
            
            # Format response
            response = f"# Deadlines"
            if risk_level:
                response += f" - {risk_level.upper()}"
            response += f"\n\nFound {len(deadlines)} deadline(s)\n\n"
            
            for dl in deadlines:
                risk_emoji = {
                    'overdue': '🔴',
                    'critical': '🟠',
                    'high': '🟡',
                    'medium': '🔵',
                    'low': '🟢'
                }.get(dl['risk_level'], '⚪')
                
                response += f"{risk_emoji} **{dl['date']}** · {dl['description']}\n"
                response += f"└─ {dl['working_days_remaining']} working days · {dl['risk_level'].upper()}\n"
                if dl.get('source_id'):
                    response += f"└─ Source: {dl['source_id']}\n"
                response += "\n"
            
            return [TextContent(type="text", text=response)]
        
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"❌ Error fetching deadlines: {str(e)}"
            )]

    elif name == "get_upcoming_deadlines":
        # Get deadlines in the next N days
        days = arguments.get("days", 7)
        
        try:
            print(f"\n→ Fetching deadlines in next {days} days...")
            
            deadlines = await deadline_agent.get_upcoming_deadlines(days)
            
            if not deadlines:
                return [TextContent(
                    type="text",
                    text=f"No deadlines found in the next {days} days."
                )]
            
            # Format response
            response = f"# Upcoming Deadlines (Next {days} Days)\n\n"
            response += f"Found {len(deadlines)} deadline(s)\n\n"
            
            for dl in deadlines:
                risk_emoji = {
                    'overdue': '🔴',
                    'critical': '🟠',
                    'high': '🟡',
                    'medium': '🔵',
                    'low': '🟢'
                }.get(dl['risk_level'], '⚪')
                
                response += f"{risk_emoji} **{dl['date']}** · {dl['description']}\n"
                response += f"└─ {dl['working_days_remaining']} working days · {dl['risk_level'].upper()}\n"
                if dl.get('source_id'):
                    response += f"└─ Source: {dl['source_id']}\n"
                response += "\n"
            
            return [TextContent(type="text", text=response)]
        
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"❌ Error fetching upcoming deadlines: {str(e)}"
            )]
    elif name == "search_documents_by_type":
        # Search classified documents
        query = arguments.get("query")
        doc_type = arguments.get("doc_type", "").lower()
        matter_id = arguments.get("matter_id")
        limit = arguments.get("limit", 50)
        
        # Convert empty string to None
        doc_type = doc_type if doc_type else None
        
        try:
            print(f"\n→ Searching documents...")
            
            documents = await document_agent.search_documents(
                query=query,
                doc_type=doc_type,
                matter_id=matter_id,
                limit=limit
            )
            
            if not documents:
                filter_desc = []
                if query:
                    filter_desc.append(f"query '{query}'")
                if doc_type:
                    filter_desc.append(f"type '{doc_type}'")
                if matter_id:
                    filter_desc.append(f"matter '{matter_id}'")
                
                filter_text = " with " + " and ".join(filter_desc) if filter_desc else ""
                
                return [TextContent(
                    type="text",
                    text=f"No documents found{filter_text}."
                )]
            
            # Format response
            response = f"# Document Search Results\n\n"
            response += f"Found {len(documents)} document(s)\n\n"
            
            for doc in documents:
                doc_icon = {
                    'contract': '📜',
                    'invoice': '💰',
                    'email': '📧',
                    'report': '📊',
                    'memo': '📝',
                    'legal': '⚖️',
                    'other': '📄'
                }.get(doc['doc_type'], '📄')
                
                response += f"{doc_icon} **{doc['filename']}**\n"
                response += f"└─ Type: {doc['doc_type']}"
                
                if doc.get('matter_id'):
                    response += f" · Matter: {doc['matter_id']}"
                
                response += f" · Confidence: {doc['confidence']:.0%}\n"
                
                if doc.get('summary'):
                    response += f"└─ {doc['summary']}\n"
                
                if doc.get('tags'):
                    response += f"└─ Tags: {', '.join(doc['tags'][:5])}\n"
                
                response += "\n"
            
            return [TextContent(type="text", text=response)]
        
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"❌ Error searching documents: {str(e)}"
            )]
    
    elif name == "get_document_stats":
        # Get document classification statistics
        try:
            print(f"\n→ Fetching document statistics...")
            
            stats = await document_agent.get_document_stats()
            
            response = f"# Document Classification Statistics\n\n"
            response += f"**Total Documents:** {stats['total']:,}\n\n"
            response += "**By Type:**\n"
            response += f"- 📜 Contracts: {stats['contract']}\n"
            response += f"- 💰 Invoices: {stats['invoice']}\n"
            response += f"- 📧 Emails: {stats['email']}\n"
            response += f"- 📊 Reports: {stats['report']}\n"
            response += f"- 📝 Memos: {stats['memo']}\n"
            response += f"- ⚖️ Legal: {stats['legal']}\n"
            response += f"- 📄 Other: {stats['other']}\n"
            
            return [TextContent(type="text", text=response)]
        
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"❌ Error getting document stats: {str(e)}"
            )]
    elif name == "analyze_deadline_risk":
        # Perform strategic deadline risk analysis
        firm_id = arguments.get("firm_id", "default")
        
        try:
            print(f"\n→ Gathering deadline data for risk analysis...")
            
            # Get deadline statistics from deadline agent
            stats = await deadline_agent.get_stats()
            
            # Get upcoming deadlines
            upcoming = await deadline_agent.get_upcoming_deadlines(days=7)
            
            # Prepare data for analysis
            deadline_data = {
                "upcoming_deadlines": stats['total'],
                "overdue_tasks": stats['overdue'],
                "deadlines_next_7_days": len(upcoming),
                "critical_deadlines": stats['critical'],
                "high_deadlines": stats['high'],
                "medium_deadlines": stats['medium'],
                "low_deadlines": stats['low']
            }
            
            print(f"  → Analyzing deadline risk with SmartContext...")
            
            # Perform analysis
            analysis = await smartcontext_agent.analyze_deadline_risk(firm_id, deadline_data)
            
            # Format response
            result = analysis['result']
            
            response = f"# 📊 Strategic Deadline Risk Analysis\n\n"
            response += f"**Risk Level:** {result['risk_level'].upper()} "
            response += f"(Confidence: {result['confidence']:.0%})\n\n"
            response += f"**Summary:** {result['summary']}\n\n"
            
            response += "## Key Insights\n\n"
            for i, insight in enumerate(result['key_insights'], 1):
                response += f"{i}. {insight}\n"
            
            response += "\n## Recommended Actions\n\n"
            for i, action in enumerate(result['action_items'], 1):
                response += f"{i}. {action}\n"
            
            if result.get('metrics'):
                response += "\n## Metrics\n\n"
                for key, value in result['metrics'].items():
                    if isinstance(value, float):
                        response += f"- {key.replace('_', ' ').title()}: {value:.0%}\n"
                    else:
                        response += f"- {key.replace('_', ' ').title()}: {value}\n"
            
            response += f"\n*Analysis ID: {analysis['analysis_id']}*"
            
            return [TextContent(type="text", text=response)]
        
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"❌ Error performing deadline risk analysis: {str(e)}"
            )]
    
    elif name == "analyze_caseload_health":
        # Perform strategic caseload health analysis
        firm_id = arguments.get("firm_id", "default")
        total_cases = arguments.get("total_cases")
        active_attorneys = arguments.get("active_attorneys")
        avg_duration = arguments.get("avg_case_duration_days", 120)
        
        try:
            print(f"\n→ Analyzing caseload health with SmartContext...")
            
            caseload_data = {
                "total_cases": total_cases,
                "active_attorneys": active_attorneys,
                "avg_case_duration_days": avg_duration,
                "cases_per_attorney": total_cases / active_attorneys if active_attorneys > 0 else 0
            }
            
            # Perform analysis
            analysis = await smartcontext_agent.analyze_caseload_health(firm_id, caseload_data)
            
            # Format response
            result = analysis['result']
            
            response = f"# 📊 Strategic Caseload Health Analysis\n\n"
            response += f"**Risk Level:** {result['risk_level'].upper()} "
            response += f"(Confidence: {result['confidence']:.0%})\n\n"
            response += f"**Summary:** {result['summary']}\n\n"
            
            response += "## Key Insights\n\n"
            for i, insight in enumerate(result['key_insights'], 1):
                response += f"{i}. {insight}\n"
            
            response += "\n## Recommended Actions\n\n"
            for i, action in enumerate(result['action_items'], 1):
                response += f"{i}. {action}\n"
            
            if result.get('metrics'):
                response += "\n## Metrics\n\n"
                for key, value in result['metrics'].items():
                    if isinstance(value, float):
                        response += f"- {key.replace('_', ' ').title()}: {value:.0%}\n"
                    else:
                        response += f"- {key.replace('_', ' ').title()}: {value}\n"
            
            response += f"\n*Analysis ID: {analysis['analysis_id']}*"
            
            return [TextContent(type="text", text=response)]
        
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"❌ Error performing caseload health analysis: {str(e)}"
            )]
    
    elif name == "get_strategic_insights":
        # Get recent strategic analyses
        firm_id = arguments.get("firm_id", "default")
        analysis_type = arguments.get("analysis_type", "").lower()
        limit = arguments.get("limit", 10)
        
        analysis_type = analysis_type if analysis_type else None
        
        try:
            print(f"\n→ Fetching strategic insights...")
            
            analyses = await smartcontext_agent.get_recent_analyses(firm_id, analysis_type, limit)
            
            if not analyses:
                return [TextContent(
                    type="text",
                    text="No strategic analyses found. Run an analysis first!"
                )]
            
            response = f"# 🧠 Strategic Insights History\n\n"
            response += f"Found {len(analyses)} analysis/analyses\n\n"
            
            for analysis in analyses:
                type_icon = {
                    'deadline_risk': '⏰',
                    'caseload_health': '📋',
                    'profitability_trends': '💰'
                }.get(analysis['analysis_type'], '📊')
                
                risk_emoji = {
                    'low': '🟢',
                    'medium': '🔵',
                    'high': '🟡',
                    'critical': '🔴'
                }.get(analysis['risk_level'], '⚪')
                
                response += f"## {type_icon} {analysis['analysis_type'].replace('_', ' ').title()}\n\n"
                response += f"{risk_emoji} **Risk:** {analysis['risk_level'].upper()} "
                response += f"· **Date:** {analysis['created_at'][:10]}\n\n"
                response += f"**Summary:** {analysis['summary']}\n\n"
                
                if analysis.get('key_insights'):
                    response += "**Top Insights:**\n"
                    for insight in analysis['key_insights'][:2]:
                        response += f"- {insight}\n"
                    response += "\n"
                
                response += "---\n\n"
            
            return [TextContent(type="text", text=response)]
        
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"❌ Error fetching strategic insights: {str(e)}"
            )]


    else:
        raise ValueError(f"Unknown tool: {name}")

# Run the server
async def main():
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())