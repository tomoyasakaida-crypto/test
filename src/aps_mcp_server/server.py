"""MCP Server for Autodesk Platform Services."""

import asyncio
import os
import base64
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


def encode_urn(urn: str) -> str:
    """
    Encode URN to Base64 URL-safe format for Model Derivative API.

    Args:
        urn: URN string (e.g., urn:adsk.viewing:fs.file:...)

    Returns:
        Base64 URL-safe encoded URN
    """
    return base64.urlsafe_b64encode(urn.encode()).decode().rstrip('=')


def decode_urn(encoded_urn: str) -> str:
    """
    Decode Base64 URL-safe URN.

    Args:
        encoded_urn: Base64 URL-safe encoded URN

    Returns:
        Decoded URN string
    """
    # Add padding if needed
    padding = 4 - len(encoded_urn) % 4
    if padding != 4:
        encoded_urn += '=' * padding
    return base64.urlsafe_b64decode(encoded_urn.encode()).decode()


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
        # AEC Data Model API Tools
        Tool(
            name="list_hubs",
            description="List all hubs (accounts) accessible in AEC Data Model",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="list_projects",
            description="List all projects in a hub",
            inputSchema={
                "type": "object",
                "properties": {
                    "hub_id": {
                        "type": "string",
                        "description": "Hub ID (e.g., b.xxx)"
                    }
                },
                "required": ["hub_id"]
            }
        ),
        Tool(
            name="get_project_top_folders",
            description="Get top-level folders in a project",
            inputSchema={
                "type": "object",
                "properties": {
                    "hub_id": {
                        "type": "string",
                        "description": "Hub ID"
                    },
                    "project_id": {
                        "type": "string",
                        "description": "Project ID (e.g., b.xxx)"
                    }
                },
                "required": ["hub_id", "project_id"]
            }
        ),
        Tool(
            name="get_folder_contents",
            description="Get contents (folders and items) of a folder",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "Project ID"
                    },
                    "folder_id": {
                        "type": "string",
                        "description": "Folder ID (e.g., urn:adsk.wipprod:fs.folder:xxx)"
                    }
                },
                "required": ["project_id", "folder_id"]
            }
        ),
        Tool(
            name="get_item_versions",
            description="Get all versions of an item",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "Project ID"
                    },
                    "item_id": {
                        "type": "string",
                        "description": "Item ID (e.g., urn:adsk.wipprod:dm.lineage:xxx)"
                    }
                },
                "required": ["project_id", "item_id"]
            }
        ),
        Tool(
            name="get_item_tip",
            description="Get the latest version (tip) of an item",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "Project ID"
                    },
                    "item_id": {
                        "type": "string",
                        "description": "Item ID"
                    }
                },
                "required": ["project_id", "item_id"]
            }
        ),
        # AEC Data Model API Tools (GraphQL - ElementGroups)
        Tool(
            name="get_element_groups",
            description="Get ElementGroups (models) in a project using AEC Data Model API",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "Project ID (b.xxx format)"
                    }
                },
                "required": ["project_id"]
            }
        ),
        Tool(
            name="get_elements",
            description="Get elements from an ElementGroup using AEC Data Model API",
            inputSchema={
                "type": "object",
                "properties": {
                    "element_group_id": {
                        "type": "string",
                        "description": "ElementGroup ID from get_element_groups"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of elements to return (max 500)",
                        "default": 100
                    }
                },
                "required": ["element_group_id"]
            }
        ),
        Tool(
            name="get_elements_by_category",
            description="Get model elements filtered by category (Walls, Doors, Windows, etc.) using AEC Data Model API",
            inputSchema={
                "type": "object",
                "properties": {
                    "element_group_id": {
                        "type": "string",
                        "description": "ElementGroup ID from get_element_groups"
                    },
                    "category": {
                        "type": "string",
                        "description": "Element category (e.g., Walls, Doors, Windows, Floors, Roofs)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of elements to return (max 500)",
                        "default": 100
                    }
                },
                "required": ["element_group_id", "category"]
            }
        ),
        # Issues API Tools
        Tool(
            name="list_issues",
            description="List all issues in a project container",
            inputSchema={
                "type": "object",
                "properties": {
                    "container_id": {
                        "type": "string",
                        "description": "Container ID (project ID without 'b.' prefix)"
                    },
                    "filter": {
                        "type": "object",
                        "description": "Optional filters (e.g., {'status': 'open'})",
                        "default": {}
                    }
                },
                "required": ["container_id"]
            }
        ),
        Tool(
            name="get_issue_details",
            description="Get details of a specific issue",
            inputSchema={
                "type": "object",
                "properties": {
                    "container_id": {
                        "type": "string",
                        "description": "Container ID"
                    },
                    "issue_id": {
                        "type": "string",
                        "description": "Issue ID"
                    }
                },
                "required": ["container_id", "issue_id"]
            }
        ),
        Tool(
            name="create_issue",
            description="Create a new issue in the project",
            inputSchema={
                "type": "object",
                "properties": {
                    "container_id": {
                        "type": "string",
                        "description": "Container ID"
                    },
                    "title": {
                        "type": "string",
                        "description": "Issue title"
                    },
                    "description": {
                        "type": "string",
                        "description": "Issue description"
                    },
                    "issue_type_id": {
                        "type": "string",
                        "description": "Issue type ID"
                    },
                    "status": {
                        "type": "string",
                        "description": "Issue status",
                        "default": "open"
                    }
                },
                "required": ["container_id", "title", "description", "issue_type_id"]
            }
        ),
        Tool(
            name="update_issue",
            description="Update an existing issue",
            inputSchema={
                "type": "object",
                "properties": {
                    "container_id": {
                        "type": "string",
                        "description": "Container ID"
                    },
                    "issue_id": {
                        "type": "string",
                        "description": "Issue ID"
                    },
                    "updates": {
                        "type": "object",
                        "description": "Fields to update (e.g., {'status': 'closed', 'title': 'New Title'})"
                    }
                },
                "required": ["container_id", "issue_id", "updates"]
            }
        ),
        Tool(
            name="get_issue_comments",
            description="Get all comments for an issue",
            inputSchema={
                "type": "object",
                "properties": {
                    "container_id": {
                        "type": "string",
                        "description": "Container ID"
                    },
                    "issue_id": {
                        "type": "string",
                        "description": "Issue ID"
                    }
                },
                "required": ["container_id", "issue_id"]
            }
        ),
        Tool(
            name="add_issue_comment",
            description="Add a comment to an issue",
            inputSchema={
                "type": "object",
                "properties": {
                    "container_id": {
                        "type": "string",
                        "description": "Container ID"
                    },
                    "issue_id": {
                        "type": "string",
                        "description": "Issue ID"
                    },
                    "comment": {
                        "type": "string",
                        "description": "Comment text"
                    }
                },
                "required": ["container_id", "issue_id", "comment"]
            }
        ),
        # Model Derivative API Tools
        Tool(
            name="get_manifest",
            description="Get the manifest of a translated model",
            inputSchema={
                "type": "object",
                "properties": {
                    "urn": {
                        "type": "string",
                        "description": "Model URN (will be automatically encoded if needed)"
                    }
                },
                "required": ["urn"]
            }
        ),
        Tool(
            name="get_metadata_views",
            description="Get list of viewable items (metadata views) in a model",
            inputSchema={
                "type": "object",
                "properties": {
                    "urn": {
                        "type": "string",
                        "description": "Model URN"
                    }
                },
                "required": ["urn"]
            }
        ),
        Tool(
            name="get_object_tree",
            description="Get the object tree (hierarchy) of a model view",
            inputSchema={
                "type": "object",
                "properties": {
                    "urn": {
                        "type": "string",
                        "description": "Model URN"
                    },
                    "guid": {
                        "type": "string",
                        "description": "View GUID (from get_metadata_views)"
                    }
                },
                "required": ["urn", "guid"]
            }
        ),
        Tool(
            name="get_all_properties",
            description="Get all properties of all objects in a model view",
            inputSchema={
                "type": "object",
                "properties": {
                    "urn": {
                        "type": "string",
                        "description": "Model URN"
                    },
                    "guid": {
                        "type": "string",
                        "description": "View GUID (from get_metadata_views)"
                    }
                },
                "required": ["urn", "guid"]
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

        # AEC Data Model API handlers
        elif name == "list_hubs":
            response = await aps_client.request(
                "GET",
                "/project/v1/hubs"
            )

            hubs = response.get("data", [])
            result = f"Found {len(hubs)} hubs:\n\n"
            for hub in hubs:
                result += f"- {hub['attributes']['name']}\n"
                result += f"  ID: {hub['id']}\n"
                result += f"  Type: {hub['attributes'].get('extension', {}).get('type', 'N/A')}\n"
                result += f"  Region: {hub['attributes'].get('region', 'N/A')}\n\n"

            return [TextContent(type="text", text=result)]

        elif name == "list_projects":
            hub_id = arguments["hub_id"]

            response = await aps_client.request(
                "GET",
                f"/project/v1/hubs/{hub_id}/projects"
            )

            projects = response.get("data", [])
            result = f"Found {len(projects)} projects in hub '{hub_id}':\n\n"
            for project in projects:
                result += f"- {project['attributes']['name']}\n"
                result += f"  ID: {project['id']}\n"
                result += f"  Type: {project['type']}\n\n"

            return [TextContent(type="text", text=result)]

        elif name == "get_project_top_folders":
            hub_id = arguments["hub_id"]
            project_id = arguments["project_id"]

            response = await aps_client.request(
                "GET",
                f"/project/v1/hubs/{hub_id}/projects/{project_id}/topFolders"
            )

            folders = response.get("data", [])
            result = f"Found {len(folders)} top-level folders:\n\n"
            for folder in folders:
                result += f"- {folder['attributes']['name']}\n"
                result += f"  ID: {folder['id']}\n"
                result += f"  Type: {folder['type']}\n\n"

            return [TextContent(type="text", text=result)]

        elif name == "get_folder_contents":
            project_id = arguments["project_id"]
            folder_id = arguments["folder_id"]

            response = await aps_client.request(
                "GET",
                f"/data/v1/projects/{project_id}/folders/{folder_id}/contents"
            )

            items = response.get("data", [])
            result = f"Found {len(items)} items in folder:\n\n"

            folders = [item for item in items if item["type"] == "folders"]
            files = [item for item in items if item["type"] == "items"]

            if folders:
                result += "Folders:\n"
                for folder in folders:
                    result += f"- {folder['attributes']['displayName']}\n"
                    result += f"  ID: {folder['id']}\n\n"

            if files:
                result += "Files:\n"
                for file in files:
                    result += f"- {file['attributes']['displayName']}\n"
                    result += f"  ID: {file['id']}\n"
                    result += f"  Extension: {file['attributes'].get('extension', {}).get('type', 'N/A')}\n"
                    result += f"  Version: {file['attributes'].get('extension', {}).get('version', 'N/A')}\n\n"

            return [TextContent(type="text", text=result)]

        elif name == "get_item_versions":
            project_id = arguments["project_id"]
            item_id = arguments["item_id"]

            response = await aps_client.request(
                "GET",
                f"/data/v1/projects/{project_id}/items/{item_id}/versions"
            )

            versions = response.get("data", [])
            result = f"Found {len(versions)} versions:\n\n"
            for version in versions:
                result += f"- Version {version['attributes'].get('versionNumber', 'N/A')}\n"
                result += f"  ID: {version['id']}\n"
                result += f"  Display Name: {version['attributes']['displayName']}\n"
                result += f"  Created: {version['attributes'].get('createTime', 'N/A')}\n"
                result += f"  Created By: {version['attributes'].get('createUserName', 'N/A')}\n\n"

            return [TextContent(type="text", text=result)]

        elif name == "get_item_tip":
            project_id = arguments["project_id"]
            item_id = arguments["item_id"]

            response = await aps_client.request(
                "GET",
                f"/data/v1/projects/{project_id}/items/{item_id}/tip"
            )

            version = response.get("data", {})
            result = f"Latest Version:\n"
            result += f"- Version Number: {version['attributes'].get('versionNumber', 'N/A')}\n"
            result += f"- ID: {version['id']}\n"
            result += f"- Display Name: {version['attributes']['displayName']}\n"
            result += f"- Created: {version['attributes'].get('createTime', 'N/A')}\n"
            result += f"- Created By: {version['attributes'].get('createUserName', 'N/A')}\n"
            result += f"- File Type: {version['attributes'].get('fileType', 'N/A')}\n"
            result += f"- Storage Size: {version['attributes'].get('storageSize', 0)} bytes\n"

            # Include derivative URN if available
            derivatives = version.get("relationships", {}).get("derivatives", {}).get("data", {})
            if derivatives:
                result += f"- Derivative URN: {derivatives.get('id', 'N/A')}\n"

            return [TextContent(type="text", text=result)]

        # AEC Data Model API handlers (GraphQL - ElementGroups)
        elif name == "get_element_groups":
            project_id = arguments["project_id"]

            # GraphQL query to get ElementGroups
            query = """
            query GetElementGroupsByProject($projectId: ID!) {
                elementGroupsByProject(projectId: $projectId) {
                    pagination {
                        cursor
                    }
                    results {
                        id
                        name
                        alternativeIdentifiers {
                            fileUrn
                            fileVersionUrn
                        }
                    }
                }
            }
            """

            response = await aps_client.graphql_request(
                query=query,
                variables={"projectId": project_id}
            )

            data = response.get("data", {}).get("elementGroupsByProject", {})
            element_groups = data.get("results", [])

            result = f"Found {len(element_groups)} ElementGroups:\n\n"
            for eg in element_groups:
                result += f"- {eg.get('name', 'N/A')}\n"
                result += f"  ID: {eg.get('id', 'N/A')}\n"
                alt_ids = eg.get("alternativeIdentifiers", {})
                if alt_ids:
                    result += f"  File URN: {alt_ids.get('fileUrn', 'N/A')}\n"
                    result += f"  Version URN: {alt_ids.get('fileVersionUrn', 'N/A')}\n"
                result += "\n"

            return [TextContent(type="text", text=result)]

        elif name == "get_elements":
            element_group_id = arguments["element_group_id"]
            limit = arguments.get("limit", 100)

            # GraphQL query to get elements
            query = """
            query GetElements($elementGroupId: ID!, $limit: Int!) {
                elementsByElementGroup(elementGroupId: $elementGroupId, pagination: {limit: $limit}) {
                    pagination {
                        cursor
                    }
                    results {
                        id
                        name
                        properties {
                            results {
                                name
                                value
                                definition {
                                    units {
                                        name
                                    }
                                }
                            }
                        }
                    }
                }
            }
            """

            response = await aps_client.graphql_request(
                query=query,
                variables={"elementGroupId": element_group_id, "limit": limit}
            )

            data = response.get("data", {}).get("elementsByElementGroup", {})
            elements = data.get("results", [])

            result = f"Found {len(elements)} elements:\n\n"
            for elem in elements[:20]:  # Show first 20
                result += f"- {elem.get('name', 'N/A')}\n"
                result += f"  ID: {elem.get('id', 'N/A')}\n"

                # Show some key properties
                props = elem.get("properties", {}).get("results", [])
                for prop in props[:5]:  # Show first 5 properties
                    prop_name = prop.get("name", "N/A")
                    prop_value = prop.get("value", "N/A")
                    units = prop.get("definition", {}).get("units", {})
                    unit_name = units.get("name", "") if units else ""
                    result += f"  {prop_name}: {prop_value} {unit_name}\n".strip() + "\n"

                result += "\n"

            if len(elements) > 20:
                result += f"... and {len(elements) - 20} more elements\n"

            return [TextContent(type="text", text=result)]

        elif name == "get_elements_by_category":
            element_group_id = arguments["element_group_id"]
            category = arguments["category"]
            limit = arguments.get("limit", 100)

            # GraphQL query with category filter
            query = """
            query GetElementsByCategory($elementGroupId: ID!, $propertyFilter: String!, $limit: Int!) {
                elementsByElementGroup(
                    elementGroupId: $elementGroupId,
                    filter: {query: $propertyFilter},
                    pagination: {limit: $limit}
                ) {
                    pagination {
                        cursor
                    }
                    results {
                        id
                        name
                        properties {
                            results {
                                name
                                value
                                definition {
                                    units {
                                        name
                                    }
                                }
                            }
                        }
                    }
                }
            }
            """

            # Build property filter for category
            property_filter = f"property.name.category=={category}"

            response = await aps_client.graphql_request(
                query=query,
                variables={
                    "elementGroupId": element_group_id,
                    "propertyFilter": property_filter,
                    "limit": limit
                }
            )

            data = response.get("data", {}).get("elementsByElementGroup", {})
            elements = data.get("results", [])

            result = f"Found {len(elements)} {category} elements:\n\n"
            for elem in elements[:20]:  # Show first 20
                result += f"- {elem.get('name', 'N/A')}\n"
                result += f"  ID: {elem.get('id', 'N/A')}\n"

                # Show key properties
                props = elem.get("properties", {}).get("results", [])
                for prop in props:
                    prop_name = prop.get("name", "")
                    # Show common dimension properties
                    if prop_name in ["Length", "Height", "Width", "Area", "Volume"]:
                        prop_value = prop.get("value", "N/A")
                        units = prop.get("definition", {}).get("units", {})
                        unit_name = units.get("name", "") if units else ""
                        result += f"  {prop_name}: {prop_value} {unit_name}\n".strip() + "\n"

                result += "\n"

            if len(elements) > 20:
                result += f"... and {len(elements) - 20} more {category} elements\n"

            return [TextContent(type="text", text=result)]

        # Issues API handlers
        elif name == "list_issues":
            container_id = arguments["container_id"]
            filters = arguments.get("filter", {})

            # Build query parameters
            params = {}
            for key, value in filters.items():
                params[f"filter[{key}]"] = value

            response = await aps_client.request(
                "GET",
                f"/issues/v1/containers/{container_id}/issues",
                params=params
            )

            issues = response.get("data", [])
            result = f"Found {len(issues)} issues:\n\n"

            for issue in issues:
                attributes = issue.get("attributes", {})
                result += f"- {attributes.get('title', 'N/A')}\n"
                result += f"  ID: {issue.get('id', 'N/A')}\n"
                result += f"  Status: {attributes.get('status', 'N/A')}\n"
                result += f"  Type: {attributes.get('ng_issue_type_id', 'N/A')}\n"
                result += f"  Created: {attributes.get('created_at', 'N/A')}\n"
                result += f"  Updated: {attributes.get('updated_at', 'N/A')}\n\n"

            return [TextContent(type="text", text=result)]

        elif name == "get_issue_details":
            container_id = arguments["container_id"]
            issue_id = arguments["issue_id"]

            response = await aps_client.request(
                "GET",
                f"/issues/v1/containers/{container_id}/issues/{issue_id}"
            )

            issue = response.get("data", {})
            attributes = issue.get("attributes", {})

            result = f"Issue Details:\n"
            result += f"- Title: {attributes.get('title', 'N/A')}\n"
            result += f"- ID: {issue.get('id', 'N/A')}\n"
            result += f"- Status: {attributes.get('status', 'N/A')}\n"
            result += f"- Type: {attributes.get('ng_issue_type_id', 'N/A')}\n"
            result += f"- Description: {attributes.get('description', 'N/A')}\n"
            result += f"- Created At: {attributes.get('created_at', 'N/A')}\n"
            result += f"- Created By: {attributes.get('created_by', 'N/A')}\n"
            result += f"- Updated At: {attributes.get('updated_at', 'N/A')}\n"
            result += f"- Updated By: {attributes.get('updated_by', 'N/A')}\n"
            result += f"- Assigned To: {attributes.get('assigned_to', 'N/A')}\n"
            result += f"- Due Date: {attributes.get('due_date', 'N/A')}\n"
            result += f"- Location: {attributes.get('location_description', 'N/A')}\n"

            return [TextContent(type="text", text=result)]

        elif name == "create_issue":
            container_id = arguments["container_id"]
            title = arguments["title"]
            description = arguments["description"]
            issue_type_id = arguments["issue_type_id"]
            status = arguments.get("status", "open")

            payload = {
                "data": {
                    "type": "issues",
                    "attributes": {
                        "title": title,
                        "description": description,
                        "status": status,
                        "ng_issue_type_id": issue_type_id
                    }
                }
            }

            response = await aps_client.request(
                "POST",
                f"/issues/v1/containers/{container_id}/issues",
                json=payload
            )

            issue = response.get("data", {})
            attributes = issue.get("attributes", {})

            result = f"Issue created successfully:\n"
            result += f"- ID: {issue.get('id', 'N/A')}\n"
            result += f"- Title: {attributes.get('title', 'N/A')}\n"
            result += f"- Status: {attributes.get('status', 'N/A')}\n"
            result += f"- Created At: {attributes.get('created_at', 'N/A')}\n"

            return [TextContent(type="text", text=result)]

        elif name == "update_issue":
            container_id = arguments["container_id"]
            issue_id = arguments["issue_id"]
            updates = arguments["updates"]

            payload = {
                "data": {
                    "type": "issues",
                    "id": issue_id,
                    "attributes": updates
                }
            }

            response = await aps_client.request(
                "PATCH",
                f"/issues/v1/containers/{container_id}/issues/{issue_id}",
                json=payload
            )

            issue = response.get("data", {})
            attributes = issue.get("attributes", {})

            result = f"Issue updated successfully:\n"
            result += f"- ID: {issue.get('id', 'N/A')}\n"
            result += f"- Title: {attributes.get('title', 'N/A')}\n"
            result += f"- Status: {attributes.get('status', 'N/A')}\n"
            result += f"- Updated At: {attributes.get('updated_at', 'N/A')}\n"

            return [TextContent(type="text", text=result)]

        elif name == "get_issue_comments":
            container_id = arguments["container_id"]
            issue_id = arguments["issue_id"]

            response = await aps_client.request(
                "GET",
                f"/issues/v1/containers/{container_id}/issues/{issue_id}/comments"
            )

            comments = response.get("data", [])
            result = f"Found {len(comments)} comments:\n\n"

            for comment in comments:
                attributes = comment.get("attributes", {})
                result += f"- Comment ID: {comment.get('id', 'N/A')}\n"
                result += f"  Body: {attributes.get('body', 'N/A')}\n"
                result += f"  Created At: {attributes.get('created_at', 'N/A')}\n"
                result += f"  Created By: {attributes.get('created_by', 'N/A')}\n\n"

            return [TextContent(type="text", text=result)]

        elif name == "add_issue_comment":
            container_id = arguments["container_id"]
            issue_id = arguments["issue_id"]
            comment_text = arguments["comment"]

            payload = {
                "data": {
                    "type": "comments",
                    "attributes": {
                        "body": comment_text
                    }
                }
            }

            response = await aps_client.request(
                "POST",
                f"/issues/v1/containers/{container_id}/issues/{issue_id}/comments",
                json=payload
            )

            comment = response.get("data", {})
            attributes = comment.get("attributes", {})

            result = f"Comment added successfully:\n"
            result += f"- ID: {comment.get('id', 'N/A')}\n"
            result += f"- Body: {attributes.get('body', 'N/A')}\n"
            result += f"- Created At: {attributes.get('created_at', 'N/A')}\n"

            return [TextContent(type="text", text=result)]

        # Model Derivative API handlers
        elif name == "get_manifest":
            urn = arguments["urn"]
            # Encode URN if it starts with "urn:"
            if urn.startswith("urn:"):
                urn = encode_urn(urn)

            response = await aps_client.request(
                "GET",
                f"/modelderivative/v2/designdata/{urn}/manifest"
            )

            result = f"Manifest:\n"
            result += f"- Type: {response.get('type', 'N/A')}\n"
            result += f"- URN: {response.get('urn', 'N/A')}\n"
            result += f"- Status: {response.get('status', 'N/A')}\n"
            result += f"- Progress: {response.get('progress', 'N/A')}\n"

            derivatives = response.get("derivatives", [])
            if derivatives:
                result += f"\nDerivatives ({len(derivatives)}):\n"
                for deriv in derivatives:
                    result += f"\n- Output Type: {deriv.get('outputType', 'N/A')}\n"
                    children = deriv.get("children", [])
                    if children:
                        result += f"  Children ({len(children)}):\n"
                        for child in children[:5]:  # Limit to first 5
                            result += f"  - Type: {child.get('type', 'N/A')}\n"
                            result += f"    Role: {child.get('role', 'N/A')}\n"
                            result += f"    GUID: {child.get('guid', 'N/A')}\n"

            return [TextContent(type="text", text=result)]

        elif name == "get_metadata_views":
            urn = arguments["urn"]
            if urn.startswith("urn:"):
                urn = encode_urn(urn)

            response = await aps_client.request(
                "GET",
                f"/modelderivative/v2/designdata/{urn}/metadata"
            )

            metadata = response.get("data", {}).get("metadata", [])
            result = f"Found {len(metadata)} viewable items:\n\n"

            for item in metadata:
                result += f"- Name: {item.get('name', 'N/A')}\n"
                result += f"  GUID: {item.get('guid', 'N/A')}\n"
                result += f"  Role: {item.get('role', 'N/A')}\n\n"

            return [TextContent(type="text", text=result)]

        elif name == "get_object_tree":
            urn = arguments["urn"]
            guid = arguments["guid"]

            if urn.startswith("urn:"):
                urn = encode_urn(urn)

            response = await aps_client.request(
                "GET",
                f"/modelderivative/v2/designdata/{urn}/metadata/{guid}"
            )

            def format_tree(objects, parent_id=None, level=0, max_items=50):
                """Format object tree with indentation."""
                result_text = ""
                count = 0
                for obj in objects:
                    if count >= max_items:
                        result_text += "  " * level + "... (truncated)\n"
                        break
                    if obj.get("objects"):
                        result_text += "  " * level + f"- {obj.get('name', 'N/A')} (ID: {obj.get('objectid', 'N/A')})\n"
                        result_text += format_tree(obj["objects"], obj.get("objectid"), level + 1, max_items - count)
                        count += len(obj["objects"])
                    else:
                        result_text += "  " * level + f"- {obj.get('name', 'N/A')} (ID: {obj.get('objectid', 'N/A')})\n"
                    count += 1
                return result_text

            objects = response.get("data", {}).get("objects", [])
            result = f"Object Tree (showing first 50 items):\n\n"
            result += format_tree(objects)

            return [TextContent(type="text", text=result)]

        elif name == "get_all_properties":
            urn = arguments["urn"]
            guid = arguments["guid"]

            if urn.startswith("urn:"):
                urn = encode_urn(urn)

            response = await aps_client.request(
                "GET",
                f"/modelderivative/v2/designdata/{urn}/metadata/{guid}/properties"
            )

            collection = response.get("data", {}).get("collection", [])
            result = f"Found {len(collection)} objects with properties:\n\n"

            # Show first 20 objects
            for item in collection[:20]:
                result += f"Object ID: {item.get('objectid', 'N/A')}\n"
                result += f"  Name: {item.get('name', 'N/A')}\n"

                properties = item.get("properties", {})
                if properties:
                    result += "  Properties:\n"
                    # Show first 10 properties
                    for key, value in list(properties.items())[:10]:
                        result += f"    - {key}: {value}\n"

                result += "\n"

            if len(collection) > 20:
                result += f"... and {len(collection) - 20} more objects\n"

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
