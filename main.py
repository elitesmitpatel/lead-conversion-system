"""
Lead Conversion System - Main Application
FastAPI application for receiving leads with AI auto-response
"""
import os
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

load_dotenv()

from integrations.supabase_client import supabase

app = FastAPI(
    title="Lead Conversion System",
    description="AI-powered lead conversion with auto-response",
    version="1.0.0"
)

# Debug: Print environment variables on startup
gemini_key = os.getenv("GEMINI_API_KEY") or ""
resend_key = os.getenv("RESEND_API_KEY") or ""
print(f"GEMINI_API_KEY: {gemini_key[:20] if gemini_key else 'NOT SET'}")
print(f"RESEND_API_KEY: {resend_key[:20] if resend_key else 'NOT SET'}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class LeadInput(BaseModel):
    name: str
    email: str
    company: Optional[str] = None
    service: Optional[str] = None
    message: str = ""

async def generate_auto_response(name: str, service: str, message: str) -> str:
    """Generate personalized response using Gemini"""
    try:
        import google.generativeai as genai
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key or api_key == "test-key":
            return f"Hi {name}! Thanks for reaching out. We'll be in touch within 24 hours."
        
        genai.configure(api_key=api_key)
        
        prompt = f"""Write a short, friendly follow-up email to a new lead who just contacted us.
        
Lead name: {name}
Interested service: {service}
Their message: {message}

Write a warm, professional response that:
1. Thanks them for contacting us
2. Shows we understand their needs
3. Offers to schedule a call
4. Signs off professionally

Keep it short (under 100 words)."""
        
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(prompt)
        return response.text
    
    except Exception as e:
        print(f"Error generating response: {e}")
        return f"Hi {name}! Thanks for reaching out. We'll be in touch within 24 hours."

async def send_auto_email(to_email: str, name: str, service: str, message: str):
    """Send auto-response email via Resend"""
    print(f"[EMAIL] Attempting to send to {to_email}")
    try:
        import resend
        api_key = os.getenv("RESEND_API_KEY")
        
        if not api_key:
            print(f"[EMAIL] No API key configured")
            return None
        
        print(f"[EMAIL] API key found: {api_key[:10]}...")
        
        if api_key == "re_test":
            print(f"[EMAIL] Test mode - would send to {to_email}")
            return {"id": "test-email"}
        
        resend.api_key = api_key
        
        subject = f"Thanks for contacting us, {name}!"
        body = await generate_auto_response(name, service, message)
        
        email = resend.emails.send({
            "from": "onboarding@resend.dev",
            "to": to_email,
            "subject": subject,
            "html": f"<p>Hi {name},</p><p>{body}</p><p>Best regards,<br>The Team</p>"
        })
        print(f"[EMAIL] Resend result: {email}")
        if isinstance(email, dict) and "id" in email:
            print(f"[EMAIL] SUCCESS - email sent with ID: {email['id']}")
            return email
        return email
    
    except Exception as e:
        print(f"[EMAIL] Exception: {e}")
        import traceback
        print(f"[EMAIL] Traceback: {traceback.format_exc()}")
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
            
            # Send auto-response email
            try:
                email_result = await send_auto_email(
                    lead_input.email,
                    lead_input.name,
                    lead_input.service or "your services",
                    lead_input.message
                )
                email_sent = bool(email_result)
                email_info = str(email_result) if email_result else "None"
            except Exception as email_err:
                email_sent = False
                email_info = f"Error: {str(email_err)}"
            
            return {
                "status": "processed",
                "lead_id": lead_id,
                "email_sent": email_sent,
                "email_result": email_info
            }
        
        return {"status": "processed", "message": "Lead saved"}
        
    except Exception as e:
        print(f"Error processing lead: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/leads")
async def get_leads():
    """Get all leads"""
    try:
        response = supabase.table("contacts").select("*").order("created_at", desc=True).execute()
        return {"leads": response.data, "count": len(response.data)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/debug")
async def debug_env():
    """Debug environment variables"""
    return {
        "gemini_key_set": bool(os.getenv("GEMINI_API_KEY")),
        "resend_key_set": bool(os.getenv("RESEND_API_KEY")),
        "resend_key_value": os.getenv("RESEND_API_KEY", "NOT SET")[:15] + "..."
    }

@app.get("/test-email")
async def test_email():
    """Test sending an email"""
    try:
        import resend
        api_key = os.getenv("RESEND_API_KEY")
        
        if not api_key:
            return {"error": "No RESEND_API_KEY"}
        
        resend.api_key = api_key
        
        # Send test email
        email = resend.emails.send({
            "from": "onboarding@resend.dev",
            "to": "elitesmit@gmail.com",
            "subject": "Test Email from Lead System",
            "html": "<p>This is a test email.</p>"
        })
        
        return {"result": email}
    except Exception as e:
        import traceback
        return {"error": str(e), "trace": traceback.format_exc()}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)