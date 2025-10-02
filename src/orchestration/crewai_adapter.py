# Optional CrewAI adapter. Install: uv add crewai crewai-tools
from typing import Dict, Any

def run_crewai_brainstorm(idea: str) -> Dict[str, Any]:
    try:
        from crewai import Agent, Task, Crew  # type: ignore
    except Exception:
        return {"engine": "crewai", "error": "crewai not installed", "result": {}}
    planner = Agent(role="Planner", goal="Break down idea", backstory="Product thinker")
    builder = Agent(role="Builder", goal="Propose implementation steps", backstory="Engineer")
    t = Task(description=f"Plan next 5 steps for: {idea}", agent=planner)
    crew = Crew(agents=[planner, builder], tasks=[t])
    res = crew.kickoff()
    return {"engine": "crewai", "result": str(res)}
