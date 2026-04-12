"""
Lead Conversion System - Main Application
FastAPI application for receiving leads with AI auto-response
"""
import os
from datetime import datetime, timedelta
from typing import Optional
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from fastapi.responses import HTMLResponse
import asyncio

load_dotenv()

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

# Mount static files for dashboard
try:
    app.mount("/static", StaticFiles(directory="dashboard"), name="static")
except:
    pass

class LeadInput(BaseModel):
    name: str
    email: str
    company: Optional[str] = None
    service: Optional[str] = None
    message: str = ""

class LeadUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None

def generate_response_sync(name: str, service: str, message: str) -> str:
    """Generate personalized response using Gemini"""
    try:
        import google.generativeai as genai
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return f"Hi {name}! Thanks for reaching out. We'll be in touch within 24 hours."

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        prompt = f"""Write a short, friendly email to a new lead.

Lead name: {name}
Service interested: {service}
Message: {message}

Write 2-3 sentences that thanks them and offers to schedule a call."""

        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"AI error: {e}")
        return f"Hi {name}! Thanks for reaching out. We'll be in touch within 24 hours."

def send_email_sync(to_email: str, name: str, service: str, message: str):
    """Send email via Resend"""
    try:
        import resend
        api_key = os.getenv("RESEND_API_KEY")

        if not api_key:
            print("No RESEND_API_KEY")
            return None

        resend.api_key = api_key

        subject = f"Thanks for contacting us, {name}!"
        body = generate_response_sync(name, service, message)

        email = resend.Emails.send({
            "from": "onboarding@resend.dev",
            "to": to_email,
            "subject": subject,
            "html": f"<p>Hi {name},</p><p>{body}</p><p>Best regards,<br>The Team</p>"
        })

        return email
    except Exception as e:
        print(f"Email error: {e}")
        return None

@app.post("/webhook/new-lead")
async def receive_lead(lead_input: LeadInput):
    """Webhook to receive leads - saves to contacts and sends auto-email"""
    try:
        lead_data = {
            "name": lead_input.name,
            "email": lead_input.email,
            "company": lead_input.company or "",
            "service": lead_input.service or "",
            "message": lead_input.message
        }

        response = supabase.table("contacts").insert(lead_data).execute()

        if response.data:
            lead_id = response.data[0].get("id")

            email_result = send_email_sync(
                lead_input.email,
                lead_input.name,
                lead_input.service or "your services",
                lead_input.message
            )

            return {
                "status": "processed",
                "lead_id": lead_id,
                "email_sent": bool(email_result)
            }

        return {"status": "processed", "message": "Lead saved"}

    except Exception as e:
        print(f"Error: {e}")
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
            .email-badge { background: #22c55e20; color: #22c55e; padding: 2px 8px; border-radius: 4px; font-size: 12px; }
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
                    <div class="stat-value" id="emailsSent">-</div>
                    <div class="stat-label">Emails Sent</div>
                </div>
            </div>
            
            <button class="btn refresh-btn" onclick="loadLeads()">Refresh</button>
            
            <div class="leads-table">
                <table>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Name</th>
                            <th>Email</th>
                            <th>Company</th>
                            <th>Service</th>
                            <th>Message</th>
                            <th>Created</th>
                            <th>Action</th>
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
                    
                    // Update stats
                    document.getElementById('totalLeads').textContent = data.count;
                    
                    const today = new Date().toDateString();
                    const todayLeads = data.leads.filter(l => new Date(l.created_at).toDateString() === today).length;
                    document.getElementById('todayLeads').textContent = todayLeads;
                    
                    const weekAgo = new Date();
                    weekAgo.setDate(weekAgo.getDate() - 7);
                    const weekLeads = data.leads.filter(l => new Date(l.created_at) > weekAgo).length;
                    document.getElementById('thisWeek').textContent = weekLeads;
                    
                    document.getElementById('emailsSent').textContent = data.count + ' auto';
                    
                    // Render table
                    const tbody = document.getElementById('leadsBody');
                    if (data.leads.length === 0) {
                        tbody.innerHTML = '<tr><td colspan="8" style="text-align: center; padding: 40px; color: #6b6b80;">No leads yet</td></tr>';
                        return;
                    }
                    
                    tbody.innerHTML = data.leads.map(lead => `
                        <tr>
                            <td>${lead.id}</td>
                            <td><strong>${lead.name || '-'}</strong></td>
                            <td>${lead.email || '-'}</td>
                            <td>${lead.company || '-'}</td>
                            <td>${lead.service || '-'}</td>
                            <td>${(lead.message || '-').substring(0, 30)}${lead.message && lead.message.length > 30 ? '...' : ''}</td>
                            <td>${new Date(lead.created_at).toLocaleDateString()}</td>
                            <td><button class="btn" onclick="sendFollowup(${lead.id}, '${lead.email}', '${lead.name.replace(/'/g, "\\\\'")}')">Follow-up</button></td>
                        </tr>
                    `).join('');
                } catch (e) {
                    console.error('Error loading leads:', e);
                    document.getElementById('leadsBody').innerHTML = '<tr><td colspan="8" style="text-align: center; padding: 40px; color: #ef4444;">Error loading leads</td></tr>';
                }
            }
            
            async function sendFollowup(id, email, name) {
                alert('Sending follow-up to ' + name + ' at ' + email);
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
        response = supabase.table("contacts").select("*").order("created_at", desc=True).execute()
        return {"leads": response.data, "count": len(response.data)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/leads/{lead_id}/followup")
async def send_followup(lead_id: int):
    """Send follow-up email to a lead"""
    try:
        response = supabase.table("contacts").select("*").eq("id", lead_id).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        lead = response.data[0]
        email_result = send_email_sync(
            lead["email"],
            lead["name"],
            lead.get("service", "your services"),
            lead.get("message", "")
        )
        
        return {"status": "sent", "email_sent": bool(email_result)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/test-email")
async def test_email():
    """Test sending an email"""
    try:
        import resend
        api_key = os.getenv("RESEND_API_KEY")

        if not api_key:
            return {"error": "No RESEND_API_KEY"}

        resend.api_key = api_key

        email = resend.Emails.send({
            "from": "onboarding@resend.dev",
            "to": "elitesmit@gmail.com",
            "subject": "Test Email from Lead System",
            "html": "<p>This is a test email.</p>"
        })

        return {"result": email}
    except Exception as e:
        return {"error": str(e)}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

# Background scheduler for follow-ups
async def check_followups():
    """Check for leads needing follow-up (runs every hour)"""
    while True:
        try:
            print(f"[SCHEDULER] Checking follow-ups at {datetime.utcnow().isoformat()}")
            
            # Get leads older than 24 hours without follow-up
            yesterday = (datetime.utcnow() - timedelta(hours=24)).isoformat()
            
            response = supabase.table("contacts").select("*").lt("created_at", yesterday).execute()
            
            for lead in response.data:
                print(f"[SCHEDULER] Would send follow-up to {lead.get('name', 'Unknown')}")
            
            await asyncio.sleep(3600)
        except Exception as e:
            print(f"[SCHEDULER] Error: {e}")
            await asyncio.sleep(3600)

@app.on_event("startup")
async def startup():
    """Start background scheduler"""
    asyncio.create_task(check_followups())
    print("Lead Conversion System started!")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)