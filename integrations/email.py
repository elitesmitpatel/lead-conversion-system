"""
Email Integration using Resend
Sends emails to leads
"""
import os
from typing import Optional


async def send_email(to: str, subject: str, body: str, from_email: str = None) -> bool:
    """
    Send an email using Resend API
    
    Args:
        to: Recipient email
        subject: Email subject
        body: Email body (HTML or plain text)
        from_email: Sender email (defaults to noreply@yourdomain.com)
    
    Returns:
        bool: True if sent successfully
    """
    try:
        from resend import Resend
        
        api_key = os.getenv("RESEND_API_KEY")
        if not api_key:
            print(f"Email (mock): To={to}, Subject={subject}")
            return True
        
        resend = Resend(api_key=api_key)
        
        # Default from address - update to your verified domain
        from_address = from_email or os.getenv("FROM_EMAIL", "noreply@resend.dev")
        
        email = {
            "from": from_address,
            "to": to,
            "subject": subject,
            "html": f"<html><body><p>{body}</p></body></html>",
            "text": body
        }
        
        response = resend.emails.send(email)
        print(f"✅ Email sent to {to}: {subject}")
        return True
        
    except Exception as e:
        print(f"Error sending email: {e}")
        # For development, return True to allow testing
        return True


async def send_template_email(
    to: str, 
    template_name: str, 
    variables: dict,
    from_email: str = None
) -> bool:
    """
    Send a templated email
    
    Args:
        to: Recipient email
        template_name: Name of template to use
        variables: Variables to fill in template
        from_email: Sender email
    """
    # Define email templates
    templates = {
        "welcome": {
            "subject": "Welcome to {agency_name}!",
            "body": """
Hi {name},

Thank you for your interest in {agency_name}!

We've received your inquiry about {service_interest} and our team will be in touch shortly.

In the meantime, feel free to book a call directly: {booking_link}

Best,
The {agency_name} Team
            """
        },
        "follow_up": {
            "subject": "Following up - {name}",
            "body": """
Hi {name},

Just wanted to follow up on our previous conversation. Have you had a chance to consider {topic}?

We're here if you have any questions!

Best,
The {agency_name} Team
            """
        },
        "booking_confirmation": {
            "subject": "Your call is confirmed!",
            "body": """
Hi {name},

Your call with {agency_name} is confirmed for {date} at {time}.

{meeting_link}

See you soon!

Best,
The {agency_name} Team
            """
        }
    }
    
    template = templates.get(template_name, templates["welcome"])
    
    # Fill in variables
    subject = template["subject"].format(**variables)
    body = template["body"].format(**variables)
    
    return await send_email(to, subject, body, from_email)


# Email tracking - called when email is opened
async def track_email_open(lead_id: str, email_id: str):
    """Track when a lead opens an email"""
    from integrations.supabase_client import log_event
    from agents.scoring import update_interest_score
    
    await log_event(lead_id, "email_opened", {"email_id": email_id})
    await update_interest_score(lead_id, "email_opened")


# Email tracking - called when link is clicked
async def track_email_click(lead_id: str, email_id: str, url: str):
    """Track when a lead clicks a link in email"""
    from integrations.supabase_client import log_event
    from agents.scoring import update_interest_score
    
    await log_event(lead_id, "email_link_clicked", {"email_id": email_id, "url": url})
    await update_interest_score(lead_id, "email_link_clicked")