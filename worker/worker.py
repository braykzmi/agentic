from flask import Flask, request, jsonify, send_from_directory
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
import resource
import signal

app = Flask(__name__)
OUTPUT_DIR = os.environ.get('CHART_DIR', 'output')
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Charts should be saved to OUTPUT_DIR and path stored in chart_path variable

def limit_resources():
    resource.setrlimit(resource.RLIMIT_CPU, (5, 5))
    resource.setrlimit(resource.RLIMIT_AS, (512 * 1024 * 1024, 512 * 1024 * 1024))

class TimeoutException(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutException()

@app.route('/execute', methods=['POST'])
def execute_code():
    payload = request.get_json()
    code = payload.get('code')
    global_vars = {'pd': pd, 'plt': plt, 'result': None, 'chart_path': None}
    try:
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(5)
        limit_resources()
        exec(code, global_vars)
        signal.alarm(0)
        resp = {}
        if isinstance(global_vars.get('result'), pd.DataFrame):
            resp['table'] = global_vars['result'].to_dict(orient='records')
        chart_path = global_vars.get('chart_path')
        if not chart_path and plt.get_fignums():
            chart_path = os.path.join(OUTPUT_DIR, 'chart.png')
            plt.savefig(chart_path)
        if chart_path:
            resp['image'] = f'/charts/{os.path.basename(chart_path)}'
        return jsonify(resp)
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/charts/<path:name>')
def send_chart(name):
    return send_from_directory(OUTPUT_DIR, name)

if __name__ == '__main__':
    app.run(port=8001)
