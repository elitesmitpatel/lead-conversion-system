"""
Agent Worker Entry Point
Run as: python -m agents.scheduler
Or: python -m agents
"""
import os
import sys
import asyncio
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point for the worker process"""
    logger.info("=" * 50)
    logger.info("Lead Conversion System - Worker Starting")
    logger.info(f"Started at: {datetime.utcnow().isoformat()}")
    logger.info("=" * 50)
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        from agents.scheduler import setup_scheduler, process_due_followups, run_reactivation_batch
        
        scheduler = setup_scheduler()
        
        if scheduler:
            scheduler.start()
            logger.info("Scheduler started successfully")
            logger.info("Jobs scheduled:")
            logger.info("  - Follow-up check: Every hour")
            logger.info("  - Reactivation batch: Sundays at 2am")
            
            asyncio.get_event_loop().run_forever()
        else:
            logger.warning("APScheduler not available, running single check instead")
            asyncio.run(process_due_followups())
            
    except KeyboardInterrupt:
        logger.info("Worker stopped by user")
    except Exception as e:
        logger.error(f"Worker error: {e}")
        raise


if __name__ == "__main__":
    main()
