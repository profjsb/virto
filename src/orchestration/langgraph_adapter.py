# Optional LangGraph adapter. Install: uv add langgraph langchain
from typing import Dict, Any, List

def run_langgraph_meeting_cycle(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        from langgraph.graph import StateGraph, START, END  # type: ignore
    except Exception as e:
        return {"engine": "langgraph", "error": "langgraph not installed", "result": {}}

    def brainstorm(state): return {"brainstorm": {"ideas": context.get("ideas", []), "top3": context.get("top3", [])}}
    def standup(state): return {"standup": {"today": context.get("today", []), "blockers": context.get("blockers", [])}}
    def allhands(state): return {"allhands": {"metrics": context.get("metrics", {})}}

    workflow = StateGraph(dict)
    workflow.add_node("brainstorm", brainstorm)
    workflow.add_node("standup", standup)
    workflow.add_node("allhands", allhands)
    workflow.add_edge(START, "brainstorm")
    workflow.add_edge("brainstorm", "standup")
    workflow.add_edge("standup", "allhands")
    workflow.add_edge("allhands", END)

    app = workflow.compile()
    res = app.invoke({})
    return {"engine": "langgraph", "result": res}
