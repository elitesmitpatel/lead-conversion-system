"""
=============================================================================
LEAD CONVERSION SYSTEM - Main Application
=============================================================================
A FastAPI application that receives leads via webhook, saves them to the
database, and sends automatic email responses.

KEY FLOW:
1. Webhook receives lead data
2. Lead is saved to Supabase database
3. Status is updated from "new" to "contacted"
4. Auto-response email is sent to the lead
5. Lead appears in the dashboard

VERSION: 1.0.1
=============================================================================
"""

# ============================================================================
# IMPORTS
# ============================================================================
import os
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel  # Data validation
from fastapi.responses import HTMLResponse
import httpx  # For making HTTP requests (email API)

# Database client from integrations folder
from integrations.supabase_client import supabase


# ============================================================================
# FASTAPI APP SETUP
# ============================================================================
app = FastAPI(
    title="Lead Conversion System",
    description="AI-powered lead conversion with auto-response",
    version="1.0.1"
)

# Enable CORS for all origins (allows dashboard to call API)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],    # Allow all HTTP methods
    allow_headers=["*"],
)

# Mount static files for dashboard (if dashboard folder exists)
try:
    app.mount("/static", StaticFiles(directory="dashboard"), name="static")
except:
    pass


# ============================================================================
# DATA MODELS (Request/Response schemas)
# ============================================================================

class LeadInput(BaseModel):
    """
    Schema for incoming lead data from webhook.
    
    Required fields:
    - client_id: Your agency/client ID (UUID from clients table)
    - name: Lead's name
    - email: Lead's email address
    - message: Lead's message/inquiry
    
    Optional fields:
    - phone: Lead's phone number
    - source: Where lead came from (default: "website")
    """
    client_id: str
    name: str
    email: str
    phone: Optional[str] = None
    source: Optional[str] = "website"
    message: str = ""


# ============================================================================
# EMAIL SENDING FUNCTION
# ============================================================================

async def send_auto_email(to: str, name: str, message: str) -> dict:
    """
    Sends an automatic response email to a new lead using Resend API.
    
    Args:
        to: Recipient email address
        name: Lead's name (for personalization)
        message: Lead's original message (for reference)
    
    Returns:
        dict with 'success' (bool) and optionally 'error' (str)
    """
    # Get API key from environment variables
    api_key = os.getenv("RESEND_API_KEY")
    
    # Check if API key exists
    if not api_key:
        return {"success": False, "error": "RESEND_API_KEY not configured"}
    
    # Email payload for Resend API
    payload = {
        "from": "onboarding@resend.dev",  # Sender address (must be verified in Resend)
        "to": [to],                        # Recipient (as array)
        "subject": f"Thanks for reaching out, {name}!",  # Personalized subject
        "html": f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2>Hi {name}!</h2>
            <p>Thanks for your interest! We've received your message:</p>
            <blockquote style="border-left: 3px solid #ccc; padding-left: 15px; color: #666;">
                "{message[:200]}{'...' if len(message) > 200 else ''}"
            </blockquote>
            <p>Our team will be in touch within 24 hours.</p>
            <p>Best regards,<br>The Team</p>
        </body>
        </html>
        """,
        "text": f"Hi {name}!\n\nThanks for your interest! We've received your message: '{message[:200]}'\n\nOur team will be in touch within 24 hours.\n\nBest regards,\nThe Team"
    }
    
    try:
        # Send email via Resend API
        response = httpx.post(
            "https://api.resend.com/emails",
            json=payload,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            timeout=30  # 30 second timeout
        )
        
        # Check if email was sent successfully
        if response.status_code in [200, 201]:
            return {"success": True, "id": response.json().get("id")}
        else:
            return {"success": False, "error": f"Status {response.status_code}: {response.text}"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.post("/webhook/new-lead")
async def receive_lead(lead_input: LeadInput):
    """
    MAIN WEBHOOK ENDPOINT
    
    Receives new lead data, saves to database, and sends auto-response.
    
    Flow:
    1. Validate incoming data (handled by Pydantic)
    2. Save lead to Supabase "leads" table
    3. Update status from "new" to "contacted"
    4. Send auto-response email
    5. Return success response with lead_id
    
    Example request:
        POST /webhook/new-lead
        {
            "client_id": "00814277-181b-47a1-94e5-e04827edaa2f",
            "name": "John Doe",
            "email": "john@example.com",
            "message": "I'm interested in your services"
        }
    """
    try:
        # Prepare lead data for database
        lead_data = {
            "client_id": lead_input.client_id,
            "name": lead_input.name,
            "email": lead_input.email,
            "phone": lead_input.phone or "",
            "source": lead_input.source or "website",
            "original_message": lead_input.message,
            "channel": "email",           # Primary communication channel
            "status": "new",             # Initial status
            "interest_score": 50         # Neutral starting score (0-100)
        }

        # Insert lead into Supabase database
        response = supabase.table("leads").insert(lead_data).execute()

        if response.data:
            lead_id = response.data[0].get("id")
            
            # Update lead status to "contacted"
            supabase.table("leads").update({
                "status": "contacted",
                "last_contact": datetime.utcnow().isoformat()
            }).eq("id", lead_id).execute()
            
            # Send auto-response email to the lead
            email_result = await send_auto_email(
                to=lead_input.email,
                name=lead_input.name,
                message=lead_input.message
            )

            # Return success response
            return {
                "status": "processed",
                "lead_id": lead_id,
                "email_sent": email_result.get("success", False),
                "message": "Lead received!" + (" Email sent." if email_result.get("success") else " Email failed.")
            }

        return {"status": "processed", "message": "Lead saved"}

    except Exception as e:
        # Return error details (useful for debugging)
        return {"status": "error", "detail": str(e)}


# ============================================================================
# UI ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    """Root page - redirects to dashboard"""
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
    """
    CRM Dashboard - Real-time view of all leads
    
    Features:
    - Total leads count
    - Today's leads count
    - Active leads (contacted/nurturing)
    - Table with all leads
    - Auto-refresh every 30 seconds
    """
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
            
            <!-- Stats Cards -->
            <div class="stats" id="stats">
                <div class="stat-card"><div class="stat-value" id="totalLeads">-</div><div class="stat-label">Total Leads</div></div>
                <div class="stat-card"><div class="stat-value" id="todayLeads">-</div><div class="stat-label">Today</div></div>
                <div class="stat-card"><div class="stat-value" id="thisWeek">-</div><div class="stat-label">This Week</div></div>
                <div class="stat-card"><div class="stat-value" id="activeLeads">-</div><div class="stat-label">Active</div></div>
            </div>
            
            <!-- Leads Table -->
            <div class="leads-table">
                <table>
                    <thead>
                        <tr>
                            <th>Name</th>
                            <th>Email</th>
                            <th>Status</th>
                            <th>Score</th>
                            <th>Created</th>
                        </tr>
                    </thead>
                    <tbody id="leadsBody">
                        <tr><td colspan="5" style="text-align:center;padding:40px;color:#6b6b80;">Loading...</td></tr>
                    </tbody>
                </table>
            </div>
        </div>
        
        <!-- JavaScript for fetching and displaying data -->
        <script>
            async function loadLeads() {
                try {
                    // Fetch leads from API
                    const res = await fetch('/leads');
                    const data = await res.json();
                    
                    // Update stats
                    document.getElementById('totalLeads').textContent = data.count;
                    
                    const today = new Date().toDateString();
                    document.getElementById('todayLeads').textContent = data.leads.filter(l => new Date(l.created_at).toDateString() === today).length;
                    document.getElementById('activeLeads').textContent = data.leads.filter(l => ['contacted','nurturing'].includes(l.status)).length;
                    
                    // Render table
                    const tbody = document.getElementById('leadsBody');
                    if (data.leads.length === 0) {
                        tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;padding:40px;color:#6b6b80;">No leads yet</td></tr>';
                        return;
                    }
                    tbody.innerHTML = data.leads.map(l => 
                        `<tr>
                            <td><strong>${l.name||'-'}</strong></td>
                            <td>${l.email||'-'}</td>
                            <td>${l.status||'new'}</td>
                            <td>${l.interest_score||50}</td>
                            <td>${new Date(l.created_at).toLocaleDateString()}</td>
                        </tr>`
                    ).join('');
                } catch (e) {
                    document.getElementById('leadsBody').innerHTML = '<tr><td colspan="5" style="color:#ef4444;">Error loading leads</td></tr>';
                }
            }
            loadLeads();
            setInterval(loadLeads, 30000);  // Refresh every 30 seconds
        </script>
    </body>
    </html>
    """)


# ============================================================================
# API ENDPOINTS (continued)
# ============================================================================

@app.get("/leads")
async def get_leads():
    """
    Get all leads from the database.
    
    Returns:
        JSON with 'leads' array and 'count'
    """
    try:
        response = supabase.table("leads").select("*").order("created_at", desc=True).execute()
        return {"leads": response.data, "count": len(response.data)}
    except Exception as e:
        return {"leads": [], "count": 0, "error": str(e)}


@app.get("/test-email")
async def test_email():
    """
    Test endpoint - sends a test email to elitesmit@gmail.com
    Useful for verifying email configuration.
    """
    result = await send_auto_email(
        to="elitesmit@gmail.com",
        name="Test User",
        message="This is a test email from the Lead Conversion System."
    )
    return result


@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring.
    
    Returns:
        Status, timestamp, and version
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.1"
    }


# ============================================================================
# APP STARTUP
# ============================================================================

@app.on_event("startup")
async def startup():
    """Runs when the app starts - logging message"""
    print("Lead Conversion System v1.0.1 started!")


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    # Run the app on port 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)
