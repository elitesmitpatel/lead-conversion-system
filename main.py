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

class LeadInput(BaseModel):
    name: str
    email: str
    company: Optional[str] = None
    service: Optional[str] = None
    message: str = ""

def generate_response_sync(name: str, service: str, message: str) -> str:
    """Generate personalized response using Gemini (sync version)"""
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
    """Send email via Resend (sync version)"""
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
            
            # Send email in background
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

@app.get("/leads")
async def get_leads():
    """Get all leads"""
    try:
        response = supabase.table("contacts").select("*").order("created_at", desc=True).execute()
        return {"leads": response.data, "count": len(response.data)}
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)