"""
Agent 1: Speed-to-Lead
Responds to every new lead within 60 seconds via their preferred channel
"""
from typing import TypedDict, Literal
from datetime import datetime
import os
import asyncio

# Import Google Gemini
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

# Import integrations
from integrations.email import send_email
from integrations.sms import send_sms
from integrations.supabase_client import update_lead, log_conversation, log_event


# Prompt for Speed-to-Lead agent
SPEED_TO_LEAD_PROMPT = """You are a friendly, professional assistant for {agency_name}, a marketing agency.

A new lead just came in:
- Name: {lead_name}
- Message: {lead_message}
- Source: {lead_source}

Your job:
1. Greet them by name warmly
2. Acknowledge their specific message/source
3. Ask ONE qualifying question (budget, timeline, or goal)
4. Offer to book a call using this link: {booking_link}

Rules:
- Keep it under 3 sentences
- Sound human, not robotic
- No jargon
- Match their energy (if casual, be casual; if formal, be professional)
- Never mention you're an AI
- Be helpful and eager to assist
"""


def generate_response(state: dict) -> str:
    """Generate AI response using Google Gemini"""
    
    if not GEMINI_AVAILABLE:
        # Fallback response if no API key
        return f"Hi {state['name']}! Thanks for reaching out. Would you like to book a call to discuss how we can help?"
    
    # Configure Gemini
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return f"Hi {state['name']}! Thanks for reaching out. Would you like to book a call to discuss how we can help?"
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # Get client config
    client_config = state.get("client_config", {})
    agency_name = client_config.get("agency_name", "our agency")
    calcom_link = client_config.get("calcom_link", "https://cal.com")
    
    # Build prompt
    prompt = SPEED_TO_LEAD_PROMPT.format(
        agency_name=agency_name,
        lead_name=state.get("name", "there"),
        lead_message=state.get("message", ""),
        lead_source=state.get("source", "website"),
        booking_link=calcom_link
    )
    
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Error generating response: {e}")
        # Fallback
        return f"Hi {state['name']}! Thanks for reaching out. Would you like to book a call to discuss how we can help?"


async def speed_to_lead_agent(state: dict) -> dict:
    """
    Responds to new leads within seconds via their channel
    """
    
    # Generate AI response
    reply_text = generate_response(state)
    
    # Determine channel
    channel = state.get("channel", "email")
    
    # Send via appropriate channel
    try:
        if channel == "email":
            await send_email(
                to=state["email"],
                subject=f"Re: Your inquiry - {state.get('client_config', {}).get('agency_name', 'We')}",
                body=reply_text
            )
        elif channel == "sms":
            await send_sms(
                to=state["phone"],
                body=reply_text
            )
        elif channel == "chat":
            # For chat, we just return the message - it's handled by the chat endpoint
            pass
        
        print(f"✅ Sent {channel} response to {state['name']} ({state['email']})")
        
    except Exception as e:
        print(f"Error sending {channel} message: {e}")
    
    # Update state
    state["status"] = "contacted"
    state["last_contact"] = datetime.utcnow().isoformat()
    state["follow_up_count"] = 1
    state["next_action"] = "follow_up"
    state["interest_score"] = 50  # Start with neutral score
    
    # Add to conversation history
    state["conversation_history"] = state.get("conversation_history", [])
    state["conversation_history"].append({
        "role": "assistant",
        "content": reply_text,
        "timestamp": datetime.utcnow().isoformat(),
        "channel": channel,
        "strategy": "initial_response"
    })
    
    # Update lead in database
    try:
        await update_lead(state["lead_id"], {
            "status": "contacted",
            "last_contact": state["last_contact"],
            "follow_up_count": 1,
            "next_followup_at": datetime.utcnow() + timedelta(days=1)
        })
        
        # Log conversation
        await log_conversation(
            lead_id=state["lead_id"],
            role="assistant",
            content=reply_text,
            channel=channel,
            strategy="initial_response"
        )
        
        # Log event
        await log_event(state["lead_id"], "speed_to_lead_response_sent", {
            "channel": channel,
            "interest_score": 50
        })
        
    except Exception as e:
        print(f"Error updating database: {e}")
    
    return state


# Helper to calculate next follow-up time
from datetime import timedelta

FOLLOW_UP_SEQUENCE = {
    1: 1,   # Day 1
    3: 3,   # Day 3
    5: 5,   # Day 5
    7: 7,   # Day 7
    10: 10, # Day 10
    14: 14  # Day 14
}


def get_next_followup_day(follow_up_count: int) -> int:
    """Get the day number for the next follow-up"""
    count = follow_up_count + 1
    if count in FOLLOW_UP_SEQUENCE:
        return FOLLOW_UP_SEQUENCE[count]
    # Default: every 2 days after sequence completes
    return 14 + (count - 6) * 2