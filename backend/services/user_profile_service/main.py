# backend/services/user_profile_service/main.py
import os
import psycopg2
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

# --- Database Connection ---
DATABASE_URL = os.getenv("DATABASE_URL")

def get_db_connection():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except psycopg2.OperationalError as e:
        print(f"Error connecting to the database: {e}")
        raise HTTPException(status_code=500, detail="Database connection error")

# --- Pydantic Models ---
class Preference(BaseModel):
    user_id: int
    key: str
    value: str

# --- Database Logic Functions (MODIFIED) ---
def save_user_preference(pref_dict: dict, conn):
    """
    Saves or updates a user preference in the database from a dictionary.
    The connection is NOT closed here; it's managed by the calling function.
    """
    try:
        with conn.cursor() as cur:
            # "Upsert" logic using dictionary key access
            cur.execute("""
                INSERT INTO user_preferences (user_id, key, value)
                VALUES (%s, %s, %s)
                ON CONFLICT (user_id, key)
                DO UPDATE SET value = EXCLUDED.value;
            """, (pref_dict['user_id'], pref_dict['key'], pref_dict['value']))
            conn.commit()
            print(f"--- Saved preference: {{'key': '{pref_dict['key']}', 'value': '{pref_dict['value']}'}} for user_id: {pref_dict['user_id']} ---")
    except Exception as e:
        conn.rollback()
        print(f"Error saving preference: {e}")
        # Re-raise the exception so the caller knows something went wrong
        raise e

def get_user_preferences(user_id: int, conn):
    """
    Retrieves all preferences for a given user.
    The connection is NOT closed here; it's managed by the calling function.
    """
    preferences = {}
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT key, value FROM user_preferences WHERE user_id = %s;", (user_id,))
            rows = cur.fetchall()
            for row in rows:
                preferences[row[0]] = row[1]
        print(f"--- Fetched preferences for user_id {user_id}: {preferences} ---")
        return preferences
    except Exception as e:
        print(f"Error fetching preferences: {e}")
        return {} # Return empty dict on error

# --- API Router ---
router = APIRouter(
    prefix="/users",
    tags=["User Profile Service"],
)

@router.post("/initialize_database", summary="Create database tables and dummy user")
def initialize_database(conn=Depends(get_db_connection)):
    """
    Creates tables, enables pgvector, and creates a dummy user with ID 1 if one doesn't exist.
    """
    try:
        with conn.cursor() as cur:
            # ... (rest of the function is unchanged)
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY, email VARCHAR(255) UNIQUE NOT NULL, created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS user_preferences (
                    id SERIAL PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id), key VARCHAR(255) NOT NULL, value VARCHAR(255) NOT NULL, created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, UNIQUE(user_id, key)
                );
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS past_canvases (
                    id SERIAL PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id), canvas_data JSONB NOT NULL, created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
            """)
            cur.execute("""
                INSERT INTO users (id, email)
                VALUES (1, 'dummyuser@agentive.pro')
                ON CONFLICT (id) DO NOTHING;
            """)
            print("Dummy user with ID 1 ensured.")
            conn.commit()
        return {"status": "Database initialized successfully."}
    finally:
        # This function manages its own connection, so it's okay to close here.
        conn.close()