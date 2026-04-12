"""
Agent 3: Database Reactivation
Turns dead/cold leads into new booked calls
"""
from typing import TypedDict, Literal
from datetime import datetime, timedelta
import os
import asyncio
import random

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


# Reactivation offers
REACTIVATION_OFFERS = {
    "free_audit": "We're offering free marketing audits this week — want one?",
    "new_service": "We just launched a new program that might be a better fit.",
    "case_study": "We helped a similar client achieve 3x results — want to see how?",
    "limited_spots": "We have limited spots opening up next month — wanted to give you first dibs.",
    "updated_portfolio": "We just updated our case studies — thought you might find them relevant."
}


REACTIVATION_PROMPT = """
You are reaching out to {lead_name} who contacted {agency_name} 
{months_ago} months ago about: {original_message}

They went cold because: {cold_reason}

Write a reactivation {channel} that:
1. Acknowledges the time gap honestly (don't pretend it hasn't been months)
2. Offers something NEW — a new service, case study, or limited offer
3. Makes it easy to say yes (one-click booking, free audit, etc.)
4. Has a "reason why" you're reaching out NOW

Tone: Warm, no guilt-tripping, genuinely helpful
Length: Keep it SHORT — {length}
"""


def months_between(date_str1: str, date_str2: datetime) -> int:
    """Calculate months between two dates"""
    try:
        date1 = datetime.fromisoformat(date_str1.replace('Z', '+00:00'))
        date2 = date_str2 if isinstance(date_str2, datetime) else datetime.fromisoformat(str(date_str2).replace('Z', '+00:00'))
        months = (date2.year - date1.year) * 12 + (date2.month - date1.month)
        return max(1, months)
    except:
        return 1


def infer_cold_reason(state: dict) -> str:
    """Analyzes conversation history to guess why they went cold"""
    history = state.get("conversation_history", [])
    
    last_messages = [m for m in history if m.get("role") == "user"]
    if last_messages:
        last_msg = last_messages[-1].get("content", "").lower()
        if any(w in last_msg for w in ["expensive", "budget", "cost", "price"]):
            return "price concerns"
        if any(w in last_msg for w in ["think about", "later", "not right now", "busy"]):
            return "timing issues"
        if any(w in last_msg for w in ["competitor", "other option", "going with"]):
            return "evaluating competitors"
        if any(w in last_msg for w in ["not interested", "no thanks"]):
            return "not interested"
    
    return "went quiet — reason unknown"


def select_offer(state: dict) -> str:
    """Select the best reactivation offer based on lead profile"""
    interest_score = state.get("interest_score", 0)
    
    # Higher interest = more direct offers
    if interest_score > 50:
        return random.choice(["new_service", "case_study", "limited_spots"])
    elif interest_score > 30:
        return random.choice(["free_audit", "updated_portfolio", "case_study"])
    else:
        return random.choice(["free_audit", "new_service"])


def generate_reactivation(state: dict) -> str:
    """Generate AI reactivation message"""
    
    if not GEMINI_AVAILABLE:
        return f"Hi {state['name']}! It's been a while. We recently helped a client similar to you achieve great results. Would you be open to a quick chat?"
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return f"Hi {state['name']}! It's been a while. We'd love to reconnect and see if we can help."
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # Get details
    channel = state.get("channel", "email")
    cold_reason = infer_cold_reason(state)
    offer_type = select_offer(state)
    offer_text = REACTIVATION_OFFERS.get(offer_type, "Let's connect!")
    
    length = "1-2 sentences" if channel == "sms" else "short paragraph"
    
    prompt = REACTIVATION_PROMPT.format(
        lead_name=state.get("name", "there"),
        agency_name=state.get("client_config", {}).get("agency_name", "our agency"),
        months_ago=months_between(state.get("last_contact", ""), datetime.utcnow()),
        original_message=state.get("message", ""),
        cold_reason=cold_reason,
        channel=channel,
        length=length
    ) + f"\n\nOffer to include: {offer_text}"
    
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Error generating reactivation: {e}")
        return f"Hi {state['name']}! It's been a few months since we connected. We just launched some new services that might be a better fit. Want to reconnect?"


async def reactivation_agent(state: dict) -> dict:
    """
    Re-engages dead leads with fresh value
    """
    
    # Generate reactivation message
    reply_text = generate_reactivation(state)
    
    # Send via appropriate channel
    channel = state.get("channel", "email")
    
    try:
        if channel == "email":
            await send_email(
                to=state["email"],
                subject=f"{state['name']}, quick question",
                body=reply_text
            )
        elif channel == "sms":
            await send_sms(
                to=state["phone"],
                body=reply_text
            )
        
        print(f"✅ Sent reactivation to {state['name']}")
        
    except Exception as e:
        print(f"Error sending reactivation: {e}")
    
    # Update state - back into nurturing flow
    state["status"] = "nurturing"
    state["follow_up_count"] = 0  # Reset follow-up count
    state["last_contact"] = datetime.utcnow().isoformat()
    state["next_action"] = "follow_up"
    state["interest_score"] = 30  # Lower score for reactivated leads
    
    # Add to conversation history
    state["conversation_history"] = state.get("conversation_history", [])
    state["conversation_history"].append({
        "role": "assistant",
        "content": reply_text,
        "timestamp": datetime.utcnow().isoformat(),
        "channel": channel,
        "strategy": "reactivation"
    })
    
    # Update database
    try:
        await update_lead(state["lead_id"], {
            "status": "nurturing",
            "follow_up_count": 0,
            "last_contact": state["last_contact"],
            "next_followup_at": datetime.utcnow() + timedelta(days=1),
            "interest_score": 30
        })
        
        await log_conversation(
            lead_id=state["lead_id"],
            role="assistant",
            content=reply_text,
            channel=channel,
            strategy="reactivation"
        )
        
        await log_event(state["lead_id"], "reactivation_sent", {
            "months_ago": months_between(state.get("last_contact", ""), datetime.utcnow())
        })
        
    except Exception as e:
        print(f"Error updating database: {e}")
    
    return state


async def run_batch_reactivation(client_id: str, batch_size: int = 50) -> dict:
    """
    Pulls dead leads, reactivates in batches
    Can be triggered manually or on schedule
    """
    from integrations.supabase_client import get_leads
    
    # Get dead leads that haven't been contacted in 30+ days
    dead_leads = await get_leads(
        client_id=client_id,
        status="dead",
        limit=batch_size
    )
    
    # Filter by last contact > 30 days ago
    cutoff = datetime.utcnow() - timedelta(days=30)
    eligible_leads = []
    
    for lead in dead_leads:
        last_contact = lead.get("last_contact")
        if last_contact:
            try:
                last_date = datetime.fromisoformat(last_contact.replace('Z', '+00:00'))
                if last_date < cutoff:
                    eligible_leads.append(lead)
            except:
                eligible_leads.append(lead)
    
    results = {"sent": 0, "errors": 0}
    
    for lead in eligible_leads:
        try:
            # Build state
            from .speed_to_lead import SPEED_TO_LEAD_PROMPT
            
            state = {
                "lead_id": lead["id"],
                "name": lead["name"],
                "email": lead["email"],
                "phone": lead.get("phone", ""),
                "source": lead.get("source", "database"),
                "message": lead.get("original_message", ""),
                "channel": lead.get("channel", "email"),
                "status": "dead",
                "follow_up_count": lead.get("follow_up_count", 10),
                "last_contact": lead.get("last_contact", ""),
                "next_action": "reactivation",
                "conversation_history": [],
                "interest_score": lead.get("interest_score", 25),
                "client_id": client_id,
                "client_config": {}
            }
            
            # Run reactivation
            await reactivation_agent(state)
            results["sent"] += 1
            
            # Rate limiting
            await asyncio.sleep(1)
            
        except Exception as e:
            results["errors"] += 1
            print(f"Error reactivating lead {lead.get('id')}: {e}")
    
    return results