"""
Client Manager
Handles CRUD operations for client management
"""

import os
from typing import Dict, List, Optional
from supabase import create_client, Client


class ClientManager:
    """
    Manages client data in Supabase.
    Provides CRUD operations for client records.
    """
    
    def __init__(self, supabase_url: str = None, supabase_key: str = None):
        """Initialize the client manager with Supabase credentials"""
        # Get credentials from parameters or environment
        self.supabase_url = supabase_url or os.getenv('SUPABASE_URL')
        self.supabase_key = supabase_key or os.getenv('SUPABASE_KEY')
        
        # Validate credentials
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Missing Supabase credentials (SUPABASE_URL, SUPABASE_KEY)")
        
        # Initialize Supabase client
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
    
    async def create_client(
        self,
        name: str,
        email: str,
        phone: str = None,
        company: str = None
    ) -> Dict:
        """
        Create a new client.
        
        Args:
            name: Client name
            email: Client email (must be unique)
            phone: Optional phone number
            company: Optional company name
            
        Returns:
            Created client record with id
        """
        try:
            client_data = {
                "name": name,
                "email": email,
                "phone": phone,
                "company": company,
                "active": True
            }
            
            response = self.supabase.table('clients').insert(client_data).execute()
            return response.data[0]
        
        except Exception as e:
            raise Exception(f"Error creating client: {str(e)}")
    
    async def get_client(self, client_id: str) -> Optional[Dict]:
        """
        Get a client by ID.
        
        Args:
            client_id: UUID of the client
            
        Returns:
            Client record or None if not found
        """
        try:
            response = self.supabase.table('clients')\
                .select('*')\
                .eq('id', client_id)\
                .execute()
            
            return response.data[0] if response.data else None
        
        except Exception as e:
            raise Exception(f"Error fetching client: {str(e)}")
    
    async def get_all_clients(self, active_only: bool = True) -> List[Dict]:
        """
        Get all clients.
        
        Args:
            active_only: If True, return only active clients
            
        Returns:
            List of client records
        """
        try:
            query = self.supabase.table('clients').select('*')
            
            if active_only:
                query = query.eq('active', True)
            
            query = query.order('created_at', desc=True)
            
            response = query.execute()
            return response.data
        
        except Exception as e:
            raise Exception(f"Error fetching clients: {str(e)}")
    
    async def update_client(
        self,
        client_id: str,
        data: Dict
    ) -> Dict:
        """
        Update client information.
        
        Args:
            client_id: UUID of the client
            data: Dict with fields to update (name, email, phone, company, active)
            
        Returns:
            Updated client record
        """
        try:
            # Only allow updating specific fields
            allowed_fields = ['name', 'email', 'phone', 'company', 'active']
            update_data = {k: v for k, v in data.items() if k in allowed_fields}
            
            if not update_data:
                raise ValueError("No valid fields to update")
            
            response = self.supabase.table('clients')\
                .update(update_data)\
                .eq('id', client_id)\
                .execute()
            
            if not response.data:
                raise ValueError(f"Client not found: {client_id}")
            
            return response.data[0]
        
        except Exception as e:
            raise Exception(f"Error updating client: {str(e)}")
    
    async def delete_client(self, client_id: str) -> Dict:
        """
        Soft delete a client (set active = False).
        
        Args:
            client_id: UUID of the client
            
        Returns:
            Updated client record
        """
        try:
            response = self.supabase.table('clients')\
                .update({"active": False})\
                .eq('id', client_id)\
                .execute()
            
            if not response.data:
                raise ValueError(f"Client not found: {client_id}")
            
            return response.data[0]
        
        except Exception as e:
            raise Exception(f"Error deleting client: {str(e)}")
    
    async def get_client_document_count(self, client_id: str) -> int:
        """
        Get the number of documents for a client.
        
        Args:
            client_id: UUID of the client
            
        Returns:
            Count of documents
        """
        try:
            response = self.supabase.table('documents')\
                .select('id', count='exact')\
                .eq('client_id', client_id)\
                .execute()
            
            return response.count or 0
        
        except Exception as e:
            raise Exception(f"Error counting documents: {str(e)}")
