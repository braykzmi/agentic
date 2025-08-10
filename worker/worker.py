from flask import Flask, request, jsonify
from sandbox_runtime import run_user_code

app = Flask(__name__)

@app.post('/execute')
def execute():
    data = request.get_json(force=True)
    code = data.get('code', '')
    csv_path = data.get('csv_path', '')
    if not code or not csv_path:
        return jsonify({"ok": False, "error": "code and csv_path are required"}), 400
    result = run_user_code(code, csv_path)
    status = 200 if result.get('ok') else 400
    return jsonify(result), status

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9000)