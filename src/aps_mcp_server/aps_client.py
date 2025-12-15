"""APS API Client for authentication and API calls."""

import asyncio
import time
import json
import os
from typing import Optional
from pathlib import Path
import httpx


class APSClient:
    """Client for Autodesk Platform Services API."""

    BASE_URL = "https://developer.api.autodesk.com"
    AUTH_URL = f"{BASE_URL}/authentication/v2/token"

    def _get_token_file_path(self) -> Path:
        """Get absolute path to token file in project root."""
        # Try to find .env file location (project root)
        current_dir = Path.cwd()

        # Search up the directory tree for .env file
        search_dir = current_dir
        for _ in range(5):  # Search up to 5 levels
            env_file = search_dir / ".env"
            if env_file.exists():
                return search_dir / ".aps_token.json"
            search_dir = search_dir.parent

        # Fallback to current directory
        return current_dir / ".aps_token.json"

    def __init__(self, client_id: str, client_secret: str, use_3legged: bool = True):
        """
        Initialize APS client.

        Args:
            client_id: APS application client ID
            client_secret: APS application client secret
            use_3legged: Use 3-legged OAuth if True, 2-legged if False
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.use_3legged = use_3legged
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.token_expires_at: float = 0
        self.http_client = httpx.AsyncClient()

        # Get token file path (evaluated at instance creation, not class load time)
        self.token_file_path = self._get_token_file_path()

        # Load 3-legged token if available
        if use_3legged:
            self._load_3legged_token()

    def _load_3legged_token(self):
        """Load 3-legged OAuth token from file."""
        token_path = self.token_file_path
        print(f"Looking for token at: {token_path.absolute()}")
        if token_path.exists():
            try:
                with open(token_path, "r") as f:
                    token_data = json.load(f)
                    self.access_token = token_data.get("access_token")
                    self.refresh_token = token_data.get("refresh_token")
                    # Calculate expiration time
                    expires_in = token_data.get("expires_in", 3600)
                    self.token_expires_at = time.time() + expires_in
                    print(f"✓ Loaded 3-legged OAuth token from {token_path.absolute()}")
            except Exception as e:
                print(f"Error loading token file: {e}")
                print("Please run auth.py to authenticate")
        else:
            print(f"Token file not found at: {token_path.absolute()}")
            print("Please run: python auth.py")

    def _save_3legged_token(self, token_data: dict):
        """
        Save 3-legged OAuth token to file.

        Args:
            token_data: Token response from OAuth
        """
        try:
            with open(self.token_file_path, "w") as f:
                json.dump(token_data, f, indent=2)
        except Exception as e:
            print(f"Error saving token file: {e}")

    async def get_access_token(self) -> str:
        """
        Get valid access token, refreshing if necessary.

        Returns:
            Valid access token
        """
        current_time = time.time()

        # Check if token is still valid (with 60 second buffer)
        if self.access_token and current_time < (self.token_expires_at - 60):
            return self.access_token

        # Use 3-legged or 2-legged OAuth
        if self.use_3legged:
            return await self._refresh_3legged_token()
        else:
            return await self._get_2legged_token()

    async def _get_2legged_token(self) -> str:
        """
        Get 2-legged OAuth token (client credentials).

        Returns:
            Access token
        """
        # Request new token using 2-legged OAuth
        # Scopes for Data Management + AEC Data Model + Issues APIs
        response = await self.http_client.post(
            self.AUTH_URL,
            data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "scope": "data:read data:write bucket:read bucket:create account:read account:write viewables:read"
            },
            headers={
                "Content-Type": "application/x-www-form-urlencoded"
            }
        )
        response.raise_for_status()

        token_data = response.json()
        self.access_token = token_data["access_token"]
        self.token_expires_at = time.time() + token_data["expires_in"]

        return self.access_token

    async def _refresh_3legged_token(self) -> str:
        """
        Refresh 3-legged OAuth token using refresh token.

        Returns:
            Access token
        """
        if not self.refresh_token:
            raise ValueError(
                "No refresh token available. Please run auth.py to authenticate."
            )

        # Refresh token
        response = await self.http_client.post(
            self.AUTH_URL,
            data={
                "grant_type": "refresh_token",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "refresh_token": self.refresh_token
            },
            headers={
                "Content-Type": "application/x-www-form-urlencoded"
            }
        )
        response.raise_for_status()

        token_data = response.json()
        self.access_token = token_data["access_token"]
        self.refresh_token = token_data.get("refresh_token", self.refresh_token)
        self.token_expires_at = time.time() + token_data["expires_in"]

        # Save updated token
        self._save_3legged_token(token_data)

        return self.access_token

    async def request(self, method: str, path: str, **kwargs) -> dict:
        """
        Make authenticated request to APS API.

        Args:
            method: HTTP method (GET, POST, etc.)
            path: API endpoint path
            **kwargs: Additional arguments for httpx request

        Returns:
            JSON response data
        """
        token = await self.get_access_token()

        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {token}"

        url = f"{self.BASE_URL}{path}"
        response = await self.http_client.request(
            method,
            url,
            headers=headers,
            **kwargs
        )
        response.raise_for_status()

        return response.json()

    async def graphql_request(self, query: str, variables: dict = None, region: str = "US") -> dict:
        """
        Make GraphQL request to AEC Data Model API.

        Args:
            query: GraphQL query string
            variables: GraphQL query variables
            region: Region (US, EMEA, etc.)

        Returns:
            GraphQL response data
        """
        token = await self.get_access_token()

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Region": region
        }

        payload = {"query": query}
        if variables:
            payload["variables"] = variables

        response = await self.http_client.post(
            "https://developer.api.autodesk.com/aec/graphql",
            headers=headers,
            json=payload
        )
        response.raise_for_status()

        return response.json()

    async def close(self):
        """Close the HTTP client."""
        await self.http_client.aclose()
