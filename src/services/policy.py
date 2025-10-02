from pathlib import Path
import yaml

POLICY_PATH = Path(__file__).resolve().parents[2] / "governance" / "policies.yaml"

def load_policies():
    if not POLICY_PATH.exists():
        return {}
    with open(POLICY_PATH, "r") as f:
        return yaml.safe_load(f) or {}

def spend_threshold(policy: dict) -> float:
    thresholds = (policy or {}).get("spend_thresholds", {})
    auto = thresholds.get("auto_approve_usd", 50)
    try:
        return float(auto)
    except Exception:
        return 50.0
