"""Small asynchronous client for the Toodledo API v3."""
from __future__ import annotations

import base64
import json
import time
from typing import Any
from urllib.parse import urlencode

from aiohttp import ClientError, ClientSession

from .const import API_BASE, TOKEN_URL


class ToodledoError(Exception):
    """Raised when Toodledo returns an API error."""


class ToodledoClient:
    def __init__(self, session: ClientSession, client_id: str, client_secret: str,
                 access_token: str, refresh_token: str, expires_at: float) -> None:
        self.session = session
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.expires_at = expires_at

    async def _token_request(self, data: dict[str, str]) -> dict[str, Any]:
        credentials = base64.b64encode(
            f"{self.client_id}:{self.client_secret}".encode()
        ).decode()
        headers = {"Authorization": f"Basic {credentials}"}
        try:
            async with self.session.post(TOKEN_URL, data=data, headers=headers) as resp:
                result = await resp.json(content_type=None)
                if resp.status >= 400 or "errorCode" in result or "error" in result:
                    raise ToodledoError(str(result))
                return result
        except (ClientError, ValueError) as err:
            raise ToodledoError(f"Token request failed: {err}") from err

    async def exchange_code(self, code: str) -> dict[str, Any]:
        return await self._token_request({
            "grant_type": "authorization_code", "code": code, "vers": "3",
            "device": "Home Assistant", "f": "json",
        })

    async def refresh(self) -> None:
        result = await self._token_request({
            "grant_type": "refresh_token", "refresh_token": self.refresh_token,
            "vers": "3", "device": "Home Assistant", "f": "json",
        })
        self._save_tokens(result)

    def _save_tokens(self, result: dict[str, Any]) -> None:
        self.access_token = result["access_token"]
        self.refresh_token = result["refresh_token"]
        self.expires_at = time.time() + int(result.get("expires_in", 7200)) - 60

    async def _request(self, endpoint: str, data: dict[str, str] | None = None) -> Any:
        if time.time() >= self.expires_at:
            await self.refresh()
        payload = dict(data or {})
        payload["access_token"] = self.access_token
        try:
            async with self.session.post(f"{API_BASE}/{endpoint}", data=payload) as resp:
                result = await resp.json(content_type=None)
                if resp.status >= 400:
                    raise ToodledoError(f"HTTP {resp.status}: {result}")
                if isinstance(result, dict) and ("errorCode" in result or "error" in result):
                    raise ToodledoError(str(result))
                return result
        except (ClientError, ValueError) as err:
            raise ToodledoError(f"Toodledo request failed: {err}") from err

    async def get_tasks(self) -> list[dict[str, Any]]:
        result = await self._request("tasks/get.php", {
            "comp": "-1", "num": "1000", "fields": "duedate,note,priority,star"
        })
        if not isinstance(result, list):
            raise ToodledoError(f"Unexpected task response: {result}")
        return [item for item in result if isinstance(item, dict) and "id" in item]

    async def add_task(self, title: str, due: int | None = None, note: str | None = None) -> str:
        task: dict[str, Any] = {"title": title}
        if due is not None:
            task["duedate"] = due
        if note:
            task["note"] = note
        result = await self._request("tasks/add.php", {"tasks": json.dumps([task])})
        if not isinstance(result, list) or not result or "id" not in result[0]:
            raise ToodledoError(f"Could not create task: {result}")
        return str(result[0]["id"])

    async def edit_task(self, uid: str, **fields: Any) -> None:
        task = {"id": int(uid), **fields}
        result = await self._request("tasks/edit.php", {"tasks": json.dumps([task])})
        if isinstance(result, list) and result and "errorCode" in result[0]:
            raise ToodledoError(str(result[0]))

    async def delete_tasks(self, uids: list[str]) -> None:
        if uids:
            await self._request("tasks/delete.php", {
                "tasks": json.dumps([int(uid) for uid in uids])
            })
