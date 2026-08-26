"""Serve the dashboard in PostgreSQL mode (DATABASE_URL from .env)."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))
os.environ['CSV_DIR'] = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'output', 'results', 'final1200')

import uvicorn
from dashboard_api import app

if __name__ == '__main__':
    uvicorn.run(app, host='127.0.0.1', port=8000)
