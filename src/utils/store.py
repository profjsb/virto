import datetime
import json
from pathlib import Path

from .s3 import STORE_TO_S3, upload_file

DATA_ROOT = Path(__file__).resolve().parents[2] / "data"
DATA_ROOT.mkdir(parents=True, exist_ok=True)


def ts() -> str:
    return datetime.datetime.utcnow().strftime("%Y%m%d-%H%M%S")


def save_json(namespace: str, name: str, obj):
    p = DATA_ROOT / namespace
    p.mkdir(parents=True, exist_ok=True)
    f = p / f"{name}.json"
    f.write_text(json.dumps(obj, indent=2))
    return str(f)


def save_markdown(namespace: str, name: str, md: str):
    p = DATA_ROOT / namespace
    p.mkdir(parents=True, exist_ok=True)
    f = p / f"{name}.md"
    f.write_text(md)
    return str(f)


def list_namespace(namespace: str):
    p = DATA_ROOT / namespace
    if not p.exists():
        return []
    return sorted([str(x) for x in p.iterdir() if x.is_file()])


def maybe_upload(namespace: str, name: str, local_path: str, ext: str):
    key = f"artifacts/{namespace}/{name}{ext}"
    info = upload_file(local_path, key) if STORE_TO_S3 else None
    return info
