"""MCP Server for Autodesk Platform Services."""

import asyncio
import os
from typing import Any
from dotenv import load_dotenv

from mcp.server import Server
from mcp.types import (
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)
import mcp.server.stdio

from .aps_client import APSClient


# Load environment variables
load_dotenv()

# Initialize APS client
client_id = os.getenv("APS_CLIENT_ID")
client_secret = os.getenv("APS_CLIENT_SECRET")

if not client_id or not client_secret:
    raise ValueError(
        "APS_CLIENT_ID and APS_CLIENT_SECRET must be set in environment variables"
    )

aps_client = APSClient(client_id, client_secret)

# Create MCP server
app = Server("aps-mcp-server")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available APS tools."""
    return [
        Tool(
            name="list_buckets",
            description="List all buckets in APS Data Management",
            inputSchema={
                "type": "object",
                "properties": {
                    "region": {
                        "type": "string",
                        "description": "Region (US or EMEA)",
                        "enum": ["US", "EMEA"],
                        "default": "US"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of buckets to return",
                        "default": 100
                    }
                }
            }
        ),
        Tool(
            name="create_bucket",
            description="Create a new bucket in APS Data Management",
            inputSchema={
                "type": "object",
                "properties": {
                    "bucket_key": {
                        "type": "string",
                        "description": "Unique bucket key (lowercase, no spaces)"
                    },
                    "policy_key": {
                        "type": "string",
                        "description": "Data retention policy",
                        "enum": ["transient", "temporary", "persistent"],
                        "default": "transient"
                    }
                },
                "required": ["bucket_key"]
            }
        ),
        Tool(
            name="get_bucket_details",
            description="Get details of a specific bucket",
            inputSchema={
                "type": "object",
                "properties": {
                    "bucket_key": {
                        "type": "string",
                        "description": "Bucket key"
                    }
                },
                "required": ["bucket_key"]
            }
        ),
        Tool(
            name="list_objects",
            description="List objects in a bucket",
            inputSchema={
                "type": "object",
                "properties": {
                    "bucket_key": {
                        "type": "string",
                        "description": "Bucket key"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of objects to return",
                        "default": 100
                    }
                },
                "required": ["bucket_key"]
            }
        ),
        Tool(
            name="get_object_details",
            description="Get details of a specific object in a bucket",
            inputSchema={
                "type": "object",
                "properties": {
                    "bucket_key": {
                        "type": "string",
                        "description": "Bucket key"
                    },
                    "object_key": {
                        "type": "string",
                        "description": "Object key"
                    }
                },
                "required": ["bucket_key", "object_key"]
            }
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls."""
    try:
        if name == "list_buckets":
            region = arguments.get("region", "US")
            limit = arguments.get("limit", 100)

            response = await aps_client.request(
                "GET",
                f"/oss/v2/buckets",
                params={
                    "region": region,
                    "limit": limit
                }
            )

            buckets = response.get("items", [])
            result = f"Found {len(buckets)} buckets:\n\n"
            for bucket in buckets:
                result += f"- {bucket['bucketKey']}\n"
                result += f"  Policy: {bucket.get('policyKey', 'N/A')}\n"
                result += f"  Created: {bucket.get('createdDate', 'N/A')}\n\n"

            return [TextContent(type="text", text=result)]

        elif name == "create_bucket":
            bucket_key = arguments["bucket_key"]
            policy_key = arguments.get("policy_key", "transient")

            response = await aps_client.request(
                "POST",
                "/oss/v2/buckets",
                json={
                    "bucketKey": bucket_key,
                    "policyKey": policy_key
                }
            )

            result = f"Bucket created successfully:\n"
            result += f"- Key: {response['bucketKey']}\n"
            result += f"- Policy: {response['policyKey']}\n"
            result += f"- Owner: {response.get('bucketOwner', 'N/A')}\n"

            return [TextContent(type="text", text=result)]

        elif name == "get_bucket_details":
            bucket_key = arguments["bucket_key"]

            response = await aps_client.request(
                "GET",
                f"/oss/v2/buckets/{bucket_key}/details"
            )

            result = f"Bucket Details:\n"
            result += f"- Key: {response['bucketKey']}\n"
            result += f"- Policy: {response.get('policyKey', 'N/A')}\n"
            result += f"- Owner: {response.get('bucketOwner', 'N/A')}\n"
            result += f"- Created: {response.get('createdDate', 'N/A')}\n"
            result += f"- Permissions: {response.get('permissions', [])}\n"

            return [TextContent(type="text", text=result)]

        elif name == "list_objects":
            bucket_key = arguments["bucket_key"]
            limit = arguments.get("limit", 100)

            response = await aps_client.request(
                "GET",
                f"/oss/v2/buckets/{bucket_key}/objects",
                params={"limit": limit}
            )

            objects = response.get("items", [])
            result = f"Found {len(objects)} objects in bucket '{bucket_key}':\n\n"
            for obj in objects:
                result += f"- {obj['objectKey']}\n"
                result += f"  Size: {obj.get('size', 0)} bytes\n"
                result += f"  SHA1: {obj.get('sha1', 'N/A')}\n\n"

            return [TextContent(type="text", text=result)]

        elif name == "get_object_details":
            bucket_key = arguments["bucket_key"]
            object_key = arguments["object_key"]

            response = await aps_client.request(
                "GET",
                f"/oss/v2/buckets/{bucket_key}/objects/{object_key}/details"
            )

            result = f"Object Details:\n"
            result += f"- Key: {response['objectKey']}\n"
            result += f"- Bucket: {response['bucketKey']}\n"
            result += f"- Size: {response.get('size', 0)} bytes\n"
            result += f"- Content-Type: {response.get('contentType', 'N/A')}\n"
            result += f"- SHA1: {response.get('sha1', 'N/A')}\n"
            result += f"- Location: {response.get('location', 'N/A')}\n"

            return [TextContent(type="text", text=result)]

        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def main():
    """Run the MCP server."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
