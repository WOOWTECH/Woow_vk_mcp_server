"""Health dashboard router for vk/mcp-server-vk.

Key difference from tuanle96 version: vk has a native /health
endpoint at port 8000 that returns JSON health status, so we can
check it directly instead of relying solely on process manager status.

Endpoints:
    GET /api/health - Dashboard health data
"""

from __future__ import annotations

import logging
from typing import Any

import httpx
from fastapi import APIRouter

from mcp_admin_core.config import get_config_store
from mcp_admin_core.process import get_process_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/health", tags=["health"])


async def _check_vk(vk_url: str) -> dict[str, Any]:
    """Check VK health via /web/health."""
    if not vk_url:
        return {"healthy": False, "url": "", "error": "Not configured"}
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{vk_url.rstrip('/')}/web/health")
            return {"healthy": resp.status_code == 200, "url": vk_url, "status_code": resp.status_code}
    except httpx.ConnectError:
        return {"healthy": False, "url": vk_url, "error": "Connection refused"}
    except httpx.TimeoutException:
        return {"healthy": False, "url": vk_url, "error": "Timed out"}
    except Exception as exc:
        return {"healthy": False, "url": vk_url, "error": str(exc)}


async def _check_mcp_health(mcp_port: int) -> dict[str, Any]:
    """Check vk's native /health endpoint.

    vk uses lazy-connect: /health returns {"status":"unhealthy"}
    until the first MCP request triggers VK authentication.
    We treat "responding at all" as healthy (server is ready to accept
    MCP connections). The "connected" field tracks VK auth state separately.
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"http://127.0.0.1:{mcp_port}/health")
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "healthy": True,  # Server is responding = healthy
                    "version": data.get("version", "unknown"),
                    "connected": data.get("connection", {}).get("connected", False),
                }
            return {"healthy": False, "version": "unknown", "connected": False}
    except Exception:
        return {"healthy": False, "version": "unknown", "connected": False}


async def _get_vk_info(vk_url: str, db: str, user: str, api_key: str) -> dict[str, Any]:
    """Get VK version and module count via XML-RPC."""
    info: dict[str, Any] = {"version": None, "db_name": db, "item_count": None}
    if not vk_url or not user:
        return info
    password = api_key
    if not password:
        return info
    try:
        import xmlrpc.client

        common = xmlrpc.client.ServerProxy(f"{vk_url.rstrip('/')}/xmlrpc/2/common", allow_none=True)
        ver = common.version()
        info["version"] = ver.get("server_version", "unknown") if isinstance(ver, dict) else str(ver)

        try:
            result = common.authenticate(db, {"login": user, "password": password, "type": "password"}, {})
        except (xmlrpc.client.Fault, TypeError):
            result = common.authenticate(db, user, password, {})
        uid = result.get("uid") if isinstance(result, dict) else result
        if uid:
            models = xmlrpc.client.ServerProxy(f"{vk_url.rstrip('/')}/xmlrpc/2/object", allow_none=True)
            count = models.execute_kw(db, uid, password, "ir.module.module", "search_count", [[["state", "=", "installed"]]])
            info["item_count"] = count
    except Exception as exc:
        logger.debug("Failed to get VK info: %s", exc)
    return info


@router.get("")
async def get_health() -> dict[str, Any]:
    """Return health data for the Dashboard frontend."""
    store = get_config_store()
    pm = get_process_manager()

    conn = await store.get("connection", {})
    vk_url = conn.get("vk_url", "")
    mcp_cfg = await store.get("mcp_server", {})
    mcp_port = mcp_cfg.get("port", 8000)

    pm_status = await pm.status()

    # vk-specific: check native /health endpoint
    mcp_health = await _check_mcp_health(mcp_port)
    mcp_running = pm_status.get("running", False)
    mcp_server = {
        "healthy": mcp_running and mcp_health.get("healthy", False),
        "pod_name": f"pid={pm_status.get('pid')}" if mcp_running else "stopped",
        "restart_count": pm_status.get("restart_count", 0),
        "vk_version": mcp_health.get("version", "unknown"),
        "vk_connected": mcp_health.get("connected", False),
    }

    target_app = await _check_vk(vk_url)
    proxy = {"healthy": True, "pod_name": "built-in reverse proxy"}

    vk_info = await _get_vk_info(
        vk_url,
        conn.get("vk_db", ""),
        conn.get("vk_user", ""),
        conn.get("vk_api_key", "") or conn.get("vk_password", ""),
    )

    all_healthy = mcp_server["healthy"] and target_app.get("healthy", False)

    return {
        "app_type": "vk-vk",
        "overall_status": "ok" if all_healthy else "degraded" if mcp_running or target_app.get("healthy") else "error",
        "mcp_server": mcp_server,
        "target_app": target_app,
        "proxy": proxy,
        "version": vk_info.get("version"),
        "db_name": vk_info.get("db_name"),
        "item_count": vk_info.get("item_count"),
        "namespace": "k3s",
    }
