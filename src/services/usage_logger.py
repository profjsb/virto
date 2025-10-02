from typing import Optional
from ..db import SessionLocal
from ..db.models import UsageEvent

def log_usage(*, run_id: Optional[int], actor: Optional[str], model: Optional[str], input_tokens: Optional[int], output_tokens: Optional[int], cost_usd: Optional[float]):
    with SessionLocal() as db:
        ev = UsageEvent(run_id=run_id, actor=actor, model=model, input_tokens=input_tokens, output_tokens=output_tokens, cost_usd=cost_usd)
        db.add(ev)
        db.commit()
        db.refresh(ev)
        return ev.id
