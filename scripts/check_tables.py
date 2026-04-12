#!/usr/bin/env python3
"""
Check existing table structure
"""
import os
from dotenv import load_dotenv
load_dotenv()

from supabase import create_client

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

client = create_client(url, key)

tables = ['agents', 'goals', 'lead_conversion_contacts']
for table in tables:
    print(f"\n=== {table} ===")
    try:
        response = client.table(table).select("*").execute()
        if response.data:
            print("Columns:", list(response.data[0].keys()))
            print("Sample data:", response.data[0])
        else:
            print("Empty table")
    except Exception as e:
        print(f"Error: {e}")
