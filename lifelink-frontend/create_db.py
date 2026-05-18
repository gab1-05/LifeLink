import pymysql
import os
from dotenv import load_dotenv
load_dotenv()

host = os.environ.get("DB_HOST", "127.0.0.1")
user = os.environ.get("DB_USER", "root")
password = os.environ.get("DB_PASSWORD", "")
port = int(os.environ.get("DB_PORT", 3306))
db_name = os.environ.get("DB_NAME", "lifelink_db")

print(f"Connecting to MySQL at {host}:{port} as {user}...")

connection = pymysql.connect(
    host=host,
    user=user,
    password=password,
    port=port
)

try:
    with connection.cursor() as cursor:
        
        cursor.execute(f"DROP DATABASE IF EXISTS {db_name};") 
        cursor.execute(f"CREATE DATABASE {db_name};")
    connection.commit()
    print(f"Database {db_name} recreated successfully.")
finally:
    connection.close()
