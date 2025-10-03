from typing import Any, Dict

from ..utils.store import save_json, save_markdown, ts
from .dag import DAG, Node
from .markdown import render_allhands, render_brainstorm, render_standup


def standup_flow(context: Dict[str, Any]) -> Dict[str, Any]:
    minutes = {
        "type": "standup",
        "date": context.get("date"),
        "attendees": context.get("attendees", []),
        "yesterday": context.get("yesterday", []),
        "today": context.get("today", []),
        "blockers": context.get("blockers", []),
        "decisions": context.get("decisions", []),
    }
    name = f"standup-{minutes['date'] or ts()}"
    md = render_standup(minutes)
    md_path = save_markdown("minutes", name, md)
    json_path = save_json("minutes", name, minutes)
    return {"markdown_path": md_path, "json_path": json_path, "markdown": md, "minutes": minutes}


def brainstorm_flow(context: Dict[str, Any]) -> Dict[str, Any]:
    doc = {
        "type": "brainstorm",
        "topic": context.get("topic", ""),
        "owner": context.get("owner", ""),
        "ideas": context.get("ideas", []),
        "top3": context.get("top3", []),
        "decision": context.get("decision", {}),
    }
    name = f"brainstorm-{ts()}"
    md = render_brainstorm(doc)
    md_path = save_markdown("minutes", name, md)
    json_path = save_json("minutes", name, doc)
    return {"markdown_path": md_path, "json_path": json_path, "markdown": md, "minutes": doc}


def allhands_flow(context: Dict[str, Any]) -> Dict[str, Any]:
    doc = {
        "type": "allhands",
        "week": context.get("week", ""),
        "metrics": context.get("metrics", {}),
        "updates": context.get("updates", {}),
        "risks": context.get("risks", []),
        "lessons": context.get("lessons", []),
    }
    name = f"allhands-{doc['week'] or ts()}"
    md = render_allhands(doc)
    md_path = save_markdown("minutes", name, md)
    json_path = save_json("minutes", name, doc)
    return {"markdown_path": md_path, "json_path": json_path, "markdown": md, "minutes": doc}


def meeting_cycle_dag(context: Dict[str, Any]) -> Dict[str, Any]:
    def n_brainstorm(ctx):
        return brainstorm_flow(ctx)

    def n_standup(ctx):
        return standup_flow(ctx)

    def n_allhands(ctx):
        return allhands_flow(ctx)

    dag = DAG(
        [
            Node(id="brainstorm", fn=n_brainstorm, depends_on=[]),
            Node(id="standup", fn=n_standup, depends_on=["brainstorm"]),
            Node(id="allhands", fn=n_allhands, depends_on=["standup"]),
        ]
    )
    return dag.run(context)
