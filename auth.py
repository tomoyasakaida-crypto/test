#!/usr/bin/env python3
"""
APS 3-legged OAuth Authentication Helper

This script helps you authenticate with Autodesk Platform Services using 3-legged OAuth.
Run this script once to obtain and save authentication tokens.
"""

import asyncio
import os
import json
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from pathlib import Path
from dotenv import load_dotenv
import httpx

# Load environment variables
load_dotenv()

# Configuration
CLIENT_ID = os.getenv("APS_CLIENT_ID")
CLIENT_SECRET = os.getenv("APS_CLIENT_SECRET")
REDIRECT_URI = "http://localhost:8080/callback"

def get_token_file_path() -> Path:
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

TOKEN_FILE = str(get_token_file_path())

# Scopes for AEC Data Model API (GraphQL)
SCOPES = [
    "data:read",
    "data:write",
    "bucket:read",
    "bucket:create",
    "account:read",
    "account:write",
    "viewables:read"
]

# Authorization code storage
auth_code = None


class CallbackHandler(BaseHTTPRequestHandler):
    """HTTP request handler for OAuth callback."""

    def do_GET(self):
        """Handle GET request from OAuth callback."""
        global auth_code

        # Parse the callback URL
        parsed_url = urlparse(self.path)

        if parsed_url.path == "/callback":
            # Extract authorization code
            query_params = parse_qs(parsed_url.query)

            if "code" in query_params:
                auth_code = query_params["code"][0]

                # Send success response
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(b"""
                <html>
                <head><title>Authentication Successful</title></head>
                <body>
                    <h1>Authentication Successful!</h1>
                    <p>You can close this window and return to the terminal.</p>
                    <script>window.close();</script>
                </body>
                </html>
                """)
            else:
                # Error in callback
                error = query_params.get("error", ["Unknown error"])[0]
                self.send_response(400)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(f"""
                <html>
                <head><title>Authentication Failed</title></head>
                <body>
                    <h1>Authentication Failed</h1>
                    <p>Error: {error}</p>
                </body>
                </html>
                """.encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        """Suppress HTTP server logs."""
        pass


async def exchange_code_for_token(code: str) -> dict:
    """
    Exchange authorization code for access token.

    Args:
        code: Authorization code from OAuth callback

    Returns:
        Token response containing access_token, refresh_token, etc.
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://developer.api.autodesk.com/authentication/v2/token",
            data={
                "grant_type": "authorization_code",
                "code": code,
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "redirect_uri": REDIRECT_URI
            },
            headers={
                "Content-Type": "application/x-www-form-urlencoded"
            }
        )
        response.raise_for_status()
        return response.json()


def save_token(token_data: dict):
    """
    Save token data to file.

    Args:
        token_data: Token response from OAuth
    """
    token_path = Path(TOKEN_FILE)
    with open(token_path, "w") as f:
        json.dump(token_data, f, indent=2)
    print(f"\nToken saved to: {token_path.absolute()}")
    print("You can now use the MCP server with 3-legged OAuth!")


def main():
    """Main authentication flow."""
    if not CLIENT_ID or not CLIENT_SECRET:
        print("Error: APS_CLIENT_ID and APS_CLIENT_SECRET must be set in .env file")
        return

    print("=== APS 3-Legged OAuth Authentication ===\n")
    print("This script will:")
    print("1. Open your browser to Autodesk login page")
    print("2. Start a local server to receive the callback")
    print("3. Save your authentication token\n")

    # Build authorization URL
    scope_string = " ".join(SCOPES)
    auth_url = (
        f"https://developer.api.autodesk.com/authentication/v2/authorize"
        f"?response_type=code"
        f"&client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&scope={scope_string}"
    )

    print(f"Authorization URL:\n{auth_url}\n")
    print("Opening browser for authentication...")

    # Open browser
    webbrowser.open(auth_url)

    # Start local HTTP server
    server_address = ("localhost", 8080)
    httpd = HTTPServer(server_address, CallbackHandler)

    print("Waiting for callback on http://localhost:8080/callback...")
    print("(Press Ctrl+C to cancel)\n")

    # Wait for callback (with timeout)
    global auth_code
    timeout = 300  # 5 minutes
    start_time = asyncio.get_event_loop().time()

    try:
        while auth_code is None:
            httpd.handle_request()

            # Check timeout
            if asyncio.get_event_loop().time() - start_time > timeout:
                print("Timeout waiting for authentication callback")
                return

    except KeyboardInterrupt:
        print("\nAuthentication cancelled")
        return
    finally:
        httpd.server_close()

    if auth_code:
        print("Authorization code received!")
        print("Exchanging code for access token...")

        # Exchange code for token
        try:
            token_data = asyncio.run(exchange_code_for_token(auth_code))
            save_token(token_data)

            print("\n✓ Authentication successful!")
            print("\nNext steps:")
            print("1. Restart Claude Desktop")
            print("2. Try using AEC Data Model API tools (get_element_groups, etc.)")

        except Exception as e:
            print(f"\nError exchanging code for token: {e}")
            return


if __name__ == "__main__":
    main()
