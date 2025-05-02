import psycopg2
from psycopg2.extras import RealDictCursor
import os

def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        database=os.getenv("POSTGRES_DB", "nubla_db"),
        user=os.getenv("POSTGRES_USER", "nubla_user"),
        password=os.getenv("POSTGRES_PASSWORD", "secure_password_123"),
        cursor_factory=RealDictCursor
    )