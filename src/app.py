import asyncio
import datetime
import json
import os
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy import func

from . import db
from .db.models import Approval, Artifact, Role, Run, User, UserRole
from .orchestration.crewai_adapter import run_crewai_brainstorm
from .orchestration.flows import allhands_flow, brainstorm_flow, meeting_cycle_dag, standup_flow
from .orchestration.langgraph_adapter import run_langgraph_meeting_cycle
from .services.auth import hash_password, make_token, verify_password
from .services.auth_rbac import require_role, roles_for_user
from .services.event_stream import hub
from .services.linear_client import create_issue, list_cycles, list_issues_in_cycle, list_teams
from .services.llm_provider import generate
from .services.notion_client import (
    append_to_page,
    create_page,
    get_page,
    list_pages,
    search_workspace,
    update_page,
)
from .services.policy import load_policies, spend_threshold
from .utils.s3 import presign as s3_presign

app = FastAPI(title="Virtual AI Org API", version="0.5.0")

# CORS for the React console
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static serving of local data artifacts
DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
if os.path.isdir(DATA_DIR):
    app.mount("/data", StaticFiles(directory=DATA_DIR), name="data")


# ---------------- DTOs ----------------
class RegisterInput(BaseModel):
    email: str
    password: str
    admin_secret: Optional[str] = None


class LoginInput(BaseModel):
    email: str
    password: str


class AssignRoleInput(BaseModel):
    user_id: int
    role: str  # admin, approver, engineer, growth, viewer


class HiringRequest(BaseModel):
    idea: str
    budget_usd: float
    deadline_days: int
    goal: str
    provider: Optional[str] = "openai"
    model: Optional[str] = None


class ApprovalRequest(BaseModel):
    description: str
    amount_usd: float
    justification: str


class StandupInput(BaseModel):
    date: Optional[str] = None
    attendees: List[str] = []
    yesterday: List[str] = []
    today: List[str] = []
    blockers: List[str] = []
    decisions: List[str] = []


class BrainstormInput(BaseModel):
    topic: str
    owner: str
    ideas: List[str] = []
    top3: List[str] = []
    decision: Dict[str, Any] = {}


class AllHandsInput(BaseModel):
    week: str
    metrics: Dict[str, Any] = {}
    updates: Dict[str, Any] = {}
    risks: List[str] = []
    lessons: List[str] = []


class AutogenInput(BaseModel):
    idea: str
    participants: List[Dict[str, str]] = []
    provider: Optional[str] = "openai"
    model: Optional[str] = None


class LinearIssueCreate(BaseModel):
    team_id: str
    title: str
    description: Optional[str] = None


class NotionSearchInput(BaseModel):
    query: str
    limit: Optional[int] = 10


class NotionPageCreate(BaseModel):
    title: str
    content: str
    parent_id: Optional[str] = None


class NotionPageUpdate(BaseModel):
    page_id: str
    title: Optional[str] = None
    content: Optional[str] = None


class NotionAppendInput(BaseModel):
    page_id: str
    content: str


@app.get("/health")
def health():
    return {"status": "ok"}


# -------- Auth endpoints + RBAC --------
@app.post("/auth/register")
def register(inp: RegisterInput):
    allow_signup = os.environ.get("ALLOW_SIGNUP", "false").lower() == "true"
    admin_secret = os.environ.get("ADMIN_SIGNUP_SECRET")
    with db.SessionLocal() as session:
        count = session.query(func.count(User.id)).scalar()
        if not allow_signup and count > 0 and inp.admin_secret != admin_secret:
            raise HTTPException(403, "signups disabled")
        if session.query(User).filter(User.email == inp.email).first():
            raise HTTPException(409, "email already registered")
        u = User(email=inp.email, password_hash=hash_password(inp.password), is_admin=False)
        session.add(u)
        session.commit()
        session.refresh(u)
        # first user becomes admin
        if count == 0:
            # ensure roles table has base roles
            ensure_roles()
            assign_role(u.id, "admin", session)
        token = make_token(sub=str(u.id), is_admin=("admin" in roles_for_user(u.id)))
        return {"access_token": token}


@app.post("/auth/login")
def login(inp: LoginInput):
    with db.SessionLocal() as session:
        u = session.query(User).filter(User.email == inp.email).first()
        if not u or not verify_password(inp.password, u.password_hash):
            raise HTTPException(401, "invalid credentials")
        token = make_token(sub=str(u.id), is_admin=("admin" in roles_for_user(u.id)))
        return {"access_token": token}


def ensure_roles():
    base = ["admin", "approver", "engineer", "growth", "viewer"]
    with db.SessionLocal() as session:
        exists = {r.name for r in session.query(Role).all()}
        for name in base:
            if name not in exists:
                session.add(Role(name=name))
        session.commit()


def assign_role(user_id: int, role_name: str, db):
    role = db.query(Role).filter(Role.name == role_name).first()
    if not role:
        role = Role(name=role_name)
        db.add(role)
        db.commit()
        db.refresh(role)
    db.add(UserRole(user_id=user_id, role_id=role.id))
    db.commit()


@app.post("/auth/assign-role")
def api_assign_role(inp: AssignRoleInput, authorization: Optional[str] = Header(None)):
    require_role(authorization, ["admin"])
    with db.SessionLocal() as session:
        if not session.get(User, inp.user_id):
            raise HTTPException(404, "user not found")
        assign_role(inp.user_id, inp.role, session)
    return {"ok": True}


# -------- Hiring / LLM --------
@app.post("/hiring/plan")
def hiring_plan(req: HiringRequest, authorization: Optional[str] = Header(None)):
    require_role(authorization, ["engineer", "growth", "approver", "admin", "viewer"])
    prompt = f"""Given IDEA: {req.idea}, budget: ${req.budget_usd}, deadline: {req.deadline_days} days, goal: {req.goal},
propose a minimal founding team (≤5 roles) and the first three workstreams. Return JSON with 'roles' and 'workstreams'."""
    llm_json = generate(
        prompt, provider=req.provider or "openai", model=req.model, run_id=None, actor="hiring"
    )
    roles = [
        {
            "role_id": "cto",
            "persona_ref": "cto.core.v1",
            "mission": "Choose stack & ship walking skeleton",
            "deliverables": ["ADR 002 (stack)", "hello-world deploy", "CI pipeline"],
            "tools": ["repo", "ci", "cloud"],
            "metrics": {"lead_time_days": 7},
        },
        {
            "role_id": "cxo",
            "persona_ref": "cxo.design.v1",
            "mission": "Wireframes and prototype",
            "deliverables": ["wireframes v1", "interactive prototype"],
            "tools": ["figma_mcp"],
            "metrics": {"usability_score": ">=4/5"},
        },
        {
            "role_id": "ceo",
            "persona_ref": "ceo.prod.v1",
            "mission": "Discovery and launch plan",
            "deliverables": ["10 problem interviews", "launch plan v1"],
            "tools": ["browse", "ticketing_mcp"],
            "metrics": {"interviews": 10},
        },
    ]
    workstreams = [
        {
            "name": "Walking Skeleton",
            "owner": "cto",
            "milestone": "prod hello-world",
            "eta_days": 7,
        },
        {
            "name": "Problem Interviews",
            "owner": "ceo",
            "milestone": "10 interviews",
            "eta_days": 10,
        },
        {"name": "Wireframes v1", "owner": "cxo", "milestone": "Figma prototype", "eta_days": 10},
    ]
    return {
        "roles": roles,
        "workstreams": workstreams,
        "llm_output": llm_json,
        "inputs": req.model_dump(),
    }


# -------- Approvals (approver/admin) --------
@app.post("/approvals/submit")
def approvals_submit(req: ApprovalRequest, authorization: Optional[str] = Header(None)):
    require_role(authorization, ["engineer", "growth", "approver", "admin"])
    policy = load_policies()
    threshold = spend_threshold(policy)
    status = "auto_approved" if req.amount_usd <= threshold else "pending"
    with db.SessionLocal() as session:
        ap = Approval(
            description=req.description,
            amount_usd=req.amount_usd,
            justification=req.justification,
            status=status,
            threshold=threshold,
        )
        session.add(ap)
        session.commit()
        session.refresh(ap)
        return {"id": ap.id, "status": ap.status, "threshold": ap.threshold}


@app.patch("/approvals/{approval_id}/decision")
def approvals_decide(approval_id: int, approved: bool, authorization: Optional[str] = Header(None)):
    require_role(authorization, ["approver", "admin"])
    with db.SessionLocal() as session:
        ap = session.get(Approval, approval_id)
        if not ap:
            raise HTTPException(404, "not found")
        ap.status = "approved" if approved else "rejected"
        ap.decided_at = datetime.datetime.utcnow()
        session.add(ap)
        session.commit()
        session.refresh(ap)
        return {"id": ap.id, "status": ap.status}


@app.get("/ops/approvals")
def list_approvals(authorization: Optional[str] = Header(None)):
    require_role(authorization, ["viewer", "engineer", "growth", "approver", "admin"])
    with db.SessionLocal() as session:
        rows = session.query(Approval).order_by(Approval.id.desc()).limit(200).all()
        return [
            {
                "id": r.id,
                "description": r.description,
                "amount_usd": r.amount_usd,
                "status": r.status,
                "created_at": str(r.created_at),
            }
            for r in rows
        ]


# -------- Minutes & DAG --------
@app.post("/meetings/standup")
def meeting_standup(m: StandupInput, authorization: Optional[str] = Header(None)):
    require_role(authorization, ["engineer", "viewer", "admin"])
    result = standup_flow(m.model_dump())
    with db.SessionLocal() as session:
        art = Artifact(
            kind="minutes",
            name="standup",
            path=result["markdown_path"],
            meta=json.dumps(m.model_dump()),
        )
        session.add(art)
        session.commit()
    return result


@app.post("/meetings/brainstorm")
def meeting_brainstorm(m: BrainstormInput, authorization: Optional[str] = Header(None)):
    require_role(authorization, ["engineer", "growth", "viewer", "admin"])
    result = brainstorm_flow(m.model_dump())
    with db.SessionLocal() as session:
        art = Artifact(
            kind="minutes",
            name=f"brainstorm:{m.topic}",
            path=result["markdown_path"],
            meta=json.dumps(m.model_dump()),
        )
        session.add(art)
        session.commit()
    return result


@app.post("/meetings/allhands")
def meeting_allhands(m: AllHandsInput, authorization: Optional[str] = Header(None)):
    require_role(authorization, ["viewer", "admin"])
    result = allhands_flow(m.model_dump())
    with db.SessionLocal() as session:
        art = Artifact(
            kind="minutes",
            name=f"allhands:{m.week}",
            path=result["markdown_path"],
            meta=json.dumps(m.model_dump()),
        )
        session.add(art)
        session.commit()
    return result


@app.post("/orchestration/dag/meeting_cycle")
def run_meeting_cycle(context: Dict[str, Any], authorization: Optional[str] = Header(None)):
    require_role(authorization, ["engineer", "admin"])
    return meeting_cycle_dag(context)


@app.post("/orchestration/langgraph/meeting_cycle")
def run_langgraph(context: Dict[str, Any], authorization: Optional[str] = Header(None)):
    require_role(authorization, ["engineer", "admin"])
    return run_langgraph_meeting_cycle(context)


@app.post("/orchestration/crewai/brainstorm")
def run_crewai(idea: Dict[str, str], authorization: Optional[str] = Header(None)):
    require_role(authorization, ["engineer", "admin"])
    return run_crewai_brainstorm(idea.get("idea", ""))


# -------- SSE run streams --------
@app.post("/runs/start_demo")
async def runs_start_demo(authorization: Optional[str] = Header(None)):
    require_role(authorization, ["engineer", "admin"])
    with db.SessionLocal() as session:
        run = Run(run_type="demo", status="running", summary="Demo run")
        session.add(run)
        session.commit()
        session.refresh(run)
        rid = run.id

    # fire-and-forget background simulation
    async def simulate():
        await hub.publish(rid, "event:log\ndata: Starting demo run\n\n")
        await asyncio.sleep(0.5)
        await hub.publish(rid, "event:log\ndata: Planning...\n\n")
        await asyncio.sleep(0.5)
        await hub.publish(rid, "event:log\ndata: Executing step 1\n\n")
        await asyncio.sleep(0.5)
        await hub.publish(rid, "event:done\ndata: Completed\n\n")
        with db.SessionLocal() as session:
            r = session.get(Run, rid)
            r.status = "done"
            session.add(r)
            session.commit()

    asyncio.create_task(simulate())
    return {"run_id": rid}


@app.get("/streams/runs/{run_id}")
async def stream_run(run_id: int, authorization: Optional[str] = Header(None)):
    require_role(authorization, ["viewer", "engineer", "admin"])
    q = hub.subscribe(run_id)

    async def gen():
        try:
            while True:
                msg = await q.get()
                yield msg
        finally:
            hub.unsubscribe(run_id, q)

    return StreamingResponse(gen(), media_type="text/event-stream")


# -------- Minutes & artifacts --------
@app.get("/ops/minutes")
def ops_minutes(authorization: Optional[str] = Header(None)):
    require_role(authorization, ["viewer", "engineer", "growth", "approver", "admin"])
    with db.SessionLocal() as session:
        rows = (
            session.query(Artifact)
            .filter(Artifact.kind == "minutes")
            .order_by(Artifact.id.desc())
            .limit(200)
            .all()
        )
        out = []
        for r in rows:
            link = None
            if (r.storage == "s3") and r.s3_key and r.s3_bucket:
                link = s3_presign(r.s3_key)
            else:
                if "/data/" in (r.path or ""):
                    local = r.path.split("/data/")[-1]
                    link = f"/data/{local}"
                else:
                    link = r.path
            out.append(
                {
                    "id": r.id,
                    "name": r.name,
                    "path": r.path,
                    "download": link,
                    "created_at": str(r.created_at),
                }
            )
        return out


# -------- Linear endpoints --------
@app.get("/linear/teams")
def linear_teams(authorization: Optional[str] = Header(None)):
    require_role(authorization, ["viewer", "engineer", "growth", "admin"])
    return list_teams()


@app.get("/linear/cycles")
def linear_cycles(team_id: str, authorization: Optional[str] = Header(None)):
    require_role(authorization, ["viewer", "engineer", "growth", "admin"])
    return list_cycles(team_id)


@app.get("/linear/issues")
def linear_issues(team_id: str, cycle_id: str, authorization: Optional[str] = Header(None)):
    require_role(authorization, ["viewer", "engineer", "growth", "admin"])
    return list_issues_in_cycle(team_id, cycle_id)


@app.post("/linear/issues")
def linear_create_issue(inp: LinearIssueCreate, authorization: Optional[str] = Header(None)):
    require_role(authorization, ["engineer", "growth", "admin"])
    return create_issue(inp.team_id, inp.title, inp.description)


# -------- Notion endpoints --------
@app.get("/notion/pages")
def notion_pages(limit: int = 100, authorization: Optional[str] = Header(None)):
    """List pages in Notion workspace."""
    require_role(authorization, ["viewer", "engineer", "growth", "admin"])
    return list_pages(limit)


@app.post("/notion/search")
def notion_search(inp: NotionSearchInput, authorization: Optional[str] = Header(None)):
    """Search across Notion workspace."""
    require_role(authorization, ["viewer", "engineer", "growth", "admin"])
    return search_workspace(inp.query, inp.limit)


@app.get("/notion/pages/{page_id}")
def notion_get_page(page_id: str, authorization: Optional[str] = Header(None)):
    """Get a specific Notion page by ID."""
    require_role(authorization, ["viewer", "engineer", "growth", "admin"])
    return get_page(page_id)


@app.post("/notion/pages")
def notion_create_page(inp: NotionPageCreate, authorization: Optional[str] = Header(None)):
    """Create a new Notion page."""
    require_role(authorization, ["engineer", "growth", "admin"])
    page = create_page(inp.title, inp.content, inp.parent_id)

    # Store as artifact for tracking
    with db.SessionLocal() as session:
        art = Artifact(
            kind="notion_page",
            name=inp.title,
            path=page.get("url"),
            meta=json.dumps({"page_id": page.get("id"), "parent_id": inp.parent_id}),
        )
        session.add(art)
        session.commit()

    return page


@app.patch("/notion/pages/{page_id}")
def notion_update_page(
    page_id: str, inp: NotionPageUpdate, authorization: Optional[str] = Header(None)
):
    """Update an existing Notion page."""
    require_role(authorization, ["engineer", "growth", "admin"])
    return update_page(page_id, inp.title, inp.content)


@app.post("/notion/pages/{page_id}/append")
def notion_append_page(
    page_id: str, inp: NotionAppendInput, authorization: Optional[str] = Header(None)
):
    """Append content to an existing Notion page."""
    require_role(authorization, ["engineer", "growth", "admin"])
    return append_to_page(page_id, inp.content)
