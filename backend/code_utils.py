import re
from typing import Optional

BLOCK_RE = re.compile(r"```python\n(.*?)```|```\n(.*?)```", re.DOTALL | re.IGNORECASE)

BANNED_TOKENS = [
    'import ', ' __', ' exec(', ' eval(', 'open(', 'os.', 'sys.', 'subprocess',
    'shutil', 'socket', 'requests', 'httpx', 'urllib', 'ftplib', 'pickle', 'dill',
    'builtins', 'globals(', 'locals(', 'compile(', 'input(', 'setattr(', 'getattr(',
    'delattr(', 'memoryview', 'ctypes', 'cffi', 'multiprocessing', 'thread', 'fork',
]


def extract_code(text: str) -> str:
    match = BLOCK_RE.search(text or '')
    if match:
        return (match.group(1) or match.group(2) or '').strip()
    return (text or '').strip()


def looks_unsafe(code: str) -> Optional[str]:
    lower = code.lower()
    for tok in BANNED_TOKENS:
        if tok in lower:
            return f"Use of '{tok.strip()}' is not allowed in the sandbox."
    return None