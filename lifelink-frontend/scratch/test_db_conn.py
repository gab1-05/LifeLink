import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

try:
    conn = pymysql.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "lifelink_db"),
        port=int(os.getenv("DB_PORT", 3306))
    )
    print("SUCCESS: Connected to MySQL")
    conn.close()
except Exception as e:
    print(f"FAILURE: {e}")
