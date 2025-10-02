import os, time, httpx
from typing import Dict, Any, Optional, Literal

Provider = Literal["openai", "anthropic"]
from .usage_logger import log_usage

def _env(name: str, default: Optional[str]=None) -> Optional[str]:
    v = os.environ.get(name)
    return v if v is not None else default

def _retry_call(func, retries: int = 3, backoff: float = 0.8):
    last = None
    for i in range(retries):
        try:
            return func()
        except Exception as e:
            last = e
            time.sleep(backoff * (2 ** i))
    if last:
        raise last

def generate(prompt: str, *, provider: Provider = "openai", model: Optional[str]=None, **kwargs) -> str:
    """Generate text from the configured provider.
    Falls back to a local placeholder if no API key is set.
    """
    if provider == "openai":
        key = _env("OPENAI_API_KEY")
        base = _env("OPENAI_BASE_URL", "https://api.openai.com/v1")
        mdl = model or _env("OPENAI_MODEL", "gpt-4o-mini")
        if not key:
            return f"[openai:dry-run]\nPROMPT:\n{prompt[:2000]}"
        def _run():
            with httpx.Client(base_url=base, timeout=60) as client:
                r = client.post(
                    "/chat/completions",
                    headers={"Authorization": f"Bearer {key}"},
                    json={
                        "model": mdl,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": kwargs.get("temperature", 0.3),
                    },
                )
                r.raise_for_status()
                data = r.json()
                # record usage if provided
                usage = data.get('usage') or {}
                it = usage.get('prompt_tokens') or usage.get('input_tokens')
                ot = usage.get('completion_tokens') or usage.get('output_tokens')
                # very rough pricing defaults; override via env if needed
                price_in = float(_env('OPENAI_PRICE_IN', '0.000005'))  # $ per token
                price_out = float(_env('OPENAI_PRICE_OUT', '0.000015'))
                cost = (it or 0) * price_in + (ot or 0) * price_out
                try:
                    log_usage(run_id=kwargs.get('run_id'), actor=kwargs.get('actor'), model=mdl, input_tokens=it, output_tokens=ot, cost_usd=cost)
                except Exception:
                    pass
                return data['choices'][0]['message']['content']
        return _retry_call(_run)

    if provider == "anthropic":
        key = _env("ANTHROPIC_API_KEY")
        base = _env("ANTHROPIC_BASE_URL", "https://api.anthropic.com")
        mdl = model or _env("ANTHROPIC_MODEL", "claude-3-5-sonnet-20240620")
        if not key:
            return f"[anthropic:dry-run]\nPROMPT:\n{prompt[:2000]}"
        def _run():
            with httpx.Client(base_url=base, timeout=60, headers={
                "x-api-key": key,
                "anthropic-version": "2023-06-01"
            }) as client:
                r = client.post(
                    "/v1/messages",
                    json={
                        "model": mdl,
                        "max_tokens": kwargs.get("max_tokens", 1024),
                        "messages": [{"role": "user", "content": prompt}]
                    }
                )
                r.raise_for_status()
                data = r.json()
                # Anthropics returns a list of content blocks
                parts = data.get('content', [])
                usage = data.get('usage') or {}
                it = usage.get('input_tokens')
                ot = usage.get('output_tokens')
                price_in = float(_env('ANTHROPIC_PRICE_IN', '0.000003'))
                price_out = float(_env('ANTHROPIC_PRICE_OUT', '0.000015'))
                cost = (it or 0) * price_in + (ot or 0) * price_out
                try:
                    log_usage(run_id=kwargs.get('run_id'), actor=kwargs.get('actor'), model=mdl, input_tokens=it, output_tokens=ot, cost_usd=cost)
                except Exception:
                    pass
                text = ''.join([p.get('text', '') for p in parts if p.get('type') == 'text'])
                return text
        return _retry_call(_run)

    # Default fallback
    return f"[local:dry-run]\nPROMPT:\n{prompt[:2000]}"
