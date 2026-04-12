"""
Follow-up Scheduler
Runs every hour to check and send follow-ups for leads due
"""
from datetime import datetime, timedelta
import asyncio


async def process_due_followups():
    """
    Check which leads need follow-up and process them
    """
    from integrations.supabase_client import get_leads, get_clients
    from agents.follow_up_engine import follow_up_agent
    
    print(f"🔄 Checking for due follow-ups at {datetime.utcnow().isoformat()}")
    
    try:
        # Get all clients
        clients = await get_clients()
        
        for client in clients:
            client_id = client.get("id")
            if not client_id:
                continue
            
            # Get leads that need follow-up
            leads = await get_leads(client_id=client_id)
            
            now = datetime.utcnow()
            
            for lead in leads:
                status = lead.get("status", "")
                next_followup = lead.get("next_followup_at")
                follow_up_count = lead.get("follow_up_count", 0)
                
                # Skip if not in nurturing/contacted status
                if status not in ["contacted", "nurturing"]:
                    continue
                
                # Skip if exhausted follow-ups
                if follow_up_count >= 10:
                    continue
                
                # Check if it's time for follow-up
                if next_followup:
                    try:
                        next_time = datetime.fromisoformat(next_followup.replace('Z', '+00:00'))
                        if now < next_time:
                            continue  # Not due yet
                    except:
                        pass  # If we can't parse, process anyway
                
                # Build state and run follow-up
                state = {
                    "lead_id": lead["id"],
                    "name": lead.get("name", ""),
                    "email": lead.get("email", ""),
                    "phone": lead.get("phone", ""),
                    "source": lead.get("source", ""),
                    "message": lead.get("original_message", ""),
                    "channel": lead.get("channel", "email"),
                    "status": status,
                    "follow_up_count": follow_up_count,
                    "last_contact": lead.get("last_contact", now.isoformat()),
                    "next_action": "follow_up",
                    "conversation_history": [],
                    "interest_score": lead.get("interest_score", 50),
                    "client_id": client_id,
                    "client_config": client.get("config", {})
                }
                
                print(f"📤 Sending follow-up #{follow_up_count + 1} to {lead.get('name')}")
                
                try:
                    await follow_up_agent(state)
                except Exception as e:
                    print(f"Error processing follow-up for lead {lead['id']}: {e}")
                
                # Rate limiting between leads
                await asyncio.sleep(0.5)
        
        print("✅ Follow-up check complete")
        
    except Exception as e:
        print(f"Error in follow-up scheduler: {e}")


async def run_reactivation_batch():
    """
    Run database reactivation for all clients weekly
    """
    from integrations.supabase_client import get_clients
    from agents.database_reactivation import run_batch_reactivation
    
    print(f"🔄 Running weekly reactivation batch at {datetime.utcnow().isoformat()}")
    
    try:
        clients = await get_clients()
        
        for client in clients:
            client_id = client.get("id")
            if not client_id:
                continue
            
            print(f"🔄 Running reactivation for client {client.get('agency_name')}")
            
            try:
                results = await run_batch_reactivation(client_id, batch_size=50)
                print(f"✅ Reactivation results: {results}")
            except Exception as e:
                print(f"Error in reactivation for client {client_id}: {e}")
            
            # Rate limiting between clients
            await asyncio.sleep(2)
        
        print("✅ Weekly reactivation complete")
        
    except Exception as e:
        print(f"Error in reactivation batch: {e}")


# APScheduler setup (optional - can be triggered via cron)
def setup_scheduler():
    """
    Set up APScheduler for automated tasks
    Note: APScheduler is optional - you can also use cron/Render cron
    """
    try:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
        
        scheduler = AsyncIOScheduler()
        
        # Run follow-up check every hour
        scheduler.add_job(
            process_due_followups,
            'interval',
            hours=1,
            id='followup_check',
            name='Check and send due follow-ups'
        )
        
        # Run reactivation batch weekly (Sundays at 2am)
        scheduler.add_job(
            run_reactivation_batch,
            'cron',
            day_of_week='sun',
            hour=2,
            id='reactivation_batch',
            name='Weekly database reactivation'
        )
        
        return scheduler
    except ImportError:
        print("APScheduler not available - use external cron instead")
        return None


if __name__ == "__main__":
    # Test the scheduler
    async def test():
        await process_due_followups()
    
    asyncio.run(test())