"""
Lead Conversion System - LangGraph Orchestrator
Routes leads to the appropriate agent based on their status
"""
from typing import TypedDict, Literal
from langgraph.graph import StateGraph, END
from datetime import datetime
import os
import asyncio

# Import all agents
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
    status: Literal["new", "contacted", "nurturing", "booked", "dead", "won"]
    follow_up_count: int
    last_contact: str
    next_action: str
    conversation_history: list
    interest_score: int
    client_id: str
    client_config: dict


def route_lead(state: LeadState) -> str:
    """
    Central router - decides which agent handles this lead
    """
    status = state.get("status", "new")
    next_action = state.get("next_action", "")
    follow_up_count = state.get("follow_up_count", 0)
    
    if next_action == "speed_to_lead" or status == "new":
        return "speed_to_lead"
    elif next_action == "follow_up" or (status == "contacted" and follow_up_count < 10):
        return "follow_up_engine"
    elif next_action == "reactivation" or status == "dead":
        return "database_reactivation"
    elif next_action == "sync_crm":
        return "crm_integration"
    else:
        return END


def should_continue(state: LeadState) -> Literal["continue", "end"]:
    """Determine if we should continue the conversation"""
    status = state.get("status", "new")
    
    if status in ["booked", "won", "lost", "dead"]:
        return "end"
    return "continue"


def build_graph():
    """
    Build the LangGraph state machine
    """
    # Create the graph
    graph = StateGraph(LeadState)
    
    # Add nodes
    graph.add_node("speed_to_lead", speed_to_lead_agent)
    graph.add_node("follow_up_engine", follow_up_agent)
    graph.add_node("database_reactivation", reactivation_agent)
    graph.add_node("crm_integration", crm_sync_agent)
    
    # Set entry point
    graph.set_entry_point("router")
    
    # Add conditional routing
    graph.add_conditional_edges(
        "router",
        route_lead,
        {
            "speed_to_lead": "speed_to_lead",
            "follow_up_engine": "follow_up_engine",
            "database_reactivation": "database_reactivation",
            "crm_integration": "crm_integration",
            END: END
        }
    )
    
    # After each agent completes, check if we should continue
    graph.add_conditional_edges(
        "speed_to_lead",
        should_continue,
        {"continue": "router", "end": END}
    )
    
    graph.add_conditional_edges(
        "follow_up_engine",
        should_continue,
        {"continue": "router", "end": END}
    )
    
    graph.add_conditional_edges(
        "database_reactivation",
        should_continue,
        {"continue": "follow_up_engine", "end": END}
    )
    
    graph.add_conditional_edges(
        "crm_integration",
        should_continue,
        {"continue": "router", "end": END}
    )
    
    # Compile the graph
    return graph.compile()


# Singleton graph instance
_app_graph = None


def get_app_graph():
    """Get or create the app graph"""
    global _app_graph
    if _app_graph is None:
        _app_graph = build_graph()
    return _app_graph