"""Firebase ID-token verification for state-changing portfolio APIs."""

from __future__ import annotations

import requests
from flask import Request

from backend.errors import ApiError


class IdentityService:
    def __init__(self, api_key: str, environment: str = "development", timeout: float = 10):
        self.api_key, self.environment, self.timeout = api_key, environment, timeout

    def user_id(self, request: Request) -> str:
        authorization = request.headers.get("Authorization", "")
        if authorization.startswith("Bearer ") and self.api_key:
            try:
                response = requests.post(
                    f"https://identitytoolkit.googleapis.com/v1/accounts:lookup?key={self.api_key}",
                    json={"idToken": authorization[7:]}, timeout=self.timeout,
                )
                response.raise_for_status()
                users = response.json().get("users", [])
                if users: return users[0]["localId"]
            except requests.RequestException as error:
                raise ApiError("Authentication service is unavailable.", 503, "auth_unavailable") from error
        if self.environment == "development" and request.headers.get("X-Nexora-Dev-User"):
            return request.headers["X-Nexora-Dev-User"]
        raise ApiError("A valid Firebase ID token is required.", 401, "unauthorized")
