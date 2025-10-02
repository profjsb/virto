# AutoGen-style orchestration. Uses pyautogen if installed; otherwise a simple fallback.
from typing import List, Dict, Any
from ..services.llm_provider import generate

def run_autogen_brainstorm(idea: str, participants: List[Dict[str, str]], provider: str = "openai", model: str = None) -> Dict[str, Any]:
    try:
        import autogen  # pyautogen
        # Minimal two-agent group chat with a moderator
        system_message = f"You are co-founders brainstorming how to execute the idea: '{idea}'. Produce key decisions and next steps."
        # Build agents
        agents = []
        for p in participants:
            role = autogen.AssistantAgent(name=p.get("name", "Agent"), system_message=f"You are {p.get('role','member')}. {system_message}")
            agents.append(role)
        # Moderator
        moderator = autogen.UserProxyAgent(name="Moderator", human_input_mode="NEVER")
        # Start chat
        chat_result = autogen.GroupChat(agents=agents + [moderator], messages=[{"content": system_message, "role":"system"}], max_round=4)
        manager = autogen.GroupChatManager(groupchat=chat_result)
        # Kick off with a prompt
        manager.initiate_chat(agents[0], message=f"Let's break down the idea and propose 3 next steps.")
        transcript = [m for m in chat_result.messages]
        summary_prompt = "Summarize the group chat into decisions, risks, and 5 concrete next steps."
        summary = generate(summary_prompt, provider=provider, model=model)
        return {"transcript": transcript, "summary": summary, "engine": "autogen"}
    except Exception:
        # Fallback: single-shot LLM that simulates multiple voices
        names = ", ".join([p.get("name","A") for p in participants])
        prompt = f"""Simulate a short co-founder discussion among {names} about the idea: "{idea}".
Return JSON with keys: decisions (list), risks (list), next_steps (list of 5)."""
        summary = generate(prompt, provider=provider, model=model)
        return {"transcript": [{"role":"system","content":"fallback"}], "summary": summary, "engine": "fallback"}
