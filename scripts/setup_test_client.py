#!/usr/bin/env python3
"""
Setup Test Client Script
Creates a test client in Supabase for development/testing
Run: python scripts/setup_test_client.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from integrations.supabase_client import create_client, get_clients


def setup_test_client():
    """Create a test client if one doesn't exist"""
    
    test_client_data = {
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
    
    print("Checking for existing test client...")
    
    try:
        existing_clients = get_clients()
        
        for client in existing_clients:
            if client.get("email") == test_client_data["email"]:
                print(f"✓ Test client already exists!")
                print(f"  Client ID: {client['id']}")
                print(f"  Agency: {client['agency_name']}")
                return client
        
        print("Creating new test client...")
        new_client = create_client(test_client_data)
        
        if new_client and new_client.get("id"):
            print("✓ Test client created successfully!")
            print(f"  Client ID: {new_client['id']}")
            print(f"  Agency: {new_client['agency_name']}")
            print(f"  Email: {new_client['email']}")
            return new_client
        else:
            print("✗ Failed to create test client")
            return None
            
    except Exception as e:
        print(f"✗ Error setting up test client: {e}")
        return None


def main():
    print("=" * 50)
    print("Lead Conversion System - Test Client Setup")
    print("=" * 50)
    print()
    
    client = setup_test_client()
    
    if client:
        print()
        print("=" * 50)
        print("Next Steps:")
        print("=" * 50)
        print(f"1. Use this Client ID for testing: {client['id']}")
        print()
        print("2. Test the webhook:")
        print(f"""
curl -X POST http://localhost:8000/webhook/new-lead \\
  -H "Content-Type: application/json" \\
  -d '{{
    "client_id": "{client['id']}",
    "name": "Test Lead",
    "email": "test@example.com",
    "message": "Interested in marketing services"
  }}'
        """)
        print()
        print("3. Check the dashboard at: http://localhost:8000/dashboard")
    else:
        print()
        print("Setup failed. Please check your Supabase configuration.")
        sys.exit(1)


if __name__ == "__main__":
    main()
