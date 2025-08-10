import os
import io
import base64
import signal
import resource
import contextlib
import traceback
from typing import Dict, Any, Tuple, List, Optional

import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

STORAGE_ROOT = os.getenv('STORAGE_ROOT', '/data')
CHART_DIR = os.path.join(STORAGE_ROOT, 'charts')
os.makedirs(CHART_DIR, exist_ok=True)

BANNED_TOKENS = (
    'import ', '__', ' exec(', ' eval(', 'open(', 'os.', 'sys.', 'subprocess',
    'socket', 'requests', 'http', 'urllib', 'pickle', 'dill', 'ctypes', 'cffi',
    'multiprocessing', 'thread', 'input(', 'compile(', 'globals(', 'locals(',
)


def enforce_limits():
    # CPU seconds limit
    resource.setrlimit(resource.RLIMIT_CPU, (5, 5))
    # Address space (memory) limit: 512 MB
    mem_bytes = 512 * 1024 * 1024
    try:
        resource.setrlimit(resource.RLIMIT_AS, (mem_bytes, mem_bytes))
    except Exception:
        # Some platforms disallow RLIMIT_AS; best effort
        pass


def alarm_handler(signum, frame):
    raise TimeoutError('Execution exceeded time limit')


@contextlib.contextmanager
def time_limit(seconds: int):
    signal.signal(signal.SIGALRM, alarm_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)


def _sanitize(code: str) -> Optional[str]:
    low = code.lower()
    for tok in BANNED_TOKENS:
        if tok in low:
            return f"Use of '{tok.strip()}' is not allowed."
    return None


def run_user_code(code: str, csv_path: str) -> Dict[str, Any]:
    unsafe = _sanitize(code)
    if unsafe:
        return {"ok": False, "error": unsafe, "stdout": "", "stderr": unsafe}

    # Load df lazily; let pandas infer dtypes
    df = pd.read_csv(csv_path)

    # Prepare execution env
    user_globals: Dict[str, Any] = {
        'pd': pd,
        'plt': plt,
        'df': df,
    }

    stdout_buf, stderr_buf = io.StringIO(), io.StringIO()

    try:
        enforce_limits()
        with time_limit(5), contextlib.redirect_stdout(stdout_buf), contextlib.redirect_stderr(stderr_buf):
            exec(compile(code, '<user_code>', 'exec'), user_globals, user_globals)
    except TimeoutError as e:
        return {"ok": False, "error": str(e), "stdout": stdout_buf.getvalue(), "stderr": stderr_buf.getvalue()}
    except BaseException:
        tb = traceback.format_exc(limit=3)
        return {"ok": False, "error": tb, "stdout": stdout_buf.getvalue(), "stderr": stderr_buf.getvalue()}

    # Collect table (if any)
    out_df = None
    for key in ('out_df', 'result_df', 'result'):
        obj = user_globals.get(key)
        if isinstance(obj, pd.DataFrame):
            out_df = obj
            break

    table_json, columns = None, None
    if out_df is not None:
        # Limit payload size
        sample = out_df.head(200)
        table_json = sample.to_dict(orient='records')
        columns = list(sample.columns)

    # Collect any open figures as PNGs saved to shared storage
    chart_urls: List[str] = []
    try:
        figs = [plt.figure(num) for num in plt.get_fignums()]
        for fig in figs:
            img_name = f"{os.path.basename(csv_path).split('.')[0]}_{len(chart_urls)+1}.png"
            abs_path = os.path.join(CHART_DIR, img_name)
            fig.savefig(abs_path, format='png', bbox_inches='tight')
            plt.close(fig)
            chart_urls.append(f"/static/charts/{img_name}")
    except BaseException:
        # Ignore chart errors; return other outputs
        pass

    return {
        "ok": True,
        "stdout": stdout_buf.getvalue(),
        "stderr": stderr_buf.getvalue(),
        "table": table_json,
        "columns": columns,
        "chart_urls": chart_urls,
        "error": None,
    }