from typing import Dict, List
from notion_client import Client
from pprint import pprint

def extract_plain_text_with_urls(blocks):
    """
    Convert Notion blocks into plain text content, including any URLs.

    Args:
        blocks (list): A list of Notion blocks.

    Returns:
        str: Plain text representation of the blocks' content, including URLs.
    """
    plain_text = []

    for block in blocks:
        block_type = block.get("type")
        has_children = block.get("has_children", False)
        block_content = []

        # Extract text content based on block type
        if block_type in ["paragraph", "heading_1", "heading_2", "heading_3", "numbered_list_item", "bulleted_list_item"]:
            rich_texts = block.get(block_type, {}).get("rich_text", [])
            for text in rich_texts:
                content = text.get("plain_text", "")
                url = text.get("href")  # Get the URL if present
                if url:
                    content += f" ({url})"  # Append the URL in parentheses
                block_content.append(content)

        # Join the block content into a single string
        if block_content:
            plain_text.append(" ".join(block_content))

        # Divider or other non-textual blocks
        elif block_type == "divider":
            plain_text.append("---")  # Add a horizontal line

        elif block_type == "quote":
            rich_texts = block.get("quote", {}).get("rich_text", [])
            quote_content = []
            for text in rich_texts:
                content = text.get("plain_text", "")
                url = text.get("href")
                if url:
                    content += f" ({url})"
                quote_content.append(content)
            plain_text.append(f"> {' '.join(quote_content)}")

        # Process child blocks if present
        if has_children:
            child_blocks = notion.blocks.children.list(block_id=block["id"]).get("results", [])
            child_content = extract_plain_text_with_urls(child_blocks)
            plain_text.append(child_content)

        # Add a blank line to separate blocks
        plain_text.append("")

    # Remove the trailing blank line if present
    return "\n".join(plain_text).strip()


page_id = ""  # Replace with your actual page ID
notion_secret = ""
notion = Client(auth=notion_secret)

docData = []

try:
    # Retrieve the blocks of the page
    response = notion.blocks.children.list(block_id=page_id)
    
    # Iterate through the blocks
    for block in response.get("results", []):
        # Check if the block type is 'child_database'
        if block["type"] == "child_database":
            database_id = block["id"]  # Get the ID of the child database
            
            # Retrieve all entries of the child database
            db_response = notion.databases.query(database_id=database_id)
            # print(f"Entries in child database ({database_id}):")
            
            # Iterate through each child in the database
            for child in db_response.get("results", []):
                # Check if the child is a page
                pageTitle = child['properties']['Name']['title'][0]['plain_text']
                if child["object"] == "page":
                    # Retrieve the page content
                    page_content = notion.blocks.children.list(block_id=child["id"])

                    print(f"Content of page ({child['id']}):")

                    # Extract plain text with URLs
                    plain_text_with_urls = extract_plain_text_with_urls(page_content["results"])
                    # print(plain_text_with_urls)

                    docData.append({
                        "Title": pageTitle,
                        "Description": plain_text_with_urls
                    })
                    # pprint(page_content)
                else:
                    print(f"Child is not a page: {child['id']}")
        else:
            print("Block is not a child database:")
            pprint(block)

except Exception as e:
    print(f"An error occurred: {e}")

print(docData)
