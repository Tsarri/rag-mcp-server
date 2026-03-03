from supabase import create_client, Client
from openai import OpenAI
from typing import List, Dict, Optional
import os

class VectorStore:
    """Handles vector embeddings and similarity search using Supabase + pgvector"""

    EMBEDDING_MODEL = "text-embedding-3-small"
    EMBEDDING_DIMENSIONS = 1536

    def __init__(self, supabase_url: str = None, supabase_key: str = None):
        self.supabase_url = supabase_url or os.getenv('SUPABASE_URL')
        self.supabase_key = supabase_key or os.getenv('SUPABASE_KEY')

        if not self.supabase_url or not self.supabase_key:
            raise ValueError(
                "Supabase credentials not found. Set SUPABASE_URL and SUPABASE_KEY "
                "environment variables or pass them to VectorStore constructor."
            )

        print("Connecting to Supabase...")
        self.client: Client = create_client(self.supabase_url, self.supabase_key)
        print("✓ Connected to Supabase")

        self.openai = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        print("✓ OpenAI embedding client ready")

    def _embed(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts using OpenAI"""
        response = self.openai.embeddings.create(
            model=self.EMBEDDING_MODEL,
            input=texts
        )
        return [item.embedding for item in response.data]

    async def add_documents(
        self,
        texts: List[str],
        metadata: Optional[List[Dict]] = None
    ) -> int:
        """Add documents to the Supabase vector store"""
        if not texts:
            return 0

        print(f"Generating embeddings for {len(texts)} text chunks...")

        embeddings = self._embed(texts)

        documents_to_insert = []
        for i, (text, embedding) in enumerate(zip(texts, embeddings)):
            doc = {
                'content': text,
                'embedding': embedding,
                'metadata': metadata[i] if metadata and i < len(metadata) else {}
            }
            documents_to_insert.append(doc)

        batch_size = 100
        total_inserted = 0

        for i in range(0, len(documents_to_insert), batch_size):
            batch = documents_to_insert[i:i + batch_size]
            try:
                response = self.client.table('vector_documents').insert(batch).execute()
                total_inserted += len(batch)
                print(f"  Inserted batch: {total_inserted}/{len(documents_to_insert)}")
            except Exception as e:
                print(f"  Error inserting batch: {e}")
                raise

        print(f"✓ Successfully inserted {total_inserted} documents")
        return total_inserted

    async def search(
        self,
        query: str,
        n_results: int = 5,
        similarity_threshold: float = 0.1
    ) -> List[Dict]:
        """Search for similar documents using semantic similarity"""
        print(f"Searching for: '{query}'")

        query_embedding = self._embed([query])[0]

        try:
            response = self.client.rpc(
                'match_documents',
                {
                    'query_embedding': query_embedding,
                    'match_threshold': similarity_threshold,
                    'match_count': n_results
                }
            ).execute()

            results = response.data

            formatted_results = []
            for result in results:
                formatted_results.append({
                    'id': result['id'],
                    'document': result['content'],
                    'metadata': result['metadata'],
                    'similarity': result['similarity']
                })

            print(f"✓ Found {len(formatted_results)} results")
            return formatted_results

        except Exception as e:
            print(f"✗ Error during search: {e}")
            raise

    async def get_document_count(self) -> int:
        """Get total number of documents in the database"""
        try:
            response = self.client.table('vector_documents').select('id', count='exact').execute()
            return response.count
        except Exception as e:
            print(f"Error getting document count: {e}")
            return 0

    async def clear_all_documents(self) -> int:
        """Delete all documents from the database (use with caution!)"""
        try:
            response = self.client.table('vector_documents').delete().neq('id', 0).execute()
            deleted = len(response.data) if response.data else 0
            print(f"✓ Cleared {deleted} documents from database")
            return deleted
        except Exception as e:
            print(f"✗ Error clearing documents: {e}")
            raise
