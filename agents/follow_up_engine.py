"""
Agent 2: Follow-Up Engine
Sends 5-10 automated follow-ups over 14-21 days, adapting tone based on lead behavior
"""
from typing import TypedDict, Literal
from datetime import datetime, timedelta
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


# Follow-up sequence by day offset
FOLLOW_UP_SEQUENCES = {
    1:  {"strategy": "soft_value_add", "description": "Share a helpful resource"},
    3:  {"strategy": "social_proof", "description": "Case study / testimonial"},
    5:  {"strategy": "direct_ask", "description": "Still interested?"},
    7:  {"strategy": "urgency_scarcity", "description": "Limited availability"},
    10: {"strategy": "reframe_offer", "description": "Different angle on value"},
    14: {"strategy": "breakup_email", "description": "Should I close your file?"}
}


FOLLOW_UP_PROMPT = """You are continuing a conversation with {lead_name} who inquired about 
{agency_name}'s services {days_since_last_contact} days ago.

Previous conversation:
{conversation_history}

Their original message: {original_message}
Interest score: {interest_score}/100

Strategy for this follow-up: {strategy} - {description}

Write a {channel} follow-up that:
1. References something specific from their inquiry or previous messages
2. Delivers value (don't just "check in")
3. Has ONE clear CTA (book a call, reply, etc.)
4. Feels like a real person wrote it
5. Is {length} (short for SMS, medium for email)

Do NOT:
- Say "just following up" or "circling back"
- Sound desperate or pushy
- Write more than needed
"""


def days_between(date_str1: str, date_str2: datetime) -> int:
    """Calculate days between two dates"""
    try:
        date1 = datetime.fromisoformat(date_str1.replace('Z', '+00:00'))
        date2 = date_str2 if isinstance(date_str2, datetime) else datetime.fromisoformat(str(date_str2).replace('Z', '+00:00'))
        return (date2 - date1).days
    except:
        return 1


def generate_followup(state: dict, strategy_key: int) -> str:
    """Generate AI follow-up using Google Gemini"""
    
    if not GEMINI_AVAILABLE:
        return "Hi! Just checking in - would you like to chat about how we can help?"
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "Hi! Just checking in - would you like to chat about how we can help?"
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # Get strategy
    strategy = FOLLOW_UP_SEQUENCES.get(strategy_key, {"strategy": "check_in", "description": "General follow-up"})
    
    # Get channel and tone
    channel = state.get("channel", "email")
    interest_score = state.get("interest_score", 50)
    
    if interest_score < 30:
        tone = "low pressure, purely educational"
    elif interest_score < 60:
        tone = "helpful, mildly assertive"
    else:
        tone = "confident, direct ask"
    
    length = "1-2 sentences" if channel == "sms" else "3-5 sentences"
    
    # Format conversation history
    history = state.get("conversation_history", [])
    formatted_history = ""
    for msg in history[-3:]:  # Last 3 messages
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        formatted_history += f"{role}: {content}\n"
    
    prompt = FOLLOW_UP_PROMPT.format(
        lead_name=state.get("name", "there"),
        agency_name=state.get("client_config", {}).get("agency_name", "our agency"),
        days_since_last_contact=days_between(state.get("last_contact", ""), datetime.utcnow()),
        conversation_history=formatted_history or "No previous messages",
        original_message=state.get("message", ""),
        interest_score=interest_score,
        strategy=f"{strategy['strategy']} ({tone})",
        description=strategy["description"],
        channel=channel,
        length=length
    )
    
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Error generating follow-up: {e}")
        return "Hi! Just wanted to check in - are you still interested in learning more?"


async def follow_up_agent(state: dict) -> dict:
    """
    Sends intelligent follow-ups based on sequence and behavior
    """
    
    # Get current follow-up count
    follow_up_count = state.get("follow_up_count", 0)
    next_count = follow_up_count + 1
    
    # Check if we've exhausted the sequence
    if next_count > 10:
        # Mark as dead - will be picked up by reactivation agent
        state["status"] = "dead"
        return state
    
    # Get strategy for this follow-up number
    strategy = FOLLOW_UP_SEQUENCES.get(next_count, {"strategy": "general", "description": "General follow-up"})
    
    # Adjust tone based on interest score
    interest_score = state.get("interest_score", 50)
    if interest_score < 30:
        state["status"] = "nurturing"  # Gentle nurturing for cold leads
    else:
        state["status"] = "contacted"
    
    # Generate the follow-up message
    reply_text = generate_followup(state, next_count)
    
    # Send via appropriate channel
    channel = state.get("channel", "email")
    
    try:
        if channel == "email":
            # Generate subject line
            subjects = {
                1: f"{state['name']}, here's that resource I promised",
                3: "Quick question",
                5: "Still interested?",
                7: "Last chance this month",
                10: "A different way to look at it",
                14: "Should I close your file?"
            }
            subject = subjects.get(next_count, "Following up")
            
            await send_email(
                to=state["email"],
                subject=subject,
                body=reply_text
            )
        elif channel == "sms":
            await send_sms(
                to=state["phone"],
                body=reply_text
            )
        
        print(f"✅ Sent follow-up #{next_count} to {state['name']}")
        
    except Exception as e:
        print(f"Error sending follow-up: {e}")
    
    # Update state
    state["follow_up_count"] = next_count
    state["last_contact"] = datetime.utcnow().isoformat()
    state["next_action"] = "follow_up"
    
    # Calculate next follow-up time
    days_until_next = strategy.get(next_count, 3) if next_count <= 7 else 2
    state["next_followup_at"] = (datetime.utcnow() + timedelta(days=days_until_next)).isoformat()
    
    # Add to conversation history
    state["conversation_history"] = state.get("conversation_history", [])
    state["conversation_history"].append({
        "role": "assistant",
        "content": reply_text,
        "timestamp": datetime.utcnow().isoformat(),
        "channel": channel,
        "strategy": strategy["strategy"]
    })
    
    # Update database
    try:
        await update_lead(state["lead_id"], {
            "status": state["status"],
            "follow_up_count": next_count,
            "last_contact": state["last_contact"],
            "next_followup_at": state["next_followup_at"]
        })
        
        await log_conversation(
            lead_id=state["lead_id"],
            role="assistant",
            content=reply_text,
            channel=channel,
            strategy=strategy["strategy"]
        )
        
        await log_event(state["lead_id"], f"follow_up_{next_count}", {
            "strategy": strategy["strategy"],
            "interest_score": interest_score
        })
        
    except Exception as e:
        print(f"Error updating database: {e}")
    
    return state


# Function to check if a lead needs follow-up
def needs_followup(lead: dict) -> bool:
    """Check if a lead is due for follow-up"""
    status = lead.get("status", "")
    next_followup = lead.get("next_followup_at")
    
    if status not in ["contacted", "nurturing"]:
        return False
    
    if not next_followup:
        return True
    
    try:
        next_time = datetime.fromisoformat(next_followup.replace('Z', '+00:00'))
        return datetime.utcnow() >= next_time
    except:
        return True


# Function to get next follow-up strategy
def get_next_strategy(count: int) -> dict:
    """Get the strategy for the next follow-up"""
    return FOLLOW_UP_SEQUENCES.get(count, {
        "strategy": "general",
        "description": "General follow-up"
    })