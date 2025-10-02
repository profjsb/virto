import os, httpx, json

LINEAR_API_KEY = os.environ.get("LINEAR_API_KEY")

USE_MOCK = os.environ.get("LINEAR_MOCK", "false").lower() == "true"

def _mock():
    teams = [{"id":"T1","key":"APP","name":"App Team"}]
    cycles = [{"id":"C1","number":42,"startsAt":"2025-09-22","endsAt":"2025-10-06","name":"Cycle 42"}]
    issues = [
        {"id":"I1","identifier":"APP-101","title":"Implement walking skeleton","state":{"name":"In Progress"},"assignee":{"name":"CTO"},"url":"https://example.local/APP-101"},
        {"id":"I2","identifier":"APP-102","title":"User interviews — recruit 10","state":{"name":"Todo"},"assignee":{"name":"CEO"},"url":"https://example.local/APP-102"},
        {"id":"I3","identifier":"APP-103","title":"Wireframes v1","state":{"name":"Todo"},"assignee":{"name":"CXO"},"url":"https://example.local/APP-103"},
    ]
    return teams, cycles, issues


API_URL = "https://api.linear.app/graphql"

def _headers():
    if not LINEAR_API_KEY:
        raise RuntimeError("LINEAR_API_KEY not set")
    return {"Content-Type":"application/json", "Authorization": f"{LINEAR_API_KEY}"}

def gql(query: str, variables: dict=None):
    with httpx.Client(timeout=60) as c:
        r = c.post(API_URL, headers=_headers(), json={"query": query, "variables": variables or {}})
        r.raise_for_status()
        data = r.json()
        if "errors" in data:
            raise RuntimeError(str(data["errors"]))
        return data["data"]

def list_teams():
    if USE_MOCK or not LINEAR_API_KEY:
        return _mock()[0]
    q = """query { teams(first:50){ nodes { id key name } } }"""
    return gql(q)["teams"]["nodes"]

def list_cycles(team_id: str):
    if USE_MOCK or not LINEAR_API_KEY:
        return _mock()[1]
    q = """query($teamId: String!){ team(id:$teamId){ cycles(first:20){ nodes{ id number startsAt endsAt name } } } }"""
    return gql(q, {"teamId": team_id})["team"]["cycles"]["nodes"]

def list_issues_in_cycle(team_id: str, cycle_id: str):
    if USE_MOCK or not LINEAR_API_KEY:
        return _mock()[2]
    q = """query($teamId:String!, $cycleId:String!){
      issues(filter:{ team:{ id:{ eq:$teamId } }, cycle:{ id:{ eq:$cycleId } } }, first:200){
        nodes{ id identifier title state{ name } assignee{ name } url }
      }
    }"""
    return gql(q, {"teamId": team_id, "cycleId": cycle_id})["issues"]["nodes"]

def create_issue(team_id: str, title: str, description: str):
    if USE_MOCK or not LINEAR_API_KEY:
        return {"success": True, "issue": {"id":"I4","identifier":"APP-104","title":title, "url":"https://example.local/APP-104"}}
    q = """mutation($teamId:String!, $title:String!, $description:String){
      issueCreate(input:{ teamId:$teamId, title:$title, description:$description }){ success issue{ id identifier title url } }
    }"""
    return gql(q, {"teamId": team_id, "title": title, "description": description})
