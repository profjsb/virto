# CLAUDE.md — AI Assistant Guide

This document provides context and guidance for AI assistants (like Claude) working on the Virtual AI Organization codebase.

## Project Overview

**Virtual AI Organization** is a production-ready framework for building and operating virtual organizations staffed by AI agents. It's a FastAPI-based platform with:

- Multi-agent orchestration (DAG, LangGraph, CrewAI, AutoGen)
- JWT auth + RBAC (5 roles: admin, approver, engineer, growth, viewer)
- PostgreSQL + Alembic migrations
- React/TypeScript ops console
- Real-time event streaming (SSE)
- LLM provider abstraction (OpenAI, Anthropic)
- Usage/cost tracking
- Policy-based approval workflows
- Linear integration for project management

## Architecture Quick Reference

```
Backend (Python/FastAPI):
  src/app.py              → Main API routes (~335 lines)
  src/db/models.py        → SQLAlchemy models (User, Approval, Artifact, Run, etc.)
  src/orchestration/      → Workflow engines
    ├── dag.py            → Custom DAG implementation
    ├── flows.py          → Meeting workflows (standup, brainstorm, all-hands)
    ├── langgraph_adapter.py
    ├── crewai_adapter.py
    └── autogen_loop.py
  src/services/           → Business logic layer
    ├── auth.py           → JWT + password hashing
    ├── auth_rbac.py      → Role checking
    ├── llm_provider.py   → Multi-provider LLM interface
    ├── usage_logger.py   → Token/cost tracking
    ├── event_stream.py   → SSE pub/sub hub
    ├── linear_client.py  → Linear GraphQL client
    └── policy.py         → Policy loading/evaluation
  src/utils/              → Utilities (S3, storage, I/O)

Frontend (React/TypeScript):
  console/                → Vite-based ops dashboard

Infrastructure:
  alembic/                → Database migrations
  governance/             → Machine-readable policies
  personas/               → AI agent definitions (JSON)
  schemas/                → JSON schemas
  meetings/templates/     → Meeting markdown templates
```

## Key Patterns & Conventions

### 1. Authentication & Authorization

All protected endpoints use:

```python
from src.services.auth_rbac import require_role

def endpoint(authorization: Optional[str] = Header(None)):
    require_role(authorization, ["engineer", "admin"])
    # ... endpoint logic
```

Roles: `admin`, `approver`, `engineer`, `growth`, `viewer`

### 2. Database Sessions

Use context manager pattern:

```python
from src.db import SessionLocal

with SessionLocal() as db:
    user = db.query(User).filter(User.email == email).first()
    # ... work with db
    db.commit()
```

### 3. LLM Calls

Unified interface with automatic usage tracking:

```python
from src.services.llm_provider import generate

result = generate(
    prompt="Your prompt here",
    provider="openai",  # or "anthropic"
    model=None,         # uses default if None
    run_id=None,        # optional: link to Run record
    actor="system"      # who/what made this call
)
```

This automatically logs tokens and costs to `usage_events` table.

### 4. Event Streaming

Publish events to connected clients:

```python
from src.services.event_stream import hub

await hub.publish(run_id, "event:log\ndata: Status update\n\n")
```

Clients subscribe via `GET /streams/runs/{run_id}` (SSE endpoint).

### 5. Artifact Storage

Store meeting minutes and outputs:

```python
from src.db.models import Artifact

art = Artifact(
    kind="minutes",
    name=f"standup:{date}",
    path=local_path,  # or None if S3
    storage="local",  # or "s3"
    s3_bucket=bucket, # if S3
    s3_key=key,       # if S3
    meta=json.dumps(metadata)
)
db.add(art)
db.commit()
```

## Database Schema (Key Tables)

```sql
users              → id, email, password_hash, is_admin, created_at
roles              → id, name (admin, approver, etc.)
user_roles         → user_id, role_id (many-to-many)
approvals          → id, description, amount_usd, status, threshold, created_at, decided_at
artifacts          → id, kind, name, path, storage, s3_bucket, s3_key, meta, created_at
runs               → id, run_type, status, summary, created_at, completed_at
run_logs           → id, run_id, timestamp, level, message
usage_events       → id, run_id, actor, provider, model, prompt_tokens, completion_tokens, cost_usd
```

## Common Tasks

### Add New API Endpoint

1. Add route to `src/app.py`
2. Use `require_role()` for auth
3. Use `SessionLocal()` context manager for DB
4. Return Pydantic models or dicts
5. Document in OpenAPI (automatic via FastAPI)

### Add Database Migration

```bash
# After modifying src/db/models.py:
uv run alembic revision --autogenerate -m "description"
uv run alembic upgrade head
```

### Add New LLM Provider

Edit `src/services/llm_provider.py`:

```python
elif provider == "new_provider":
    # Add API call logic
    # Return response text
    # Log usage via log_usage()
```

### Add New Orchestration Engine

1. Create adapter in `src/orchestration/`
2. Implement workflow function
3. Add endpoint in `src/app.py`
4. Link to Run records for observability

### Add New Meeting Template

1. Create template in `meetings/templates/`
2. Add flow function in `src/orchestration/flows.py`
3. Add endpoint in `src/app.py` (or extend existing)
4. Store result as Artifact

## Package Management

This project uses **uv** for fast, modern Python package management.

```bash
# Install dependencies
uv sync

# Add new dependency
uv add package-name

# Add dev dependency
uv add --dev package-name

# Run commands in the virtual environment
uv run <command>
```

## Testing

```bash
# Run tests
uv run pytest tests/

# Manual API testing
uv run uvicorn src.app:app --reload
# Visit http://localhost:8000/docs

# Test with curl
curl -X POST localhost:8000/auth/register \
  -H 'content-type: application/json' \
  -d '{"email":"test@example.com","password":"test123"}'
```

## Environment Setup

Required for development:

```bash
export DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/virtual_ai_org
export JWT_SECRET='dev-secret-change-in-production'
export ALLOW_SIGNUP=true
```

Optional for full functionality:

```bash
export OPENAI_API_KEY=sk-...
export ANTHROPIC_API_KEY=sk-ant-...
export LINEAR_API_KEY=lin_api_...
export STORE_TO_S3=true
export S3_BUCKET=my-bucket
export REDIS_URL=redis://localhost:6379
```

## Code Style & Conventions

- **Python**: Follow PEP 8, use type hints where helpful
- **Imports**: Group by stdlib, third-party, local (separated by blank lines)
- **Error handling**: Raise `HTTPException(status_code, detail)` for API errors
- **Logging**: Use `print()` for now (TODO: add proper logging)
- **JSON responses**: Return dicts or Pydantic models (FastAPI handles serialization)
- **Database**: Always use context manager, commit explicitly
- **Security**: Never log secrets, validate all user input

## Key Files to Understand

| File | Purpose | Lines |
|------|---------|-------|
| `src/app.py` | All API routes and endpoints | ~335 |
| `src/db/models.py` | Database schema definitions | ~100 |
| `src/services/llm_provider.py` | LLM abstraction + usage tracking | ~80 |
| `src/services/auth_rbac.py` | Role-based access control | ~50 |
| `src/orchestration/dag.py` | Custom workflow engine | ~150 |
| `src/orchestration/flows.py` | Meeting implementations | ~120 |
| `alembic/versions/*` | Database migrations | Varies |

## Common Pitfall Avoidance

1. **Don't forget auth**: All endpoints need `require_role()` except `/health`, `/auth/*`
2. **Commit database changes**: SQLAlchemy doesn't auto-commit
3. **Use context managers**: Always `with SessionLocal() as db:`
4. **Link to Run records**: Pass `run_id` to LLM calls for cost tracking
5. **Validate JSON schemas**: Use schemas in `schemas/` for persona/hiring plan validation
6. **Check S3 env vars**: `STORE_TO_S3` must be true AND bucket configured
7. **Test with real DB**: SQLite won't work (uses PostgreSQL-specific features)

## Extension Points

The codebase is designed to be extended in these areas:

1. **New orchestrators**: Add adapters in `src/orchestration/`
2. **New integrations**: Add clients in `src/services/`
3. **New workflows**: Extend `src/orchestration/flows.py`
4. **New personas**: Add JSON files to `personas/`
5. **New policies**: Edit `governance/policies.yaml`
6. **New storage backends**: Extend `src/utils/store.py`
7. **New auth providers**: Extend `src/services/auth.py`

## Debugging Tips

```bash
# Check database
psql $DATABASE_URL
\dt  # list tables
\d users  # describe users table

# Check migrations status
uv run alembic current
uv run alembic history

# Test LLM provider
uv run python -c "from src.services.llm_provider import generate; print(generate('Hello', 'openai'))"

# Check Redis connection
redis-cli ping

# View API logs
# (stdout/stderr from uvicorn)
```

## Performance Considerations

- Database queries are NOT optimized (no indexes beyond auto-generated)
- LLM calls are synchronous (blocks request thread)
- No caching layer (every request hits DB/LLM)
- SSE holds connections open (consider connection limits)
- S3 operations are synchronous
- No rate limiting implemented

For production use, consider:
- Add database indexes
- Implement async LLM calls with background tasks
- Add Redis caching layer
- Use connection pooling
- Add rate limiting middleware
- Implement request queuing for long-running tasks

## Security Notes

- JWT secrets must be strong in production (`JWT_SECRET`)
- First user becomes admin automatically
- `ALLOW_SIGNUP=true` allows unrestricted registration (disable in prod)
- No rate limiting on auth endpoints (vulnerable to brute force)
- S3 presigned URLs expire based on boto3 defaults
- CORS is wide open (`allow_origins=["*"]`) — restrict in production
- No CSRF protection (stateless JWT auth)
- Passwords hashed with bcrypt (good)

## Governance System

The governance system is unique to this project:

- **Constitution** (`governance/constitution.md`): Human-readable charter
- **Policies** (`governance/policies.yaml`): Machine-readable rules
- **Personas** (`personas/*.json`): AI agent role definitions
- **Schemas** (`schemas/*.schema.json`): Validation for personas and hiring plans

These are meant to be AI-readable and enforceable programmatically.

### Example Policy Usage

```python
from src.services.policy import load_policies, spend_threshold

policy = load_policies()  # Loads governance/policies.yaml
threshold = spend_threshold(policy)  # Extracts spending.approval_threshold_usd

# Auto-approve if under threshold
status = "auto_approved" if amount <= threshold else "pending"
```

## AI Agent Integration

This system is designed to BE OPERATED by AI agents, not just to operate them. Key design choices:

1. **Structured outputs**: All workflows produce markdown with YAML frontmatter
2. **JSON schemas**: Validate AI-generated content (personas, hiring plans)
3. **Event streaming**: Real-time feedback for agentic control loops
4. **Role-based access**: Agents get different permissions (engineer vs viewer)
5. **Usage tracking**: Monitor and limit AI spending per run/actor
6. **Linear integration**: Agents can create issues, track cycles

An AI agent could:
- Register as a user
- Get assigned the `engineer` role
- Call `/hiring/plan` to generate a team
- Call `/meetings/standup` daily
- Create Linear issues via `/linear/issues`
- Monitor costs via usage_events table
- Submit approvals via `/approvals/submit`

## Future Directions

From the roadmap (README.md):

- Vector database integration for semantic search over artifacts
- OpenTelemetry for distributed tracing
- Multi-tenant support (organizations, teams)
- Webhook system for external integrations
- Advanced workflow editor UI
- Persona marketplace (share agent definitions)
- Budget forecasting and alerts

## Questions to Ask Humans

If you encounter:

1. **Missing env vars**: Ask which LLM provider they want to use
2. **Database errors**: Ask if they ran `uv run alembic upgrade head`
3. **Auth errors**: Ask if they set `JWT_SECRET`
4. **S3 errors**: Ask if they want local or S3 storage
5. **Linear errors**: Ask if they have a Linear API key
6. **Unclear requirements**: Ask for examples or user stories

## Resources

- FastAPI docs: https://fastapi.tiangolo.com/
- SQLAlchemy docs: https://docs.sqlalchemy.org/
- Alembic docs: https://alembic.sqlalchemy.org/
- Linear API: https://developers.linear.app/docs/graphql/working-with-the-graphql-api
- LangGraph: https://langchain-ai.github.io/langgraph/
- CrewAI: https://docs.crewai.com/
- AutoGen: https://microsoft.github.io/autogen/

---

**Last Updated**: 2025-10-02
**Target Audience**: AI assistants (Claude, GPT-4, etc.) working on this codebase
**Maintained By**: Project contributors
