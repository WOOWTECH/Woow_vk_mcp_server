"""Registry of all 37 vibe-kanban-mcp tools organized into 4 categories.

Each tool entry contains:
- name: The MCP tool function name
- description: Human-readable description
- category: Grouping category for UI display
- enabled_by_default: Whether the tool is enabled when first deployed
- dangerous: Whether the tool performs destructive operations
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel


class ToolCategory(str, Enum):
    """Categories for organizing VK MCP tools."""

    EXECUTION = "A - Execution"
    REPO = "B - Repo"
    ISSUE_KANBAN = "C - Issue / Kanban"
    CONTEXT = "D - Context"


class ToolDefinition(BaseModel):
    """Schema for a single MCP tool definition."""

    name: str
    description: str
    category: ToolCategory
    enabled_by_default: bool = True
    dangerous: bool = False


class ToolState(BaseModel):
    """Runtime state of a tool (definition + current enabled status)."""

    name: str
    description: str
    category: ToolCategory
    enabled_by_default: bool
    dangerous: bool
    enabled: bool


class ToolUpdateRequest(BaseModel):
    """Request body for updating tool enabled states."""

    tools: Any  # dict[str, bool] or list[dict] from frontend


class ToolUpdateResponse(BaseModel):
    """Response after updating tool states."""

    updated: int
    tools: list[ToolState]


# ---------------------------------------------------------------------------
# Complete registry of all 37 vibe-kanban-mcp tools (--mode global)
# ---------------------------------------------------------------------------

TOOL_REGISTRY: list[ToolDefinition] = [
    # ── A - Execution (10) ─────────────────────────────────────────────
    ToolDefinition(
        name="start_workspace",
        description="Create a new workspace and start the first session with an executor",
        category=ToolCategory.EXECUTION,
        dangerous=True,
    ),
    ToolDefinition(
        name="create_session",
        description="Create a new session in a workspace",
        category=ToolCategory.EXECUTION,
    ),
    ToolDefinition(
        name="run_session_prompt",
        description="Run a coding agent turn in an existing session (async, returns immediately)",
        category=ToolCategory.EXECUTION,
    ),
    ToolDefinition(
        name="get_execution",
        description="Get status and final message for an execution",
        category=ToolCategory.EXECUTION,
    ),
    ToolDefinition(
        name="list_sessions",
        description="List sessions for a workspace",
        category=ToolCategory.EXECUTION,
    ),
    ToolDefinition(
        name="update_session",
        description="Update a session's display name",
        category=ToolCategory.EXECUTION,
    ),
    ToolDefinition(
        name="list_workspaces",
        description="List local workspaces with filters and pagination",
        category=ToolCategory.EXECUTION,
    ),
    ToolDefinition(
        name="update_workspace",
        description="Update workspace properties (archived, pinned, name)",
        category=ToolCategory.EXECUTION,
    ),
    ToolDefinition(
        name="delete_workspace",
        description="Delete a local workspace and optionally its branches",
        category=ToolCategory.EXECUTION,
        dangerous=True,
    ),
    ToolDefinition(
        name="link_workspace_issue",
        description="Link an existing workspace to a remote issue",
        category=ToolCategory.EXECUTION,
    ),
    # ── B - Repo (5) ──────────────────────────────────────────────────
    ToolDefinition(
        name="list_repos",
        description="List all repositories",
        category=ToolCategory.REPO,
    ),
    ToolDefinition(
        name="get_repo",
        description="Get repository details including setup/cleanup/dev server scripts",
        category=ToolCategory.REPO,
    ),
    ToolDefinition(
        name="update_setup_script",
        description="Update the setup script that runs on workspace initialization",
        category=ToolCategory.REPO,
    ),
    ToolDefinition(
        name="update_cleanup_script",
        description="Update the cleanup script that runs on workspace teardown",
        category=ToolCategory.REPO,
    ),
    ToolDefinition(
        name="update_dev_server_script",
        description="Update the dev server startup script",
        category=ToolCategory.REPO,
    ),
    # ── C - Issue / Kanban (18) ────────────────────────────────────────
    ToolDefinition(
        name="list_projects",
        description="List all projects in an organization",
        category=ToolCategory.ISSUE_KANBAN,
    ),
    ToolDefinition(
        name="list_organizations",
        description="List all available organizations",
        category=ToolCategory.ISSUE_KANBAN,
    ),
    ToolDefinition(
        name="list_org_members",
        description="List members of an organization",
        category=ToolCategory.ISSUE_KANBAN,
    ),
    ToolDefinition(
        name="create_issue",
        description="Create a new issue with title, description, and priority",
        category=ToolCategory.ISSUE_KANBAN,
    ),
    ToolDefinition(
        name="list_issues",
        description="List issues with filtering by status, priority, assignee, tag",
        category=ToolCategory.ISSUE_KANBAN,
    ),
    ToolDefinition(
        name="get_issue",
        description="Get detailed issue info including tags, relationships, sub-issues",
        category=ToolCategory.ISSUE_KANBAN,
    ),
    ToolDefinition(
        name="update_issue",
        description="Update issue title, description, status, or priority",
        category=ToolCategory.ISSUE_KANBAN,
    ),
    ToolDefinition(
        name="delete_issue",
        description="Permanently delete an issue",
        category=ToolCategory.ISSUE_KANBAN,
        dangerous=True,
    ),
    ToolDefinition(
        name="list_issue_priorities",
        description="List allowed priority values (urgent, high, medium, low)",
        category=ToolCategory.ISSUE_KANBAN,
    ),
    ToolDefinition(
        name="assign_issue",
        description="Assign a user to an issue",
        category=ToolCategory.ISSUE_KANBAN,
    ),
    ToolDefinition(
        name="unassign_issue",
        description="Remove an assignee from an issue",
        category=ToolCategory.ISSUE_KANBAN,
    ),
    ToolDefinition(
        name="list_issue_assignees",
        description="List all assignees for an issue",
        category=ToolCategory.ISSUE_KANBAN,
    ),
    ToolDefinition(
        name="add_issue_tag",
        description="Attach a tag to an issue",
        category=ToolCategory.ISSUE_KANBAN,
    ),
    ToolDefinition(
        name="remove_issue_tag",
        description="Remove a tag from an issue",
        category=ToolCategory.ISSUE_KANBAN,
    ),
    ToolDefinition(
        name="list_issue_tags",
        description="List tags attached to an issue",
        category=ToolCategory.ISSUE_KANBAN,
    ),
    ToolDefinition(
        name="list_tags",
        description="List all tags for a project",
        category=ToolCategory.ISSUE_KANBAN,
    ),
    ToolDefinition(
        name="create_issue_relationship",
        description="Create a relationship between two issues (blocking, related, has_duplicate)",
        category=ToolCategory.ISSUE_KANBAN,
    ),
    ToolDefinition(
        name="delete_issue_relationship",
        description="Delete an issue relationship",
        category=ToolCategory.ISSUE_KANBAN,
    ),
    # ── D - Context (1) ───────────────────────────────────────────────
    ToolDefinition(
        name="get_context",
        description="Return project, issue, workspace, and orchestrator-session metadata",
        category=ToolCategory.CONTEXT,
    ),
]

# Pre-built lookups
TOOL_BY_NAME: dict[str, ToolDefinition] = {t.name: t for t in TOOL_REGISTRY}

TOOLS_BY_CATEGORY: dict[ToolCategory, list[ToolDefinition]] = {}
for _tool in TOOL_REGISTRY:
    TOOLS_BY_CATEGORY.setdefault(_tool.category, []).append(_tool)


def get_tool_states(enabled_overrides: dict[str, bool] | None = None) -> list[ToolState]:
    """Build the full tool state list, applying any enabled overrides."""
    overrides = enabled_overrides or {}
    return [
        ToolState(
            name=t.name,
            description=t.description,
            category=t.category,
            enabled_by_default=t.enabled_by_default,
            dangerous=t.dangerous,
            enabled=overrides.get(t.name, t.enabled_by_default),
        )
        for t in TOOL_REGISTRY
    ]


def get_category_summary() -> dict[str, dict[str, Any]]:
    """Return a summary of tools per category."""
    return {
        cat.value: {
            "count": len(tools),
            "tools": [t.name for t in tools],
        }
        for cat, tools in TOOLS_BY_CATEGORY.items()
    }
