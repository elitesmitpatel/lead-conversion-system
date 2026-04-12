#!/usr/bin/env python3
"""
Setup Test Client Script - Synchronous Version
Creates a test client in Supabase for development/testing
Run: python scripts/setup_test_client.py
"""
import os
from dotenv import load_dotenv
load_dotenv()

from supabase import create_client

def main():
    print("=" * 50)
    print("Lead Conversion System - Test Client Setup")
    print("=" * 50)
    print()
    
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    if not url or not key:
        print("Error: SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY not set")
        return
    
    client = create_client(url, key)
    
    print("Checking for existing test client...")
    
    response = client.table("clients").select("*").eq("email", "test@agency.com").execute()
    
    if response.data:
        existing = response.data[0]
        print(f"[OK] Test client already exists!")
        print(f"  Client ID: {existing['id']}")
        print(f"  Agency: {existing['agency_name']}")
        client_id = existing['id']
    else:
        print("Creating new test client...")
        
        test_data = {
            "agency_name": "Test Marketing Agency",
            "email": "test@agency.com",
            "phone": "+1234567890",
            "calcom_link": "https://cal.com/test-agency",
            "config": {
                "primary_channel": "email",
                "tone": "professional",
                "timezone": "America/New_York",
                "owner_email": "elitesmit@gmail.com"
            },
            "is_active": True
        }
        
        response = client.table("clients").insert(test_data).execute()
        
        if response.data:
            new_client = response.data[0]
            print(f"[OK] Test client created!")
            print(f"  Client ID: {new_client['id']}")
            print(f"  Agency: {new_client['agency_name']}")
            client_id = new_client['id']
        else:
            print("[ERROR] Failed to create test client")
            return
    
    print()
    print("=" * 50)
    print("Next Steps:")
    print("=" * 50)
    print(f"1. Use this Client ID for testing:")
    print(f"   {client_id}")
    print()
    print("2. Test the webhook:")
    print(f"""
curl -X POST https://lead-conversion-system.onrender.com/webhook/new-lead \\
  -H "Content-Type: application/json" \\
  -d '{{
    "client_id": "{client_id}",
    "name": "John Doe",
    "email": "john@example.com",
    "message": "Interested in your services"
  }}'
    """)
    print()
    print("3. Check dashboard: https://lead-conversion-system.onrender.com/dashboard")
    print()

if __name__ == "__main__":
    main()
