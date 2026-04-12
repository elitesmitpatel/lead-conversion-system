"""
Interest Scoring Engine
Tracks behavior to adjust follow-up intensity
"""
from datetime import datetime


# Score changes based on events
SCORE_CHANGES = {
    "email_opened": +5,
    "email_link_clicked": +15,
    "replied": +25,
    "visited_pricing": +20,
    "visited_case_studies": +15,
    "booked_call": +100,
    "no_response_3_days": -10,
    "unsubscribed": -100,
    "said_not_interested": -50,
    "email_bounced": -20
}


async def update_interest_score(lead_id: str, event_type: str, metadata: dict = None):
    """
    Updates lead interest score based on their behavior
    """
    from integrations.supabase_client import get_lead, update_lead, log_event
    
    # Get current lead data
    leads = await get_lead(lead_id)
    if not leads:
        return None
    
    lead = leads[0]
    current_score = lead.get("interest_score", 50)
    
    # Get score change
    change = SCORE_CHANGES.get(event_type, 0)
    
    # Apply change (keep between 0-100)
    new_score = max(0, min(100, current_score + change))
    
    # Update lead
    await update_lead(lead_id, {"interest_score": new_score})
    
    # Log event
    await log_event(lead_id, "score_updated", {
        "event_type": event_type,
        "old_score": current_score,
        "new_score": new_score,
        "change": change,
        "metadata": metadata or {}
    })
    
    # If they replied, route back to speed-to-lead for real-time response
    if event_type == "replied":
        from .speed_to_lead import speed_to_lead_agent
        from .orchestrator import get_app_graph
        
        # Build state and process reply
        state = {
            "lead_id": lead_id,
            "name": lead.get("name", ""),
            "email": lead.get("email", ""),
            "phone": lead.get("phone", ""),
            "source": lead.get("source", ""),
            "message": metadata.get("reply_text", "") if metadata else "",
            "channel": lead.get("channel", "email"),
            "status": "contacted",
            "follow_up_count": lead.get("follow_up_count", 0),
            "last_contact": datetime.utcnow().isoformat(),
            "next_action": "speed_to_lead",
            "conversation_history": [],
            "interest_score": new_score,
            "client_id": lead.get("client_id", ""),
            "client_config": {}
        }
        
        # Process through agent
        graph = get_app_graph()
        await graph.ainvoke(state)
    
    return new_score


def get_score_description(score: int) -> str:
    """Get human-readable score description"""
    if score >= 80:
        return "Hot - Ready to buy"
    elif score >= 60:
        return "Warm - Actively evaluating"
    elif score >= 40:
        return " tepid - Need more nurturing"
    elif score >= 20:
        return "Cold - Low engagement"
    else:
        return "Frozen - Likely lost"


def should_skip_followup(score: int) -> bool:
    """Determine if we should skip follow-up based on score"""
    return score < 10  # Skip if score is very low