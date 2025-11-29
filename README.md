# Multi-Agent RAG MCP Server

A comprehensive multi-agent Retrieval-Augmented Generation (RAG) system built on the Model Context Protocol (MCP), featuring specialized AI microagents for legal document processing, deadline extraction, and strategic analytics.

## 🎯 Overview

This project implements an interconnected agentic ecosystem using MCP servers as the foundation for coordinating specialized AI agents. The system is designed for legal tech applications, particularly document intelligence and deadline management.

## ✨ Features

- **Multi-Agent Architecture**: Three specialized agents working in coordination
- **Vector Storage**: Supabase with pgvector for semantic search
- **MCP Integration**: Seamless integration with Claude Desktop
- **Legal Document Processing**: Specialized for Spanish legal notifications
- **Strategic Analytics**: Business intelligence and context analysis
- **Zero-Input Strategy**: 75% automation, 25% strategic oversight

## 🤖 Agents

### 1. Deadline Agent
Extracts and manages deadlines from Spanish legal documents with high accuracy.

**Capabilities:**
- Spanish legal text processing
- Deadline extraction and categorization
- Automated deadline tracking
- Legal notification parsing

### 2. Document Classification Agent
Automatically categorizes and classifies legal documents.

**Capabilities:**
- Multi-class document classification
- Metadata extraction
- Automated tagging
- Document type recognition

### 3. SmartContext Analytics Agent
Provides strategic business intelligence and contextual analysis.

**Capabilities:**
- Strategic analytics
- Business context extraction
- Cross-document insights
- Trend analysis

## 🏗️ Architecture
```
rag-mcp-server/
├── src/
│   ├── server.py              # Main MCP server
│   ├── agents/
│   │   ├── deadline_agent.py
│   │   ├── document_agent.py
│   │   └── smartcontext_agent.py
│   └── data_sources/
├── database/
│   └── schema.sql             # Database schema
├── docs/                      # Documentation
├── config/                    # Configuration files
├── data/                      # Data storage
└── tests/                     # Test files
```

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Supabase account
- Claude Desktop (for MCP integration)
- PostgreSQL with pgvector extension

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/rag-mcp-server.git
cd rag-mcp-server
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your credentials
```

5. **Initialize database**
```bash
# Run the database schema (see docs for details)
psql -h your-supabase-host -U postgres -d your-database -f database/schema.sql
```

6. **Configure Claude Desktop**
Edit your Claude Desktop config file (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):
```json
{
  "mcpServers": {
    "rag-server": {
      "command": "python",
      "args": ["/Users/yourusername/rag-mcp-server/src/server.py"],
      "env": {
        "SUPABASE_URL": "your_supabase_url",
        "SUPABASE_KEY": "your_supabase_key"
      }
    }
  }
}
```

7. **Restart Claude Desktop**

## 🛠️ Usage

Once configured, the agents are available through Claude Desktop with the following tools:

### Deadline Agent Tools
- `extract_deadlines` - Extract deadlines from legal documents
- `list_deadlines` - List all tracked deadlines
- `search_deadlines` - Search deadlines by criteria

### Document Agent Tools
- `classify_document` - Classify document type
- `index_document` - Add document to vector store
- `search_documents` - Semantic document search

### SmartContext Agent Tools
- `analyze_context` - Strategic context analysis
- `extract_insights` - Business intelligence extraction
- `trend_analysis` - Cross-document trend analysis

## 📊 Database Schema

The system uses 5 main tables:
- `documents` - Document storage and metadata
- `document_embeddings` - Vector embeddings for semantic search
- `deadlines` - Extracted deadline tracking
- `document_classifications` - Document categorization
- `strategic_analysis` - Strategic insights and analytics

See `database/schema.sql` for complete schema details.

## 📚 Documentation

Comprehensive documentation is available in the `docs/` folder:
- **Quick Start Guide** - 30-minute setup from scratch
- **Architecture Guide** - Complete system design and patterns
- **Troubleshooting Guide** - Common issues and solutions
- **API Reference** - Tool definitions and usage

## 🔒 Security

This system implements three-layered security:
1. **Authentication** - User identity verification
2. **Authorization** - Access control and permissions
3. **Encryption** - Zero-knowledge encryption for sensitive data

**Never commit your `.env` file** - it contains sensitive credentials.

## 🧪 Testing

Run the test suite:
```bash
pytest tests/
```

Test individual agents:
```bash
python test_deadline_extraction.py
```

## 🤝 Contributing

This is a personal project, but suggestions and feedback are welcome! Please open an issue to discuss proposed changes.

## 📝 License

[Add your license here]

## 🙏 Acknowledgments

Built with:
- [Anthropic Claude](https://www.anthropic.com/) - AI capabilities
- [Model Context Protocol](https://modelcontextprotocol.io/) - Agent coordination
- [Supabase](https://supabase.com/) - Database and vector storage
- [pgvector](https://github.com/pgvector/pgvector) - Vector similarity search

## 📞 Contact

[Add your contact information]

---

**Status**: Production-Ready  
**Version**: 1.0  
**Last Updated**: November 2024
