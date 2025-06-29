#!/usr/bin/env python3
"""
Generate OpenAPI (Swagger) documentation for VENDORA FastAPI application
"""

import json
import sys
import os

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.fastapi_main import app


def generate_openapi_json():
    """Generate OpenAPI JSON schema from FastAPI app"""
    
    # Get the OpenAPI schema
    openapi_schema = app.openapi()
    
    # Add additional information
    openapi_schema["info"]["description"] = """
    # VENDORA API
    
    The VENDORA API provides AI-powered analytics for automotive dealerships using a hierarchical multi-agent system.
    
    ## Authentication
    
    All endpoints (except `/health`) require Firebase authentication. Include your Firebase ID token in the Authorization header:
    
    ```
    Authorization: Bearer YOUR_FIREBASE_ID_TOKEN
    ```
    
    ## Key Features
    
    - **Hierarchical Agent System**: L1 Orchestrator → L2 Specialists → L3 Master Analyst
    - **Quality Assurance**: Every insight is validated before delivery
    - **Real-time Analytics**: Process complex queries about sales, inventory, and performance
    - **Role-based Access**: Control access with custom claims and roles
    - **Dealership Isolation**: Users can only access their assigned dealership data
    
    ## Rate Limits
    
    - Default: 100 requests/minute per user
    - Query endpoint: 20 requests/minute per user
    - Metrics endpoint: 10 requests/minute per user (admin/analyst only)
    """
    
    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "FirebaseAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Firebase ID token obtained from Firebase Authentication"
        }
    }
    
    # Add global security (except for health endpoint)
    openapi_schema["security"] = [{"FirebaseAuth": []}]
    
    # Remove security from health endpoint
    if "paths" in openapi_schema and "/health" in openapi_schema["paths"]:
        if "get" in openapi_schema["paths"]["/health"]:
            openapi_schema["paths"]["/health"]["get"]["security"] = []
    
    # Add tags descriptions
    openapi_schema["tags"] = [
        {
            "name": "System",
            "description": "System health and status endpoints"
        },
        {
            "name": "VENDORA API",
            "description": "Core analytical endpoints for query processing and insights"
        },
        {
            "name": "Authentication",
            "description": "User authentication and profile management"
        },
        {
            "name": "Webhooks",
            "description": "External webhook integrations (Mailgun)"
        }
    ]
    
    # Add servers
    openapi_schema["servers"] = [
        {
            "url": "http://localhost:8000",
            "description": "Local development server"
        },
        {
            "url": "https://api.vendora.com",
            "description": "Production server"
        }
    ]
    
    # Write to file
    with open("openapi.json", "w") as f:
        json.dump(openapi_schema, f, indent=2)
    
    print("✅ OpenAPI schema generated: openapi.json")
    print(f"📄 Total endpoints: {sum(len(methods) for methods in openapi_schema['paths'].values())}")
    
    # Also generate a simplified version for Postman
    generate_postman_collection(openapi_schema)


def generate_postman_collection(openapi_schema):
    """Generate a Postman collection from OpenAPI schema"""
    
    collection = {
        "info": {
            "name": "VENDORA API",
            "description": openapi_schema["info"]["description"],
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
        },
        "auth": {
            "type": "bearer",
            "bearer": [
                {
                    "key": "token",
                    "value": "{{firebase_token}}",
                    "type": "string"
                }
            ]
        },
        "variable": [
            {
                "key": "base_url",
                "value": "http://localhost:8000",
                "type": "string"
            },
            {
                "key": "firebase_token",
                "value": "",
                "type": "string"
            },
            {
                "key": "dealership_id",
                "value": "dealer_123",
                "type": "string"
            }
        ],
        "item": []
    }
    
    # Group endpoints by tags
    tag_folders = {}
    
    for path, methods in openapi_schema["paths"].items():
        for method, details in methods.items():
            tags = details.get("tags", ["Other"])
            tag = tags[0]
            
            if tag not in tag_folders:
                tag_folders[tag] = {
                    "name": tag,
                    "item": []
                }
            
            # Create request item
            request_item = {
                "name": details.get("summary", f"{method.upper()} {path}"),
                "request": {
                    "method": method.upper(),
                    "header": [],
                    "url": {
                        "raw": "{{base_url}}" + path,
                        "host": ["{{base_url}}"],
                        "path": path.strip("/").split("/")
                    },
                    "description": details.get("description", "")
                }
            }
            
            # Add body for POST/PUT requests
            if method in ["post", "put", "patch"] and "requestBody" in details:
                content = details["requestBody"].get("content", {})
                if "application/json" in content:
                    schema = content["application/json"].get("schema", {})
                    # Get example from schema
                    example = None
                    if "$ref" in schema:
                        # Extract model name and get its example
                        model_name = schema["$ref"].split("/")[-1]
                        model_schema = openapi_schema["components"]["schemas"].get(model_name, {})
                        example = model_schema.get("example")
                    
                    request_item["request"]["body"] = {
                        "mode": "raw",
                        "raw": json.dumps(example if example else {}, indent=2),
                        "options": {
                            "raw": {
                                "language": "json"
                            }
                        }
                    }
            
            # Add to appropriate folder
            tag_folders[tag]["item"].append(request_item)
    
    # Add folders to collection
    collection["item"] = list(tag_folders.values())
    
    # Write Postman collection
    with open("vendora_api_postman.json", "w") as f:
        json.dump(collection, f, indent=2)
    
    print("✅ Postman collection generated: vendora_api_postman.json")


if __name__ == "__main__":
    generate_openapi_json()