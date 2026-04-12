"""
Lead Conversion System - Main Application
"""
import os
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from fastapi.responses import HTMLResponse

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
    source: Optional[str] = "website"
    message: str = ""

@app.post("/webhook/new-lead")
async def receive_lead(lead_input: LeadInput):
    try:
        lead_data = {
            "client_id": lead_input.client_id,
            "name": lead_input.name,
            "email": lead_input.email,
            "phone": lead_input.phone or "",
            "source": lead_input.source or "website",
            "original_message": lead_input.message,
            "channel": "email",
            "status": "new",
            "interest_score": 50
        }

        response = supabase.table("leads").insert(lead_data).execute()

        if response.data:
            lead_id = response.data[0].get("id")
            return {
                "status": "processed",
                "lead_id": lead_id,
                "message": "Lead received!"
            }

        return {"status": "processed", "message": "Lead saved"}

    except Exception as e:
        return {"status": "error", "detail": str(e)}

@app.get("/")
async def root():
    return HTMLResponse(content="""
    <html>
        <head><title>Lead Conversion System</title></head>
        <body style="font-family: sans-serif; text-align: center; padding: 50px; background: #0a0a0f; color: #fff;">
            <h1>Lead Conversion System</h1>
            <p>System is running!</p>
            <p><a href="/dashboard" style="color: #6366f1;">Open Dashboard</a></p>
        </body>
    </html>
    """)

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
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
            table { width: 100%; border-collapse: collapse; }
            th { background: #1a1a25; padding: 12px 16px; text-align: left; font-size: 12px; text-transform: uppercase; color: #6b6b80; }
            td { padding: 12px 16px; border-top: 1px solid #2a2a3a; }
            .leads-table { background: #12121a; border: 1px solid #2a2a3a; border-radius: 12px; overflow: hidden; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Lead Conversion Dashboard</h1>
            <div class="stats" id="stats">
                <div class="stat-card"><div class="stat-value" id="totalLeads">-</div><div class="stat-label">Total Leads</div></div>
                <div class="stat-card"><div class="stat-value" id="todayLeads">-</div><div class="stat-label">Today</div></div>
                <div class="stat-card"><div class="stat-value" id="thisWeek">-</div><div class="stat-label">This Week</div></div>
                <div class="stat-card"><div class="stat-value" id="activeLeads">-</div><div class="stat-label">Active</div></div>
            </div>
            <div class="leads-table">
                <table>
                    <thead><tr><th>Name</th><th>Email</th><th>Status</th><th>Created</th></tr></thead>
                    <tbody id="leadsBody"><tr><td colspan="4" style="text-align:center;padding:40px;color:#6b6b80;">Loading...</td></tr></tbody>
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
                    document.getElementById('todayLeads').textContent = data.leads.filter(l => new Date(l.created_at).toDateString() === today).length;
                    document.getElementById('activeLeads').textContent = data.leads.filter(l => ['contacted','nurturing'].includes(l.status)).length;
                    const tbody = document.getElementById('leadsBody');
                    if (data.leads.length === 0) { tbody.innerHTML = '<tr><td colspan="4" style="text-align:center;padding:40px;color:#6b6b80;">No leads yet</td></tr>'; return; }
                    tbody.innerHTML = data.leads.map(l => `<tr><td><strong>${l.name||'-'}</strong></td><td>${l.email||'-'}</td><td>${l.status||'new'}</td><td>${new Date(l.created_at).toLocaleDateString()}</td></tr>`).join('');
                } catch (e) { document.getElementById('leadsBody').innerHTML = '<tr><td colspan="4" style="color:#ef4444;">Error loading leads</td></tr>'; }
            }
            loadLeads(); setInterval(loadLeads, 30000);
        </script>
    </body>
    </html>
    """)

@app.get("/leads")
async def get_leads():
    try:
        response = supabase.table("leads").select("*").order("created_at", desc=True).execute()
        return {"leads": response.data, "count": len(response.data)}
    except Exception as e:
        return {"leads": [], "count": 0, "error": str(e)}

@app.get("/test-email")
async def test_email():
    try:
        from integrations.email import send_email
        result = await send_email(to="elitesmit@gmail.com", subject="Test Email", body="Test from Lead Conversion System")
        return {"status": "sent" if result else "failed"}
    except Exception as e:
        return {"error": str(e)}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

@app.on_event("startup")
async def startup():
    print("Lead Conversion System started!")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
