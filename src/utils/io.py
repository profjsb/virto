import json
from pathlib import Path
from typing import Any


def write_json(path: str, obj: Any):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2))
