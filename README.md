# No‑Code Data Analysis MVP

A minimal full‑stack app that lets a user upload a CSV/XLSX and ask free‑text questions. The backend prompts GPT for **Python (pandas/matplotlib)**, executes it inside a constrained worker container, then returns tables and charts.

## Quick Start

### Prereqs
- Docker + docker compose
- OpenAI API key

### 1) Configure

Create an `.env` file at repository root: