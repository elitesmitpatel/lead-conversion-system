"""
Lead Conversion System - Main Application
FastAPI application for receiving leads with AI auto-response
"""
import os
from datetime import datetime, timedelta
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from fastapi.responses import HTMLResponse
import asyncio

from integrations.supabase_client import supabase

app = FastAPI(
    title="Lead Conversion System",
    description="AI-powered lead conversion with auto-response",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

try:
    app.mount("/static", StaticFiles(directory="dashboard"), name="static")
except:
    pass

class LeadInput(BaseModel):
    client_id: str
    name: str
    email: str
    phone: Optional[str] = None
    company: Optional[str] = None
    service: Optional[str] = None
    source: Optional[str] = "website"
    message: str = ""

class LeadUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None

async def process_lead_through_agents(lead_data: dict, client_config: dict):
    """Process new lead through the LangGraph agent system"""
    try:
        from integrations.email import send_email
        from agents.orchestrator import get_app_graph
        
        state = {
            "lead_id": lead_data.get("id"),
            "name": lead_data.get("name", ""),
            "email": lead_data.get("email", ""),
            "phone": lead_data.get("phone", ""),
            "source": lead_data.get("source", "website"),
            "message": lead_data.get("message", ""),
            "channel": "email",
            "status": "new",
            "follow_up_count": 0,
            "last_contact": datetime.utcnow().isoformat(),
            "next_action": "speed_to_lead",
            "conversation_history": [],
            "interest_score": 50,
            "client_id": lead_data.get("client_id", ""),
            "client_config": client_config
        }
        
        print(f"[AGENT] Processing lead: {state['name']} ({state['email']})")
        
        graph = get_app_graph()
        result = await graph.ainvoke(state)
        
        print(f"[AGENT] Processing complete for lead: {lead_data.get('name')}")
        return result
    except Exception as e:
        print(f"[AGENT ERROR] {e}")
        import traceback
        traceback.print_exc()
        return None

@app.post("/webhook/new-lead")
async def receive_lead(lead_input: LeadInput):
    """Webhook to receive leads - saves to database and triggers agent processing"""
    try:
        lead_data = {
            "client_id": lead_input.client_id,
            "name": lead_input.name,
            "email": lead_input.email,
            "phone": lead_input.phone or "",
            "company": lead_input.company or "",
            "service": lead_input.service or "",
            "source": lead_input.source or "website",
            "original_message": lead_input.message,
            "channel": "email",
            "status": "new",
            "interest_score": 50
        }

        response = supabase.table("leads").insert(lead_data).execute()

        if response.data:
            lead_id = response.data[0].get("id")
            print(f"[WEBHOOK] Lead saved: {lead_id}")
            
            try:
                client_response = supabase.table("clients").select("config").eq("id", lead_input.client_id).execute()
                client_config = client_response.data[0].get("config", {}) if client_response.data else {}
            except Exception as e:
                print(f"[WEBHOOK] Error getting client: {e}")
                client_config = {}
            
            asyncio.create_task(
                process_lead_through_agents(
                    {**lead_data, "id": lead_id},
                    client_config
                )
            )

            return {
                "status": "processed",
                "lead_id": lead_id,
                "message": "Lead received and processing started"
            }

        return {"status": "processed", "message": "Lead saved"}

    except Exception as e:
        print(f"[WEBHOOK ERROR] {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    """Redirect to dashboard"""
    return HTMLResponse(content="""
    <html>
        <head><title>Lead Conversion System</title></head>
        <body style="font-family: sans-serif; text-align: center; padding: 50px; background: #0a0a0f; color: #fff;">
            <h1>Lead Conversion System</h1>
            <p>System is running!</p>
            <p><a href="/dashboard" style="color: #6366f1;">Open Dashboard</a></p>
            <p style="margin-top: 20px; color: #666;">
                Endpoints:<br>
                POST /webhook/new-lead - Receive leads<br>
                GET /leads - List all leads<br>
                GET /health - Health check
            </p>
        </body>
    </html>
    """)

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    """CRM Dashboard"""
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Lead Dashboard</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0a0a0f; color: #e8e8f0; min-height: 100vh; padding: 24px; }
            .container { max-width: 1200px; margin: 0 auto; }
            h1 { font-size: 24px; margin-bottom: 24px; }
            .stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 24px; }
            .stat-card { background: #12121a; border: 1px solid #2a2a3a; border-radius: 12px; padding: 20px; }
            .stat-value { font-size: 32px; font-weight: 700; color: #6366f1; }
            .stat-label { color: #6b6b80; font-size: 14px; margin-top: 4px; }
            .leads-table { background: #12121a; border: 1px solid #2a2a3a; border-radius: 12px; overflow: hidden; }
            table { width: 100%; border-collapse: collapse; }
            th { background: #1a1a25; padding: 12px 16px; text-align: left; font-size: 12px; text-transform: uppercase; color: #6b6b80; }
            td { padding: 12px 16px; border-top: 1px solid #2a2a3a; }
            tr:hover { background: #1a1a25; }
            .btn { background: #6366f1; color: white; border: none; padding: 6px 12px; border-radius: 6px; cursor: pointer; font-size: 12px; }
            .btn:hover { background: #8b5cf6; }
            .refresh-btn { margin-bottom: 16px; }
            .status-badge { padding: 2px 8px; border-radius: 4px; font-size: 12px; }
            .status-new { background: #3b82f620; color: #3b82f6; }
            .status-contacted { background: #22c55e20; color: #22c55e; }
            .status-nurturing { background: #f59e0b20; color: #f59e0b; }
            .status-dead { background: #ef444420; color: #ef4444; }
            .status-booked { background: #10b981; color: white; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Lead Conversion Dashboard</h1>
            
            <div class="stats" id="stats">
                <div class="stat-card">
                    <div class="stat-value" id="totalLeads">-</div>
                    <div class="stat-label">Total Leads</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" id="todayLeads">-</div>
                    <div class="stat-label">Today</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" id="thisWeek">-</div>
                    <div class="stat-label">This Week</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" id="activeLeads">-</div>
                    <div class="stat-label">Active (Contacted)</div>
                </div>
            </div>
            
            <button class="btn refresh-btn" onclick="loadLeads()">Refresh</button>
            
            <div class="leads-table">
                <table>
                    <thead>
                        <tr>
                            <th>Name</th>
                            <th>Email</th>
                            <th>Company</th>
                            <th>Source</th>
                            <th>Status</th>
                            <th>Score</th>
                            <th>Follow-ups</th>
                            <th>Created</th>
                        </tr>
                    </thead>
                    <tbody id="leadsBody">
                        <tr><td colspan="8" style="text-align: center; padding: 40px; color: #6b6b80;">Loading...</td></tr>
                    </tbody>
                </table>
            </div>
        </div>
        
        <script>
            async function loadLeads() {
                try {
                    const res = await fetch('/leads');
                    const data = await res.json();
                    
                    document.getElementById('totalLeads').textContent = data.count;
                    
                    const today = new Date().toDateString();
                    const todayLeads = data.leads.filter(l => new Date(l.created_at).toDateString() === today).length;
                    document.getElementById('todayLeads').textContent = todayLeads;
                    
                    const weekAgo = new Date();
                    weekAgo.setDate(weekAgo.getDate() - 7);
                    const weekLeads = data.leads.filter(l => new Date(l.created_at) > weekAgo).length;
                    document.getElementById('thisWeek').textContent = weekLeads;
                    
                    const activeLeads = data.leads.filter(l => ['contacted', 'nurturing'].includes(l.status)).length;
                    document.getElementById('activeLeads').textContent = activeLeads;
                    
                    const tbody = document.getElementById('leadsBody');
                    if (data.leads.length === 0) {
                        tbody.innerHTML = '<tr><td colspan="8" style="text-align: center; padding: 40px; color: #6b6b80;">No leads yet</td></tr>';
                        return;
                    }
                    
                    tbody.innerHTML = data.leads.map(lead => `
                        <tr>
                            <td><strong>${lead.name || '-'}</strong></td>
                            <td>${lead.email || '-'}</td>
                            <td>${lead.company || '-'}</td>
                            <td>${lead.source || '-'}</td>
                            <td><span class="status-badge status-${lead.status}">${lead.status || 'new'}</span></td>
                            <td>${lead.interest_score || 50}/100</td>
                            <td>${lead.follow_up_count || 0}</td>
                            <td>${new Date(lead.created_at).toLocaleDateString()}</td>
                        </tr>
                    `).join('');
                } catch (e) {
                    console.error('Error loading leads:', e);
                    document.getElementById('leadsBody').innerHTML = '<tr><td colspan="8" style="text-align: center; padding: 40px; color: #ef4444;">Error loading leads</td></tr>';
                }
            }
            
            loadLeads();
            setInterval(loadLeads, 30000);
        </script>
    </body>
    </html>
    """)

@app.get("/leads")
async def get_leads():
    """Get all leads"""
    try:
        response = supabase.table("leads").select("*").order("created_at", desc=True).execute()
        return {"leads": response.data, "count": len(response.data)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/leads/{lead_id}/followup")
async def send_followup(lead_id: str):
    """Manually trigger follow-up for a lead"""
    try:
        from agents.follow_up_engine import follow_up_agent
        
        lead = supabase.table("leads").select("*").eq("id", lead_id).execute()
        if not lead.data:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        lead_data = lead.data[0]
        
        client = supabase.table("clients").select("config").eq("id", lead_data.get("client_id")).execute()
        client_config = client.data[0].get("config", {}) if client.data else {}
        
        state = {
            "lead_id": lead_data["id"],
            "name": lead_data.get("name", ""),
            "email": lead_data.get("email", ""),
            "phone": lead_data.get("phone", ""),
            "source": lead_data.get("source", ""),
            "message": lead_data.get("original_message", ""),
            "channel": lead_data.get("channel", "email"),
            "status": lead_data.get("status", "contacted"),
            "follow_up_count": lead_data.get("follow_up_count", 0),
            "last_contact": lead_data.get("last_contact", datetime.utcnow().isoformat()),
            "next_action": "follow_up",
            "conversation_history": [],
            "interest_score": lead_data.get("interest_score", 50),
            "client_id": lead_data.get("client_id", ""),
            "client_config": client_config
        }
        
        result = await follow_up_agent(state)
        
        return {"status": "sent", "result": result}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/test-email")
async def test_email():
    """Test sending an email"""
    try:
        from integrations.email import send_email
        
        result = await send_email(
            to="elitesmit@gmail.com",
            subject="Test Email from Lead Conversion System",
            body="This is a test email from the Lead Conversion System. If you receive this, your email integration is working!"
        )
        
        return {"status": "sent" if result else "failed"}
    except Exception as e:
        return {"error": str(e)}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

@app.on_event("startup")
async def startup():
    """Start background scheduler"""
    asyncio.create_task(check_followups())
    print("Lead Conversion System started!")

async def check_followups():
    """Check for leads needing follow-up (runs every hour)"""
    from agents.scheduler import process_due_followups
    
    while True:
        try:
            print(f"[SCHEDULER] Checking follow-ups at {datetime.utcnow().isoformat()}")
            await process_due_followups()
            await asyncio.sleep(3600)
        except Exception as e:
            print(f"[SCHEDULER] Error: {e}")
            await asyncio.sleep(3600)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
