import requests
import os

WORKER_URL = os.getenv('WORKER_URL', 'http://localhost:9000')

def execute_in_worker(code: str, csv_path: str):
    url = f"{WORKER_URL}/execute"
    resp = requests.post(url, json={"code": code, "csv_path": csv_path}, timeout=15)
    resp.raise_for_status()
    return resp.json()