"""
Lead Conversion System - Main Application
FastAPI application with LangGraph agent orchestration
"""
import os
from datetime import datetime, timedelta
from typing import TypedDict, Literal, Optional
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio

# Load environment variables
load_dotenv()

# Import agents
from agents.orchestrator import build_graph, LeadState
from integrations.email import send_email
from integrations.sms import send_sms
from integrations.supabase_client import get_client, get_leads, create_lead, update_lead, log_conversation, log_event

# Initialize FastAPI
app = FastAPI(
    title="Lead Conversion System",
    description="AI-powered lead conversion with 4 specialized agents",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# Pydantic Models
# ============================================

class LeadInput(BaseModel):
    client_id: str
    name: str
    email: str
    phone: Optional[str] = None
    source: str = "website"
    message: str = ""
    channel: str = "email"

class ChatInput(BaseModel):
    client_id: str
    message: str
    lead_id: Optional[str] = None
    session_id: Optional[str] = None

class LeadUpdate(BaseModel):
    status: Optional[str] = None
    interest_score: Optional[int] = None
    notes: Optional[str] = None

# ============================================
# Webhook Endpoint - Receive New Leads
# ============================================

@app.post("/webhook/new-lead")
async def receive_lead(lead_input: LeadInput):
    """
    Webhook to receive leads from any source:
    - Facebook Lead Ads
    - Website forms
    - Google Ads
    - Chat widget
    """
    try:
        # Create lead in database
        lead = await create_lead(lead_input)
        
        # Build initial state
        client = await get_client(lead_input.client_id)
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        state: LeadState = {
            "lead_id": lead["id"],
            "name": lead_input.name,
            "email": lead_input.email,
            "phone": lead_input.phone or "",
            "source": lead_input.source,
            "message": lead_input.message,
            "channel": lead_input.channel,
            "status": "new",
            "follow_up_count": 0,
            "last_contact": datetime.utcnow().isoformat(),
            "next_action": "speed_to_lead",
            "conversation_history": [],
            "interest_score": 50,
            "client_id": lead_input.client_id,
            "client_config": client.get("config", {})
        }
        
        # Log event
        await log_event(lead["id"], "lead_received", {"source": lead_input.source})
        
        # Run the agent graph
        app_graph = build_graph()
        result = await app_graph.ainvoke(state)
        
        return {
            "status": "processed",
            "lead_id": lead["id"],
            "message": "Lead processed successfully"
        }
        
    except Exception as e:
        print(f"Error processing lead: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# Chat Endpoint - For Chat Widget
# ============================================

@app.post("/chat")
async def handle_chat(chat_input: ChatInput):
    """
    Handle chat messages from the embeddable widget
    """
    try:
        client = await get_client(chat_input.client_id)
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        # If lead_id provided, continue existing conversation
        if chat_input.lead_id:
            leads = await get_leads(client_id=chat_input.client_id, lead_id=chat_input.lead_id)
            if not leads:
                raise HTTPException(status_code=404, detail="Lead not found")
            
            lead = leads[0]
            state: LeadState = {
                "lead_id": lead["id"],
                "name": lead["name"],
                "email": lead["email"],
                "phone": lead["phone"] or "",
                "source": lead["source"],
                "message": chat_input.message,
                "channel": "chat",
                "status": lead["status"],
                "follow_up_count": lead.get("follow_up_count", 0),
                "last_contact": lead.get("last_contact", datetime.utcnow().isoformat()),
                "next_action": "respond",
                "conversation_history": [],
                "interest_score": lead.get("interest_score", 50),
                "client_id": chat_input.client_id,
                "client_config": client.get("config", {})
            }
        else:
            # New conversation - create new lead
            lead_input = LeadInput(
                client_id=chat_input.client_id,
                name="Chat Visitor",
                email="chat@visitor.com",
                source="chat",
                message=chat_input.message,
                channel="chat"
            )
            lead = await create_lead(lead_input)
            
            state: LeadState = {
                "lead_id": lead["id"],
                "name": "Chat Visitor",
                "email": "chat@visitor.com",
                "phone": "",
                "source": "chat",
                "message": chat_input.message,
                "channel": "chat",
                "status": "new",
                "follow_up_count": 0,
                "last_contact": datetime.utcnow().isoformat(),
                "next_action": "speed_to_lead",
                "conversation_history": [],
                "interest_score": 50,
                "client_id": chat_input.client_id,
                "client_config": client.get("config", {})
            }
        
        # Run agent to generate response
        from agents.speed_to_lead import speed_to_lead_agent
        result = await speed_to_lead_agent(state)
        
        # Get the last assistant message
        reply = "Thank you for your message! Our team will get back to you shortly."
        if result.get("conversation_history"):
            for msg in reversed(result["conversation_history"]):
                if msg.get("role") == "assistant":
                    reply = msg["content"]
                    break
        
        return {"reply": reply, "lead_id": result["lead_id"]}
        
    except Exception as e:
        print(f"Error handling chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# CRM API Endpoints
# ============================================

@app.get("/api/dashboard/{client_id}")
async def get_dashboard(client_id: str):
    """Get dashboard data for a client"""
    try:
        # Get pipeline stats
        leads = await get_leads(client_id=client_id)
        
        pipeline = {}
        for lead in leads:
            status = lead.get("status", "new")
            pipeline[status] = pipeline.get(status, 0) + 1
        
        # Calculate metrics
        total = len(leads)
        contacted = sum(1 for l in leads if l.get("status") != "new")
        response_rate = (contacted / total * 100) if total > 0 else 0
        booked = sum(1 for l in leads if l.get("status") == "booked")
        
        # Get recent activity
        events = await log_event(None, "dashboard_view", {"client_id": client_id})
        
        return {
            "pipeline": pipeline,
            "metrics": {
                "total_leads": total,
                "response_rate": round(response_rate, 1),
                "booking_rate": round(booked / total * 100, 1) if total > 0 else 0,
                "booked_calls": booked
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/leads/{client_id}")
async def get_client_leads(
    client_id: str, 
    status: Optional[str] = None,
    page: int = 1
):
    """Get leads for a client with optional filtering"""
    try:
        leads = await get_leads(client_id=client_id, status=status)
        
        # Paginate
        limit = 50
        start = (page - 1) * limit
        end = start + limit
        
        return {
            "leads": leads[start:end],
            "page": page,
            "total": len(leads)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/lead/{lead_id}")
async def get_lead_details(lead_id: str):
    """Get full details of a lead including conversation"""
    try:
        leads = await get_leads(lead_id=lead_id)
        if not leads:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        lead = leads[0]
        
        # Get conversations
        from integrations.supabase_client import get_conversations
        conversations = await get_conversations(lead_id)
        
        # Get events
        from integrations.supabase_client import get_events
        events = await get_events(lead_id)
        
        return {
            "lead": lead,
            "conversations": conversations,
            "events": events
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.patch("/api/lead/{lead_id}")
async def update_lead_status(lead_id: str, update: LeadUpdate):
    """Update lead status"""
    try:
        lead = await update_lead(lead_id, update.dict(exclude_unset=True))
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        return {"status": "updated", "lead": lead}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/lead/{lead_id}/book")
async def mark_lead_booked(lead_id: str, deal_value: Optional[float] = None):
    """Mark lead as having booked a call"""
    try:
        lead = await update_lead(lead_id, {
            "status": "booked",
            "booked_at": datetime.utcnow().isoformat(),
            "deal_value": deal_value
        })
        
        # Log event
        await log_event(lead_id, "call_booked", {"deal_value": deal_value})
        
        return {"status": "booked", "lead": lead}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# Client Management
# ============================================

@app.post("/api/clients/onboard")
async def onboard_client(agency_name: str, email: str, calcom_link: str = None):
    """Onboard a new client"""
    try:
        from integrations.supabase_client import create_client
        
        client = await create_client({
            "agency_name": agency_name,
            "email": email,
            "calcom_link": calcom_link
        })
        
        api_key = client["api_key"]
        
        return {
            "api_key": api_key,
            "webhook_url": f"{os.getenv('APP_URL', 'http://localhost:8000')}/webhook/new-lead?key={api_key}",
            "dashboard_url": f"{os.getenv('APP_URL', 'http://localhost:8000')}/dashboard?client={api_key}",
            "setup_instructions": {
                "step_1": "Add the webhook URL to your Facebook Lead Ads / Google Ads",
                "step_2": "Paste the chat widget code before </body> on your website",
                "step_3": "Connect your Cal.com account link"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# Health Check
# ============================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "system": "Lead Conversion System v1.0"
    }

# ============================================
# Background Tasks - Follow-up Scheduler
# ============================================

async def check_followups():
    """Check and send follow-ups for leads due"""
    try:
        from agents.scheduler import process_due_followups
        await process_due_followups()
    except Exception as e:
        print(f"Error in follow-up scheduler: {e}")

# Start background scheduler
@app.on_event("startup")
async def startup():
    """Start background tasks"""
    # Run follow-up check every hour
    asyncio.create_task(check_followups())
    print("Lead Conversion System started!")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)