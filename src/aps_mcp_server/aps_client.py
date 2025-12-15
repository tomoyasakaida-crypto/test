"""APS API Client for authentication and API calls."""

import asyncio
import time
from typing import Optional
import httpx


class APSClient:
    """Client for Autodesk Platform Services API."""

    BASE_URL = "https://developer.api.autodesk.com"
    AUTH_URL = f"{BASE_URL}/authentication/v2/token"

    def __init__(self, client_id: str, client_secret: str):
        """
        Initialize APS client.

        Args:
            client_id: APS application client ID
            client_secret: APS application client secret
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token: Optional[str] = None
        self.token_expires_at: float = 0
        self.http_client = httpx.AsyncClient()

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

        # Request new token using 2-legged OAuth
        # Scopes for Data Management + AEC Data Model + Issues + Index APIs
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
        self.token_expires_at = current_time + token_data["expires_in"]

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
