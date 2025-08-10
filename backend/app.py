import os
import io
import uuid
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import pandas as pd
from dotenv import load_dotenv

from schema_utils import infer_schema
from code_utils import extract_code, looks_unsafe
from openai_client import get_client
from worker_client import execute_in_worker

load_dotenv()

STORAGE_ROOT = os.getenv('STORAGE_ROOT', '/data')
UPLOAD_DIR = os.path.join(STORAGE_ROOT, 'uploads')
CHART_DIR = os.path.join(STORAGE_ROOT, 'charts')
MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(CHART_DIR, exist_ok=True)

app = Flask(__name__)
CORS(app)
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB


def _save_as_csv(df: pd.DataFrame) -> str:
    dsid = str(uuid.uuid4())
    path = os.path.join(UPLOAD_DIR, f"{dsid}.csv")
    df.to_csv(path, index=False)
    return dsid, path


@app.route('/api/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    f = request.files['file']
    if not f or f.filename == '':
        return jsonify({"error": "No selected file"}), 400

    name = f.filename.lower()
    notes = []
    try:
        if name.endswith('.csv'):
            data = f.read()
            buf = io.BytesIO(data)
            df = pd.read_csv(buf)
        elif name.endswith('.xlsx'):
            # Read first sheet only
            xdf = pd.ExcelFile(f)
            sheet = xdf.sheet_names[0]
            if len(xdf.sheet_names) > 1:
                notes.append(f"Multiple sheets detected; using first sheet: '{sheet}'.")
            df = pd.read_excel(xdf, sheet_name=sheet)
        else:
            return jsonify({"error": "Unsupported file type. Upload CSV or XLSX."}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to parse file: {e}"}), 400

    # Normalize: try to parse datetime columns
    for col in df.columns:
        try:
            dt = pd.to_datetime(df[col], errors='ignore')
            if getattr(dt, 'dtype', None) is not None and str(dt.dtype).startswith('datetime'):
                df[col] = dt
        except Exception:
            pass

    schema = infer_schema(df)
    dsid, path = _save_as_csv(df)

    preview = df.head(5).to_dict(orient='records')
    return jsonify({
        'dataset_id': dsid,
        'filename': f.filename,
        'storage_path': path,
        'schema': schema,
        'preview': preview,
        'notes': notes,
    })


SYSTEM_PROMPT = (
    "You are a Python data analysis assistant. Given a dataset 'df' (pandas DataFrame), "
    "answer the user's question ONLY by writing Python code that uses pandas and matplotlib. "
    "Rules: do not import anything; do not read files; do not mutate the filesystem; do not call plt.show(); "
    "If you produce a tabular answer, assign it to a variable named out_df. If you produce a chart, "
    "just create the figure/axes with matplotlib; the runtime will save any open figures. Keep it simple: "
    "bar or line charts only. Keep runtime under 5s."
)


@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json(force=True)
    dsid = data.get('dataset_id')
    question = data.get('question', '').strip()
    if not dsid or not question:
        return jsonify({"error": "dataset_id and question are required"}), 400

    csv_path = os.path.join(UPLOAD_DIR, f"{dsid}.csv")
    if not os.path.isfile(csv_path):
        return jsonify({"error": "Dataset not found (maybe expired). Re-upload."}), 404

    # Build lightweight schema context
    try:
        df_head = pd.read_csv(csv_path, nrows=5)
    except Exception:
        df_head = None

    schema_summary = []
    if df_head is not None:
        for col in df_head.columns:
            schema_summary.append({
                'name': col,
                'samples': df_head[col].head(3).tolist(),
            })

    client = get_client()

    user_prompt = (
        f"SCHEMA PREVIEW (first rows per column):\n{schema_summary}\n\n"
        f"TASK: {question}\n\n"
        "Write only Python code (no explanations) enclosed in a triple backtick block."
    )

    try:
        completion = client.chat.completions.create(
            model=MODEL,
            temperature=0.1,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
        )
        content = completion.choices[0].message.content or ''
        code = extract_code(content)
        unsafe = looks_unsafe(code)
        if unsafe:
            return jsonify({"error": unsafe, "generated": code}), 400
    except Exception as e:
        return jsonify({"error": f"LLM request failed: {e}"}), 500

    try:
        result = execute_in_worker(code=code, csv_path=csv_path)
    except Exception as e:
        return jsonify({"error": f"Worker failed: {e}", "generated": code}), 500

    # Pass-through with minor shape
    payload = {
        'ok': bool(result.get('ok')),
        'stdout': result.get('stdout',''),
        'stderr': result.get('stderr',''),
        'generated_code': code,
        'table': result.get('table'),            # list[dict] or None
        'columns': result.get('columns'),        # list[str] or None
        'charts': result.get('chart_urls', []),  # list[str]
        'error': result.get('error'),
    }
    status = 200 if payload['ok'] else 400
    return jsonify(payload), status


@app.route('/static/charts/<path:fname>')
def charts(fname):
    return send_from_directory(CHART_DIR, fname, as_attachment=False)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)