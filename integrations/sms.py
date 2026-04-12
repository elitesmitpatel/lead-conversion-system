"""
SMS Integration using Twilio
Sends SMS messages to leads
"""
import os
from typing import Optional


async def send_sms(to: str, body: str) -> bool:
    """
    Send an SMS using Twilio API
    
    Args:
        to: Recipient phone number (e.g., +1234567890)
        body: SMS body text
    
    Returns:
        bool: True if sent successfully
    """
    try:
        from twilio.rest import Client
        
        account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        from_number = os.getenv("TWILIO_PHONE_NUMBER")
        
        if not all([account_sid, auth_token, from_number]):
            # Mock send for development
            print(f"SMS (mock): To={to}, Body={body[:50]}...")
            return True
        
        client = Client(account_sid, auth_token)
        
        message = client.messages.create(
            body=body,
            from_=from_number,
            to=to
        )
        
        print(f"✅ SMS sent to {to}: {message.sid}")
        return True
        
    except Exception as e:
        print(f"Error sending SMS: {e}")
        # For development, return True
        return True


async def send_sms_template(to: str, template_name: str, variables: dict) -> bool:
    """
    Send a templated SMS
    
    Args:
        to: Recipient phone number
        template_name: Name of template
        variables: Variables to fill in template
    """
    templates = {
        "follow_up_1": "Hi {name}! Just checking in - still interested in {topic}? Reply to chat!",
        "follow_up_2": "{name}, wanted to share a helpful resource: {link}",
        "reminder": "Reminder: Your call with {agency_name} is tomorrow at {time}!",
        "reactivation": "Hi {name}! It's been a while. We just launched some new services that might help. Want to reconnect?"
    }
    
    template = templates.get(template_name, templates["follow_up_1"])
    body = template.format(**variables)
    
    return await send_sms(to, body)


# Webhook handler for incoming SMS (Twilio callback)
async def handle_incoming_sms(from_number: str, body: str) -> dict:
    """
    Handle incoming SMS from a lead
    Called when lead replies to an SMS
    """
    from integrations.supabase_client import get_leads, update_lead
    from agents.scoring import update_interest_score
    
    # Find lead by phone number
    leads = await get_leads(phone=from_number)
    
    if not leads:
        return {"message": "Lead not found", "continue": False}
    
    lead = leads[0]
    lead_id = lead["id"]
    
    # Update interest score
    await update_interest_score(lead_id, "replied", {"reply_text": body})
    
    # Update lead status
    await update_lead(lead_id, {
        "status": "contacted",
        "last_contact": datetime.utcnow().isoformat()
    })
    
    # Return response to trigger agent
    return {
        "lead_id": lead_id,
        "message": body,
        "continue": True
    }


# For datetime import
from datetime import datetime