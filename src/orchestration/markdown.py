def render_standup(m: dict) -> str:
    lines = [f"# Stand-up — {m.get('date','')}", "", "## Attendees"]
    for a in m.get('attendees', []): lines.append(f"- {a}")
    lines += ["", "## Yesterday"] + [f"- {x}" for x in m.get('yesterday', [])]
    lines += ["", "## Today"] + [f"- {x}" for x in m.get('today', [])]
    lines += ["", "## Blockers"] + [f"- {x}" for x in m.get('blockers', [])]
    lines += ["", "## Decisions"] + [f"- {x}" for x in m.get('decisions', [])]
    return "\n".join(lines)

def render_brainstorm(d: dict) -> str:
    lines = [f"# Brainstorm — {d.get('topic','')}", "", f"**Facilitator:** {d.get('owner','')}", "", "## Idea Map"]
    for idea in d.get('ideas', []): lines.append(f"- {idea}")
    lines += ["", "## Top-3 Concepts"]
    for i, c in enumerate(d.get('top3', []), start=1): lines.append(f"{i}. {c}")
    lines += ["", "## Decision Memo"]
    dec = d.get('decision', {})
    if dec: lines += [f"- Problem: {dec.get('problem','')}", f"- Option chosen: {dec.get('option','')}", f"- Why now: {dec.get('why','')}"]
    return "\n".join(lines)

def render_allhands(d: dict) -> str:
    lines = [f"# All-Hands — {d.get('week','')}", "", "## Metrics"]
    for k,v in (d.get('metrics') or {}).items(): lines.append(f"- {k}: {v}")
    lines += ["", "## Updates by Workstream"]
    for k,v in (d.get('updates') or {}).items(): lines.append(f"- {k}: {v}")
    lines += ["", "## Risks & Mitigations"]
    for r in d.get('risks', []): lines.append(f"- {r}")
    lines += ["", "## Lessons Learned"]
    for l in d.get('lessons', []): lines.append(f"- {l}")
    return "\n".join(lines)
