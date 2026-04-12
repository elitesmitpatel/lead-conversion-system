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
    try:
        import resend
        api_key = os.getenv("RESEND_API_KEY")
        if not api_key or api_key == "re_test":
            print(f"[EMAIL] Would send to {to_email}: Thanks for contacting us!")
            return {"id": "test-email"}
        
        resend.api_key = api_key
        
        subject = f"Thanks for contacting us, {name}!"
        body = await generate_auto_response(name, service, message)
        
        email = resend.Email.send({
            "from": "Lead System <onboarding@resend.dev>",
            "to": to_email,
            "subject": subject,
            "html": f"<p>Hi {name},</p><p>{body}</p><p>Best regards,<br>The Team</p>"
        })
        return email
    
    except Exception as e:
        print(f"Error sending email: {e}")
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
            email_result = await send_auto_email(
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

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)