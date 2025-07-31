#!/usr/bin/env python3
"""
Create three Notion databases for project management:
1. Product Roadmap (board view)
2. Feature Requests (table view) 
3. Dev Cycles (board view)
"""

import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def create_notion_database(name, properties, parent_page_id, notion_token, is_inline=False):
    """Create a Notion database with the given properties."""
    url = "https://api.notion.com/v1/databases"
    
    headers = {
        "Authorization": f"Bearer {notion_token}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    payload = {
        "parent": {
            "type": "page_id",
            "page_id": parent_page_id
        },
        "title": [
            {
                "type": "text",
                "text": {
                    "content": name
                }
            }
        ],
        "properties": properties,
        "is_inline": is_inline
    }
    
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Created '{name}' database with ID: {data['id']}")
        return data['id']
    else:
        print(f"❌ Failed to create '{name}' database:")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        return None


def create_product_roadmap_db(parent_page_id, notion_token):
    """Create Product Roadmap database with board view."""
    properties = {
        "Feature Name": {
            "title": {}
        },
        "Status": {
            "select": {
                "options": [
                    {"name": "Backlog", "color": "gray"},
                    {"name": "In Progress", "color": "yellow"},
                    {"name": "In Review", "color": "orange"},
                    {"name": "Done", "color": "green"},
                    {"name": "Cancelled", "color": "red"}
                ]
            }
        },
        "Priority": {
            "select": {
                "options": [
                    {"name": "High", "color": "red"},
                    {"name": "Medium", "color": "yellow"},
                    {"name": "Low", "color": "green"}
                ]
            }
        },
        "GitHub PR": {
            "url": {}
        },
        "Owner": {
            "people": {}
        },
        "Target Quarter": {
            "select": {
                "options": [
                    {"name": "Q1 2025", "color": "blue"},
                    {"name": "Q2 2025", "color": "green"},
                    {"name": "Q3 2025", "color": "yellow"},
                    {"name": "Q4 2025", "color": "orange"},
                    {"name": "Q1 2026", "color": "purple"}
                ]
            }
        }
    }
    
    return create_notion_database("Product Roadmap", properties, parent_page_id, notion_token)


def create_feature_requests_db(parent_page_id, notion_token, roadmap_db_id=None):
    """Create Feature Requests database with table view."""
    properties = {
        "Request": {
            "title": {}
        },
        "Requester": {
            "people": {}
        },
        "Impact": {
            "select": {
                "options": [
                    {"name": "High", "color": "red"},
                    {"name": "Medium", "color": "yellow"},
                    {"name": "Low", "color": "green"}
                ]
            }
        },
        "Status": {
            "select": {
                "options": [
                    {"name": "New", "color": "gray"},
                    {"name": "Under Review", "color": "yellow"},
                    {"name": "Approved", "color": "green"},
                    {"name": "In Roadmap", "color": "blue"},
                    {"name": "Rejected", "color": "red"}
                ]
            }
        }
    }
    
    # Add relation to roadmap if provided
    if roadmap_db_id:
        properties["Roadmap Link"] = {
            "relation": {
                "database_id": roadmap_db_id,
                "single_property": {}
            }
        }
    
    return create_notion_database("Feature Requests", properties, parent_page_id, notion_token, is_inline=True)


def create_dev_cycles_db(parent_page_id, notion_token):
    """Create Dev Cycles database with board view grouped by Sprint."""
    properties = {
        "Task": {
            "title": {}
        },
        "Sprint": {
            "select": {
                "options": [
                    {"name": "Sprint 1", "color": "blue"},
                    {"name": "Sprint 2", "color": "green"},
                    {"name": "Sprint 3", "color": "yellow"},
                    {"name": "Sprint 4", "color": "orange"},
                    {"name": "Sprint 5", "color": "purple"},
                    {"name": "Sprint 6", "color": "pink"}
                ]
            }
        },
        "GitHub PR": {
            "url": {}
        },
        "Status": {
            "select": {
                "options": [
                    {"name": "To Do", "color": "gray"},
                    {"name": "In Progress", "color": "yellow"},
                    {"name": "In Review", "color": "orange"},
                    {"name": "Done", "color": "green"},
                    {"name": "Blocked", "color": "red"}
                ]
            }
        },
        "Points": {
            "number": {
                "format": "number"
            }
        }
    }
    
    return create_notion_database("Dev Cycles", properties, parent_page_id, notion_token)


def main():
    """Main function to create all databases."""
    # Get environment variables
    notion_token = os.getenv("NOTION_TOKEN")
    parent_page_id = os.getenv("PARENT_PAGE_ID")
    
    if not notion_token:
        print("❌ Error: NOTION_TOKEN environment variable not set")
        return
    
    if not parent_page_id:
        print("❌ Error: PARENT_PAGE_ID environment variable not set")
        return
    
    print(f"🚀 Creating databases under parent page: {parent_page_id}")
    print()
    
    # Create Product Roadmap database first
    roadmap_db_id = create_product_roadmap_db(parent_page_id, notion_token)
    
    # Create Feature Requests database with relation to roadmap
    feature_requests_db_id = create_feature_requests_db(parent_page_id, notion_token, roadmap_db_id)
    
    # Create Dev Cycles database
    dev_cycles_db_id = create_dev_cycles_db(parent_page_id, notion_token)
    
    print()
    print("🎉 Database creation complete!")
    print()
    print("Database IDs:")
    if roadmap_db_id:
        print(f"  Product Roadmap: {roadmap_db_id}")
    if feature_requests_db_id:
        print(f"  Feature Requests: {feature_requests_db_id}")
    if dev_cycles_db_id:
        print(f"  Dev Cycles: {dev_cycles_db_id}")


if __name__ == "__main__":
    main()
