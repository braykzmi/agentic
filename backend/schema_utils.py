import pandas as pd
from typing import Dict, Any, List

HUMAN_TYPES = {
    'i': 'integer',
    'u': 'unsigned integer',
    'f': 'float',
    'b': 'boolean',
    'O': 'string',
    'M': 'datetime',
}

def infer_schema(df: pd.DataFrame) -> Dict[str, Any]:
    cols: List[Dict[str, Any]] = []
    for col in df.columns:
        series = df[col]
        inferred = str(series.dtype)
        kind = getattr(series.dtype, 'kind', 'O')
        human = HUMAN_TYPES.get(kind, 'string')
        # Try datetime detection if looks like object/strings
        if human == 'string':
            dt = pd.to_datetime(series, errors='coerce', utc=False)
            if dt.notna().mean() >= 0.8:
                human = 'datetime'
        # Simple numeric detection for object columns
        if human == 'string':
            try:
                num = pd.to_numeric(series, errors='coerce')
                if num.notna().mean() >= 0.8:
                    human = 'float' if (num % 1 != 0).any() else 'integer'
            except Exception:
                pass
        samples = series.head(5).tolist()
        cols.append({
            'name': col,
            'dtype': inferred,
            'inferred_type': human,
            'non_null_ratio': float(series.notna().mean()),
            'sample_values': samples,
        })
    return {
        'nrows': int(len(df)),
        'ncols': int(df.shape[1]),
        'columns': cols,
    }