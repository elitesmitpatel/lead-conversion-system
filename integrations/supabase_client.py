"""
Supabase Client Integration
Handles all database operations with Supabase
"""
import os
from typing import Optional, List, Dict, Any
from datetime import datetime


# Initialize Supabase client
def get_supabase_client():
    """Get Supabase client"""
    try:
        from supabase import create_client, Client
        
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        if not url or not key:
            print("Warning: SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY not set")
            return None
        
        return create_client(url, key)
    except ImportError:
        print("Supabase client not available")
        return None


supabase = get_supabase_client()


async def get_client(client_id: str) -> Optional[Dict]:
    """Get a client by ID"""
    if not supabase:
        return None
    
    try:
        response = supabase.table("clients").select("*").eq("id", client_id).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"Error getting client: {e}")
        return None


async def get_clients() -> List[Dict]:
    """Get all active clients"""
    if not supabase:
        return []
    
    try:
        response = supabase.table("clients").select("*").eq("is_active", True).execute()
        return response.data
    except Exception as e:
        print(f"Error getting clients: {e}")
        return []


async def create_client(data: Dict) -> Dict:
    """Create a new client"""
    if not supabase:
        return {}
    
    try:
        response = supabase.table("clients").insert(data).execute()
        return response.data[0] if response.data else {}
    except Exception as e:
        print(f"Error creating client: {e}")
        return {}


async def get_leads(
    client_id: str = None, 
    status: str = None, 
    lead_id: str = None,
    limit: int = 100
) -> List[Dict]:
    """Get leads with optional filtering"""
    if not supabase:
        return []
    
    try:
        query = supabase.table("lead_conversion_contacts").select("*")
        
        if client_id:
            query = query.eq("client_id", client_id)
        
        if status:
            query = query.eq("status", status)
        
        if lead_id:
            query = query.eq("id", lead_id)
        
        response = query.order("created_at", desc=True).limit(limit).execute()
        return response.data
    except Exception as e:
        print(f"Error getting leads: {e}")
        return []


async def get_lead(lead_id: str) -> Optional[Dict]:
    """Get a single lead by ID"""
    leads = await get_leads(lead_id=lead_id)
    return leads[0] if leads else None


async def create_lead(lead_data: Dict) -> Dict:
    """Create a new lead"""
    if not supabase:
        return {}
    
    try:
        response = supabase.table("lead_conversion_contacts").insert(lead_data).execute()
        return response.data[0] if response.data else {}
    except Exception as e:
        print(f"Error creating lead: {e}")
        return {}


async def update_lead(lead_id: str, data: Dict) -> Optional[Dict]:
    """Update a lead"""
    if not supabase:
        return None
    
    try:
        # Add updated_at timestamp
        data["updated_at"] = datetime.utcnow().isoformat()
        
        response = supabase.table("lead_conversion_contacts").update(data).eq("id", lead_id).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"Error updating lead: {e}")
        return None


async def log_conversation(
    lead_id: str, 
    role: str, 
    content: str, 
    channel: str = None,
    strategy: str = None
) -> bool:
    """Log a conversation message"""
    if not supabase:
        return False
    
    try:
        data = {
            "lead_id": lead_id,
            "role": role,
            "content": content,
            "channel": channel,
            "strategy": strategy
        }
        response = supabase.table("conversations").insert(data).execute()
        return bool(response.data)
    except Exception as e:
        print(f"Error logging conversation: {e}")
        return False


async def get_conversations(lead_id: str) -> List[Dict]:
    """Get conversation history for a lead"""
    if not supabase:
        return []
    
    try:
        response = (
            supabase.table("conversations")
            .select("*")
            .eq("lead_id", lead_id)
            .order("created_at", asc=True)
            .execute()
        )
        return response.data
    except Exception as e:
        print(f"Error getting conversations: {e}")
        return []


async def log_event(lead_id: str, event_type: str, metadata: Dict = None) -> bool:
    """Log an event"""
    if not supabase or not lead_id:
        return False
    
    try:
        data = {
            "lead_id": lead_id,
            "event_type": event_type,
            "metadata": metadata or {}
        }
        response = supabase.table("events").insert(data).execute()
        return bool(response.data)
    except Exception as e:
        print(f"Error logging event: {e}")
        return False


async def get_events(lead_id: str) -> List[Dict]:
    """Get events for a lead"""
    if not supabase:
        return []
    
    try:
        response = (
            supabase.table("events")
            .select("*")
            .eq("lead_id", lead_id)
            .order("created_at", desc=True)
            .execute()
        )
        return response.data
    except Exception as e:
        print(f"Error getting events: {e}")
        return []