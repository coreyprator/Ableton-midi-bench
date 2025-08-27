# src/midi_benchmark/sql_load.py

from __future__ import annotations

import os
import math
import datetime as dt
from typing import Any, Dict, Iterable, List, Optional, Tuple

import pandas as pd

try:
    import pyodbc  # type: ignore
except Exception as ex:  # pragma: no cover
    pyodbc = None  # will raise at connect time


# -----------------------------
# Connection / configuration
# -----------------------------

def _default_cfg() -> Dict[str, Any]:
    return {
        "server": r"(localdb)\MSSQLLocalDB",
        "database": "ableton-midi-bench",
        "odbc_driver": "ODBC Driver 17 for SQL Server",
        "encrypt": False,
        "trust_server_certificate": False,
        "mars": True,
    }


def _cfg_to_dict(cfg: Any) -> Dict[str, Any]:
    """
    Accept either a dict-like or an object with attributes
    (e.g., a dataclass from the GUI). Missing attrs fall back to defaults.
    """
    if cfg is None:
        return {}
    if isinstance(cfg, dict):
        return dict(cfg)

    # Attribute-based (dataclass / SimpleNamespace / custom object)
    keys = [
        "server",
        "database",
        "odbc_driver",
        "encrypt",
        "trust_server_certificate",
        "mars",
    ]
    d: Dict[str, Any] = {}
    for k in keys:
        if hasattr(cfg, k):
            d[k] = getattr(cfg, k)
    return d


def build_conn_str(cfg: Optional[Dict[str, Any] | Any] = None) -> str:
    c = {**_default_cfg(), **_cfg_to_dict(cfg)}
    driver = c["odbc_driver"]
    server = c["server"]
    database = c["database"]
    encrypt = "yes" if bool(c.get("encrypt")) else "no"
    tsc = "yes" if bool(c.get("trust_server_certificate")) else "no"
    mars = "yes" if bool(c.get("mars", True)) else "no"

    # LocalDB + Windows auth
    conn = (
        f"DRIVER={{{driver}}};"
        f"SERVER={server};"
        f"DATABASE={database};"
        f"Trusted_Connection=yes;"
        f"Encrypt={encrypt};"
        f"TrustServerCertificate={tsc};"
        f"MARS_Connection={mars}"
    )
    return conn


def _get_connection(cfg: Optional[Dict[str, Any] | Any] = None):
    if pyodbc is None:  # pragma: no cover
        raise RuntimeError("pyodbc is not available in this environment.")
    conn_str = build_conn_str(cfg)
    return pyodbc.connect(conn_str, autocommit=False)


# -----------------------------
# DataFrame -> SQL helpers
# -----------------------------

# canonical table columns in dbo.reference_notes / dbo.performance_notes
_SQL_COLS: List[str] = [
    "track_index",
    "track_name",
    "is_drum",
    "channel",
    "program",
    "pitch",
    "note_name",
    "octave",
    "start_s",
    "end_s",
    "dur_s",
    "velocity",
    "beat_absolute",
    "bar_index",
    "beat_in_bar",
    "bar_beat_label",
    "source_filename",
    "source_file_mtime",
]

# map possible incoming DataFrame column names -> SQL column names
_ALIAS_MAP: Dict[str, str] = {
    # timings
    "start": "start_s",
    "end": "end_s",
    "dur": "dur_s",
    "onset": "start_s",  # just in case
    # velocity shorthand
    "vel": "velocity",
    # pitch naming niceties
    "note": "pitch",
    # beat fields sometimes named differently
    "bar": "bar_index",
    "beat_in_measure": "beat_in_bar",
}

_INT_COLS = {"track_index", "is_drum", "channel", "program", "pitch", "octave", "bar_index"}
_FLOAT_COLS = {"start_s", "end_s", "dur_s", "beat_absolute", "beat_in_bar"}
_STR_COLS = {"track_name", "note_name", "bar_beat_label", "source_filename"}
_DT_COLS = {"source_file_mtime"}  # we’ll pass as datetime or ISO string


def _filename_and_mtime(path: str) -> Tuple[str, Optional[dt.datetime]]:
    fname = os.path.basename(path) if path else None
    mtime = None
    try:
        if path and os.path.exists(path):
            mtime = dt.datetime.fromtimestamp(os.path.getmtime(path))
    except Exception:
        mtime = None
    return (fname or "", mtime)


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    # rename aliases to canonical names (non-destructive copy)
    cols = {c: _ALIAS_MAP.get(c, c) for c in df.columns}
    out = df.rename(columns=cols).copy()

    # add any missing columns as None
    for c in _SQL_COLS:
        if c not in out.columns:
            out[c] = None

    # reorder
    out = out[_SQL_COLS]
    return out


def _coerce_value(value: Any, target: str) -> Any:
    """Coerce a single value to the correct SQL type, mapping NaN to None."""
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None

    if target in _INT_COLS:
        # Some integer-like columns may arrive as floats (e.g., 0.0), coerce safely
        try:
            return int(value)
        except Exception:
            return None

    if target in _FLOAT_COLS:
        try:
            return float(value)
        except Exception:
            return None

    if target in _DT_COLS:
        if isinstance(value, dt.datetime):
            return value
        # accept str -> try parse ISO
        if isinstance(value, str):
            try:
                return dt.datetime.fromisoformat(value)
            except Exception:
                return None
        return None

    # strings or anything else
    return str(value) if value is not None else None


def _coerce_dataframe(out: pd.DataFrame) -> pd.DataFrame:
    coerced = out.copy()
    for c in _SQL_COLS:
        coerced[c] = coerced[c].apply(lambda v: _coerce_value(v, c))
    return coerced


def _rows_for_insert(df: pd.DataFrame) -> Iterable[Tuple[Any, ...]]:
    for row in df.itertuples(index=False, name=None):
        yield tuple(row)


def _truncate_table(cur, table: str):
    cur.execute(f"TRUNCATE TABLE {table};")


def insert_notes_df(
    df: pd.DataFrame,
    table: str,
    source_path: str,
    cfg: Optional[Dict[str, Any] | Any] = None,
    truncate: bool = False,
) -> int:
    """
    Insert a notes DataFrame into the given table.
    Returns number of rows inserted.
    """
    if df is None or len(df) == 0:
        # Nothing to do, but still return 0 safely
        return 0

    # Normalize + fill source filename / mtime
    out = _normalize_columns(df)

    fname, mtime = _filename_and_mtime(source_path)
    if "source_filename" in out.columns:
        out["source_filename"] = fname
    if "source_file_mtime" in out.columns:
        out["source_file_mtime"] = mtime

    # Coerce to SQL-safe types (NaN -> None, ints/floats/datetimes)
    out = _coerce_dataframe(out)

    # Build INSERT statement in canonical column order
    cols_sql = ", ".join(f"[{c}]" for c in _SQL_COLS)
    params = ", ".join("?" for _ in _SQL_COLS)
    insert_sql = f"INSERT INTO {table} ({cols_sql}) VALUES ({params});"

    # Execute
    with _get_connection(cfg) as cn:
        cur = cn.cursor()
        try:
            if truncate:
                _truncate_table(cur, table)
            cur.fast_executemany = True  # speed up bulk insert
            cur.executemany(insert_sql, _rows_for_insert(out[_SQL_COLS]))
            cn.commit()
            return len(out)
        except Exception:
            cn.rollback()
            raise
        finally:
            cur.close()
