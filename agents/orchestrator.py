"""
Lead Conversion System - LangGraph Orchestrator
Routes leads to the appropriate agent based on their status
"""
from typing import TypedDict, Literal
from langgraph.graph import StateGraph, END, START
from datetime import datetime
import os
import asyncio

from .speed_to_lead import speed_to_lead_agent
from .follow_up_engine import follow_up_agent
from .database_reactivation import reactivation_agent
from .crm_integration import crm_sync_agent


class LeadState(TypedDict):
    """State object that flows through the agent graph"""
    lead_id: str
    name: str
    email: str
    phone: str
    source: str
    message: str
    channel: str
    status: str
    follow_up_count: int
    last_contact: str
    next_action: str
    conversation_history: list
    interest_score: int
    client_id: str
    client_config: dict


def router(state: LeadState) -> str:
    """
    Central router - decides which agent handles this lead
    Returns the name of the next node to call
    """
    status = state.get("status", "new")
    next_action = state.get("next_action", "")
    follow_up_count = state.get("follow_up_count", 0)
    
    if next_action == "speed_to_lead" or status == "new":
        return "speed_to_lead"
    elif next_action == "follow_up" or (status in ["contacted", "nurturing"] and follow_up_count < 10):
        return "follow_up_engine"
    elif next_action == "reactivation" or status == "dead":
        return "database_reactivation"
    elif next_action == "sync_crm":
        return "crm_integration"
    else:
        return "END"


def should_continue(state: LeadState) -> str:
    """Determine if we should continue the conversation or end"""
    status = state.get("status", "new")
    next_action = state.get("next_action", "")
    
    if next_action == "speed_to_lead":
        return "speed_to_lead"
    elif next_action == "follow_up":
        return "follow_up_engine"
    elif next_action == "reactivation":
        return "database_reactivation"
    elif next_action == "sync_crm":
        return "crm_integration"
    elif status in ["booked", "won", "lost", "dead"]:
        return "END"
    else:
        return "END"


def build_graph():
    """
    Build the LangGraph state machine
    """
    graph = StateGraph(LeadState)
    
    graph.add_node("router", router)
    graph.add_node("speed_to_lead", speed_to_lead_agent)
    graph.add_node("follow_up_engine", follow_up_agent)
    graph.add_node("database_reactivation", reactivation_agent)
    graph.add_node("crm_integration", crm_sync_agent)
    
    graph.set_entry_point("speed_to_lead")
    
    graph.add_conditional_edges(
        "speed_to_lead",
        should_continue,
        {
            "speed_to_lead": "speed_to_lead",
            "follow_up_engine": "follow_up_engine",
            "database_reactivation": "database_reactivation",
            "crm_integration": "crm_integration",
            "END": END
        }
    )
    
    graph.add_conditional_edges(
        "follow_up_engine",
        should_continue,
        {
            "speed_to_lead": "speed_to_lead",
            "follow_up_engine": "follow_up_engine",
            "database_reactivation": "database_reactivation",
            "crm_integration": "crm_integration",
            "END": END
        }
    )
    
    graph.add_conditional_edges(
        "database_reactivation",
        should_continue,
        {
            "speed_to_lead": "speed_to_lead",
            "follow_up_engine": "follow_up_engine",
            "database_reactivation": "database_reactivation",
            "crm_integration": "crm_integration",
            "END": END
        }
    )
    
    graph.add_conditional_edges(
        "crm_integration",
        should_continue,
        {
            "speed_to_lead": "speed_to_lead",
            "follow_up_engine": "follow_up_engine",
            "database_reactivation": "database_reactivation",
            "crm_integration": "crm_integration",
            "END": END
        }
    )
    
    return graph.compile()


_app_graph = None


def get_app_graph():
    """Get or create the app graph"""
    global _app_graph
    if _app_graph is None:
        _app_graph = build_graph()
    return _app_graph


async def process_lead(lead_data: dict, client_config: dict = None) -> dict:
    """
    Process a lead through the agent system
    This is the main entry point for processing new leads
    """
    from integrations.supabase_client import create_lead, get_client
    
    if not client_config:
        client = await get_client(lead_data.get("client_id", ""))
        client_config = client.get("config", {}) if client else {}
    
    state = LeadState(
        lead_id=lead_data.get("id", ""),
        name=lead_data.get("name", ""),
        email=lead_data.get("email", ""),
        phone=lead_data.get("phone", ""),
        source=lead_data.get("source", "website"),
        message=lead_data.get("message", ""),
        channel=lead_data.get("channel", "email"),
        status=lead_data.get("status", "new"),
        follow_up_count=lead_data.get("follow_up_count", 0),
        last_contact=datetime.utcnow().isoformat(),
        next_action="speed_to_lead",
        conversation_history=[],
        interest_score=lead_data.get("interest_score", 50),
        client_id=lead_data.get("client_id", ""),
        client_config=client_config
    )
    
    graph = get_app_graph()
    result = await graph.ainvoke(state)
    return result
