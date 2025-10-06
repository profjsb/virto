import os

import httpx

NOTION_MCP_URL = os.environ.get("NOTION_MCP_URL", "https://mcp.notion.com/mcp")
NOTION_OAUTH_TOKEN = os.environ.get("NOTION_OAUTH_TOKEN")

USE_MOCK = os.environ.get("NOTION_MOCK", "false").lower() == "true"


def _mock_pages():
    return [
        {
            "id": "page-1",
            "title": "Engineering Meeting Notes",
            "url": "https://notion.so/page-1",
            "created_time": "2025-10-01T10:00:00Z",
            "last_edited_time": "2025-10-06T09:30:00Z",
        },
        {
            "id": "page-2",
            "title": "Product Roadmap Q4 2025",
            "url": "https://notion.so/page-2",
            "created_time": "2025-09-15T14:00:00Z",
            "last_edited_time": "2025-10-05T16:45:00Z",
        },
    ]


def _mock_search_results(query: str):
    return [
        {
            "id": "page-1",
            "title": f"Search result for: {query}",
            "url": "https://notion.so/page-1",
            "snippet": f"This page contains information about {query}...",
        }
    ]


def _headers():
    if not NOTION_OAUTH_TOKEN:
        raise RuntimeError("NOTION_OAUTH_TOKEN not set")
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {NOTION_OAUTH_TOKEN}",
        "Notion-Version": "2022-06-28",
    }


def mcp_request(method: str, params: dict = None):
    """
    Send MCP request to Notion MCP server.

    Args:
        method: MCP method name (e.g., "notion/search", "notion/create_page")
        params: Method parameters

    Returns:
        Response data from MCP server
    """
    if USE_MOCK or not NOTION_OAUTH_TOKEN:
        # Return mock data based on method
        if method == "notion/search":
            return _mock_search_results(params.get("query", ""))
        elif method == "notion/list_pages":
            return _mock_pages()
        elif method == "notion/create_page":
            return {
                "id": "new-page-123",
                "title": params.get("title", "New Page"),
                "url": "https://notion.so/new-page-123",
            }
        return {}

    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params or {},
    }

    with httpx.Client(timeout=60) as client:
        response = client.post(NOTION_MCP_URL, headers=_headers(), json=payload)
        response.raise_for_status()
        data = response.json()

        if "error" in data:
            raise RuntimeError(f"MCP Error: {data['error']}")

        return data.get("result", {})


def search_workspace(query: str, limit: int = 10):
    """
    Search across Notion workspace.

    Args:
        query: Search query string
        limit: Maximum number of results

    Returns:
        List of search results
    """
    return mcp_request("notion/search", {"query": query, "limit": limit})


def list_pages(limit: int = 100):
    """
    List pages in Notion workspace.

    Args:
        limit: Maximum number of pages to return

    Returns:
        List of page objects
    """
    if USE_MOCK or not NOTION_OAUTH_TOKEN:
        return _mock_pages()

    return mcp_request("notion/list_pages", {"limit": limit})


def get_page(page_id: str):
    """
    Get a specific page by ID.

    Args:
        page_id: Notion page ID

    Returns:
        Page object with full content
    """
    return mcp_request("notion/get_page", {"page_id": page_id})


def create_page(title: str, content: str, parent_id: str = None):
    """
    Create a new Notion page.

    Args:
        title: Page title
        content: Page content (markdown)
        parent_id: Parent page/database ID (optional)

    Returns:
        Created page object
    """
    params = {
        "title": title,
        "content": content,
    }
    if parent_id:
        params["parent_id"] = parent_id

    return mcp_request("notion/create_page", params)


def update_page(page_id: str, title: str = None, content: str = None):
    """
    Update an existing Notion page.

    Args:
        page_id: Page ID to update
        title: New title (optional)
        content: New content (optional)

    Returns:
        Updated page object
    """
    params = {"page_id": page_id}
    if title:
        params["title"] = title
    if content:
        params["content"] = content

    return mcp_request("notion/update_page", params)


def append_to_page(page_id: str, content: str):
    """
    Append content to an existing page.

    Args:
        page_id: Page ID
        content: Content to append (markdown)

    Returns:
        Updated page object
    """
    return mcp_request("notion/append_blocks", {"page_id": page_id, "content": content})


def create_database_entry(database_id: str, properties: dict):
    """
    Create entry in a Notion database.

    Args:
        database_id: Database ID
        properties: Entry properties as dict

    Returns:
        Created entry object
    """
    return mcp_request(
        "notion/create_database_entry",
        {
            "database_id": database_id,
            "properties": properties,
        },
    )
