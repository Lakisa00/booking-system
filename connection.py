import mysql.connector
import os
from dotenv import load_dotenv
load_dotenv()
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_NAME = os.getenv("DB_NAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")

conn = mysql.connector.connect(
    host= DB_HOST,
    user= DB_USER,
    password= DB_PASSWORD,
    database= DB_NAME 
)
cursor = conn.cursor()
cursor.execute("""
SELECT DATABASE()
""")
record = cursor.fetchone()
print(record[0])