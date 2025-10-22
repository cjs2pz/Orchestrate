import psycopg2
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')

try:
    print("Attempting to connect to Supabase...")
    conn = psycopg2.connect(DATABASE_URL)
    print("✅ Connection successful!")
    
    # Test a simple query
    cursor = conn.cursor()
    cursor.execute("SELECT version();")
    version = cursor.fetchone()
    print(f"✅ PostgreSQL version: {version[0]}")
    
    cursor.close()
    conn.close()
    print("✅ Connection closed successfully")
    
except Exception as e:
    print(f"❌ Connection failed: {e}")