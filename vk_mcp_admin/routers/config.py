"""Connection configuration router for vk/mcp-server-vk.

Manages VK connection settings. Key differences from tuanle96:
- Uses ODOO_USER (not ODOO_USERNAME)
- Supports ODOO_API_KEY for Phase 2 standard mode
- Supports ODOO_YOLO for Phase 1 read-only mode

Endpoints:
    GET  /api/config            - Current connection config
    PUT  /api/config/connection  - Update connection credentials
    POST /api/config/test        - Test XML-RPC connectivity
"""

from __future__ import annotations

import logging
import xmlrpc.client
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from mcp_admin_core.config import get_config_store
from mcp_admin_core.process import get_process_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/config", tags=["config"])


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class ConnectionConfig(BaseModel):
    vk_url: str = ""
    vk_db: str = ""
    vk_user: str = ""
    vk_api_key_masked: str = "********"
    vk_yolo: str = "off"


class ConnectionUpdateRequest(BaseModel):
    vk_url: str = Field(..., description="VK instance URL")
    vk_db: str = Field(..., description="Database name")
    vk_user: str = Field(..., description="VK username (required for XML-RPC uid)")
    vk_api_key: str = Field(default="", description="API key (Phase 2 standard mode)")
    vk_password: str = Field(default="", description="Password (Phase 1 YOLO mode)")
    vk_yolo: str = Field(default="off", description="YOLO mode: off, read, or true")
    restart: bool = Field(default=True, description="Restart MCP server after update")


class ConnectionUpdateResponse(BaseModel):
    success: bool
    message: str
    restarted: bool = False


class ConnectionTestRequest(BaseModel):
    vk_url: str
    vk_db: str
    vk_user: str
    vk_api_key: str = ""
    vk_password: str = ""


class ConnectionTestResponse(BaseModel):
    success: bool
    message: str
    uid: int | None = None
    server_version: str | None = None
    details: dict[str, Any] | None = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _mask(s: str) -> str:
    if not s or len(s) <= 2:
        return "****" if s else "(not set)"
    return f"{s[:8]}{'*' * max(0, len(s) - 12)}{s[-4:]}" if len(s) > 12 else f"{s[:4]}****"


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("", response_model=ConnectionConfig)
async def get_config() -> ConnectionConfig:
    """Return current connection config (sensitive fields masked)."""
    store = get_config_store()
    conn = await store.get("connection", {})
    api_key = conn.get("vk_api_key", "")
    return ConnectionConfig(
        vk_url=conn.get("vk_url", ""),
        vk_db=conn.get("vk_db", ""),
        vk_user=conn.get("vk_user", ""),
        vk_api_key_masked=_mask(api_key),
        vk_yolo=conn.get("vk_yolo", "off"),
    )


@router.put("/connection", response_model=ConnectionUpdateResponse)
async def update_connection(req: ConnectionUpdateRequest) -> ConnectionUpdateResponse:
    """Update connection credentials and optionally restart MCP server."""
    store = get_config_store()
    update_data: dict[str, Any] = {
        "vk_url": req.vk_url,
        "vk_db": req.vk_db,
        "vk_user": req.vk_user,
        "vk_yolo": req.vk_yolo,
    }
    if req.vk_api_key:
        update_data["vk_api_key"] = req.vk_api_key
    if req.vk_password:
        update_data["vk_password"] = req.vk_password

    await store.patch("connection", update_data)
    logger.info("Updated vk connection config")

    restarted = False
    if req.restart:
        pm = get_process_manager()
        if pm.is_running:
            await pm.restart()
            restarted = True

    return ConnectionUpdateResponse(
        success=True,
        message="Connection credentials updated",
        restarted=restarted,
    )


@router.post("/test", response_model=ConnectionTestResponse)
async def test_connection(req: ConnectionTestRequest) -> ConnectionTestResponse:
    """Test XML-RPC connectivity to VK."""
    url = req.vk_url.rstrip("/")
    password = req.vk_api_key or req.vk_password

    if not password:
        return ConnectionTestResponse(success=False, message="No API key or password provided")

    try:
        common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common", allow_none=True)
        version_info = common.version()
    except Exception as exc:
        return ConnectionTestResponse(success=False, message=f"Cannot reach VK: {exc}")

    server_version = version_info.get("server_version", "unknown") if isinstance(version_info, dict) else str(version_info)

    try:
        try:
            result = common.authenticate(
                req.vk_db,
                {"login": req.vk_user, "password": password, "type": "password"},
                {},
            )
            uid = result.get("uid") if isinstance(result, dict) else result
        except (xmlrpc.client.Fault, TypeError):
            result = common.authenticate(req.vk_db, req.vk_user, password, {})
            uid = result.get("uid") if isinstance(result, dict) else result
    except xmlrpc.client.Fault as fault:
        return ConnectionTestResponse(success=False, message=f"XML-RPC fault: {fault.faultString}", server_version=server_version)
    except Exception as exc:
        return ConnectionTestResponse(success=False, message=f"Auth failed: {exc}", server_version=server_version)

    if not uid:
        return ConnectionTestResponse(success=False, message="Invalid credentials (uid=False)", server_version=server_version)

    return ConnectionTestResponse(
        success=True,
        message=f"Authenticated as UID {uid}",
        uid=uid,
        server_version=server_version,
        details={"database": req.vk_db, "user": req.vk_user},
    )
