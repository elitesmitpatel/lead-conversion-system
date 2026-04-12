"""
Email Integration using Resend
Sends emails to leads
"""
import os
import httpx


async def send_email(to: str, subject: str, body: str, from_email: str = None) -> bool:
    """
    Send an email using Resend API
    """
    api_key = os.getenv("RESEND_API_KEY")
    
    if not api_key:
        print(f"[EMAIL] No API key configured")
        return False
    
    from_address = from_email or os.getenv("FROM_EMAIL", "onboarding@resend.dev")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "from": from_address,
        "to": [to],
        "subject": subject,
        "html": f"<html><body><p>{body.replace(chr(10), '<br>')}</p></body></html>",
        "text": body
    }
    
    try:
        response = httpx.post(
            "https://api.resend.com/emails",
            json=payload,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200 or response.status_code == 201:
            print(f"[EMAIL] ✅ Sent to {to}: {subject}")
            return True
        else:
            print(f"[EMAIL] ❌ Failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"[EMAIL] ❌ Error: {e}")
        return False
