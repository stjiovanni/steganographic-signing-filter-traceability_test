import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))
url = os.getenv('DATABASE_URL')
print('DATABASE_URL set:', bool(url), '| host part:', url.split('@')[-1] if url else None)
import psycopg2
try:
    conn = psycopg2.connect(url, connect_timeout=5)
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM hash_results')
    print('DB CONNECTED; hash_results rows =', cur.fetchone()[0])
    conn.close()
except Exception as e:
    print('DB CONNECT FAILED:', type(e).__name__, str(e)[:200])