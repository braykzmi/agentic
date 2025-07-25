# ChatGPT Data Analysis MVP

This repository contains a minimal proof-of-concept web application that lets a user upload a CSV or XLSX file and ask questions about the data using ChatGPT.

## Structure

- **frontend/** – React interface for file upload and chat
- **backend/** – Flask API for file parsing and ChatGPT requests
- **worker/** – Dockerized Python sandbox for executing GPT generated code

## Running Locally

Set your OPENAI_API_KEY environment variable before running the backend.
1. Start the worker service:
   ```bash
   cd worker
   docker build -t data-worker .
   docker run -p 8001:8001 data-worker
   ```
2. Install backend requirements and start the API:
   ```bash
   cd backend
   pip install -r requirements.txt
   python app.py
   ```
3. In another terminal start the React dev server:
   ```bash
   cd frontend
   npm install
   npm run start
   ```

Upload a CSV/XLSX file (≤10 MB) and start asking questions!
