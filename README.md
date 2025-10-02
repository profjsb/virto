# Virtual AI Organization (VO) — Bootstrap

A minimal, production-friendly starter for a virtual organization staffed by AI agents. 
It includes a governance baseline, meeting templates, JSON schemas, and a tiny API 
to request approvals and generate a hiring plan.

## Quickstart

```bash
# Python 3.10+ recommended
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Run the API (http://127.0.0.1:8000/docs)
uvicorn src.app:app --reload
```

## What’s inside

- `/src` — FastAPI app + orchestration stubs
- `/governance` — machine-readable policies
- `/meetings/templates` — stand-up, brainstorm, all-hands
- `/schemas` — hiring plan & persona JSON schemas
- `/personas` — example co‑founder personas
- `/docs/adr` — Architecture Decision Records (templates)
- `/tests` — placeholder for unit tests

## Next steps
1. Fill in your VO Charter in `governance/constitution.md`.
2. Connect your LLM of choice in `src/services/llm_provider.py` (env-driven).
3. Implement the hiring plan generator with a real model call.
4. Wire meeting flows to your chosen orchestrator in `src/orchestration/flows.py`.
5. Add storage backends (Postgres/S3/vector DB) and observability (OpenTelemetry).


## Postgres & Migrations

1. Set `DATABASE_URL` in your environment, e.g.:
   ```bash
   export DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/virtual_ai_org
   ```
2. Run migrations:
   ```bash
   alembic upgrade head
   ```

## React Ops Console

```bash
cd console
npm install
# optional: export VITE_API_BASE=http://localhost:8000
npm run dev
```


## Auth
Set a secret and (optionally) allow open signup for first user:
```bash
export JWT_SECRET='change-me'
export ADMIN_SIGNUP_SECRET='let-me-in'  # optional
export ALLOW_SIGNUP=true                 # allow first registration without admin secret
```

Register (one-time) via API:
```bash
curl -X POST localhost:8000/auth/register -H 'content-type: application/json' \
  -d '{"email":"admin@example.com","password":"admin123"}'
```

Use the returned `access_token` as a Bearer token in the console.

## S3 (optional)
```bash
export STORE_TO_S3=true
export S3_BUCKET=your-bucket
export AWS_ACCESS_KEY_ID=...
export AWS_SECRET_ACCESS_KEY=...
export AWS_REGION=us-east-1
# optional for MinIO or custom endpoint
export S3_ENDPOINT_URL=http://localhost:9000
```

## DAG Orchestration
A simple LangGraph-style DAG lives in `src/orchestration/dag.py`.
Run the built-in meeting cycle:
```bash
curl -X POST localhost:8000/orchestration/dag/meeting_cycle \
 -H 'authorization: Bearer <TOKEN>' -H 'content-type: application/json' -d '{"topic":"MVP kickoff"}'
```

## Spend Dashboard
LLM calls log basic token counts and estimated cost to `usage_events`. View in console under “Spend”.
You can override per-token prices via env vars: `OPENAI_PRICE_IN`, `OPENAI_PRICE_OUT`, `ANTHROPIC_PRICE_IN`, `ANTHROPIC_PRICE_OUT`.


**Read next:** [docs/HOWTO.md](docs/HOWTO.md)
