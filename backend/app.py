import os
import tempfile
from flask import Flask, request, jsonify, send_from_directory
import pandas as pd
import openai

openai.api_key = os.environ.get("OPENAI_API_KEY")
app = Flask(__name__)
app.static_folder = "../frontend/public"
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['CHART_FOLDER'] = 'charts'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['CHART_FOLDER'], exist_ok=True)

# Simple in-memory store for uploaded DataFrame
DATAFRAME = None
SCHEMA = None

@app.route('/upload', methods=['POST'])
def upload_file():
    global DATAFRAME, SCHEMA
    file = request.files.get('file')
    if not file:
        return jsonify({'error': 'no file'}), 400
    path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(path)
    if file.filename.lower().endswith('.xlsx'):
        df = pd.read_excel(path)
    else:
        df = pd.read_csv(path)
    DATAFRAME = df
    SCHEMA = {c: str(df[c].dtype) for c in df.columns}
    preview = df.head().to_dict(orient='records')
    return jsonify({'preview': preview, 'schema': SCHEMA})

@app.route('/chat', methods=['POST'])
def chat():
    if DATAFRAME is None:
        return jsonify({'error': 'no data uploaded'}), 400
    data = request.get_json()
    question = data.get('message')
    if not question:
        return jsonify({'error': 'no message'}), 400

    system_prompt = (
        "You are a data analyst. The user has uploaded a DataFrame with this schema:\n"
        f"{SCHEMA}."
        " Write Python pandas code (with matplotlib if needed) to answer the user's question."
        " Return only code inside a Markdown code block.")

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question}
        ],
        temperature=0
    )
    code = response['choices'][0]['message']['content']

    result = run_code(code)
    return jsonify(result)

def run_code(code_block: str):
    """Send code to worker for execution."""
    import requests
    # Expect code_block contains ```python ...```
    if '```' in code_block:
        code = code_block.split('```')[1]
    else:
        code = code_block
    # Send to local worker
    try:
        resp = requests.post('http://localhost:8001/execute', json={
            'code': code,
            'schema': SCHEMA
        }, timeout=10)
        return resp.json()
    except Exception as e:
        return {'error': str(e)}

@app.route('/charts/<path:name>')
def get_chart(name):
    return send_from_directory(app.config['CHART_FOLDER'], name)

@app.route('/')
def index():
    return app.send_static_file('index.html')

if __name__ == '__main__':
    app.run(port=8000, debug=True)
