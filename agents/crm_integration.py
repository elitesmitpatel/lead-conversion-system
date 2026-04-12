"""
Agent 4: CRM Integration & Pipeline Sync
Keeps lead data synchronized with client CRMs
"""
from typing import TypedDict, Literal
from datetime import datetime
import asyncio


async def crm_sync_agent(state: dict) -> dict:
    """
    Sync lead data with external CRM systems
    Note: This is a placeholder - implement specific CRM integrations as needed
    """
    
    # This agent handles:
    # - Syncing lead status to external CRMs
    # - Updating deal values
    # - Notifying client when lead books
    
    lead_id = state.get("lead_id")
    status = state.get("status", "")
    client_config = state.get("client_config", {})
    
    # Log the sync event
    from integrations.supabase_client import log_event
    await log_event(lead_id, "crm_sync", {
        "status": status,
        "client_id": state.get("client_id")
    })
    
    # Check if lead was booked
    if status == "booked":
        # Send notification to agency owner
        from integrations.email import send_email
        await send_email(
            to=client_config.get("owner_email", "owner@agency.com"),
            subject=f"🎉 New call booked: {state.get('name')}",
            body=f"""
A new call has been booked!

Lead: {state.get('name')} ({state.get('email')})
Source: {state.get('source')}
Interest Score: {state.get('interest_score')}/100

View in dashboard: https://your-app.com/lead/{lead_id}
            """
        )
    
    return state


async def sync_crm(client_id: str, external_crm: str = None):
    """
    Sync all leads for a client to their external CRM
    """
    from integrations.supabase_client import get_leads
    
    leads = await get_leads(client_id=client_id)
    
    # This would call external CRM APIs based on client config
    # For now, just log the intent
    print(f"Would sync {len(leads)} leads to CRM for client {client_id}")
    
    return {"synced": len(leads)}


async def export_leads_csv(client_id: str) -> str:
    """
    Export leads as CSV for client download
    """
    from integrations.supabase_client import get_leads
    import csv
    import io
    
    leads = await get_leads(client_id=client_id)
    
    # Create CSV
    output = io.StringIO()
    if leads:
        writer = csv.DictWriter(output, fieldnames=leads[0].keys())
        writer.writeheader()
        writer.writerows(leads)
    
    return output.getvalue()