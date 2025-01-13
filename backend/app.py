import json
from flask import Flask, request, Response, jsonify, stream_with_context
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import marqo
from ai_chat import answer
from typing import List
from knowledge_store import MarqoKnowledgeStore
import document_processors
from document_processors import (
    simple_chunker,
    simple_denewliner,
    sentence_chunker,
    sentence_pair_chunker,
)
from pprint import pprint
from notion_client import Client

# Configuration
INDEX_NAME = "knowledge-management-8"
MARQO_CLIENT_URL = "http://localhost:8882"
KNOWLEDGE_ATTR = "knowledge"
CHUNK_SIZE = 512

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Initialize Marqo Client and Knowledge Store
CLIENT = marqo.Client(MARQO_CLIENT_URL)
document_processors.CHUNK_SIZE = CHUNK_SIZE


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

MKS = MarqoKnowledgeStore(
    CLIENT,
    INDEX_NAME,
    document_chunker=sentence_pair_chunker,
    document_cleaner=simple_denewliner,
)


MKS.reset_index()


########

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

########

# Add documents to the index
MKS.add_documents_from_list_of_dicts(docData)

def get_document_text(url: str) -> str:
    """Fetch the text content from a webpage given its URL."""
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    return soup.get_text()

@app.route("/getKnowledge", methods=["POST"])
def get_knowledge():
    """Endpoint to retrieve knowledge based on a query."""
    print(f"Incoming request: {request.method} {request.url}")
    """Incoming request: {request.method} {request.url}"""

    if request.mimetype == 'text/plain':
        try:
            # Manually decode and parse the JSON from the raw data
            data = json.loads(request.data.decode('utf-8'))
            # data = request.get_json()
            q: str = data.get("q")
            limit: int = data.get("limit", 5)
            return Response(
                stream_with_context(answer(q, MKS, limit)),
                mimetype="text/event-stream")
        except json.JSONDecodeError:
            return {"error": "Invalid payload when doing stuff text/plain"}, 400    
    elif request.mimetype == 'application/json':
        try:
                # Manually decode and parse the JSON from the raw data
                # data = json.loads(request.data.decode('utf-8'))
                data = request.get_json()
                q: str = data.get("q")
                limit: int = data.get("limit", 5)
                return Response(
                    stream_with_context(answer(q, MKS, limit)),
                    mimetype="text/event-stream",)
        except json.JSONDecodeError:
            return {"error": "Invalid payload when doing stuff json"}, 400    

@app.route("/addKnowledge", methods=["POST"])
def add_knowledge():
    """Endpoint to add a document to the knowledge index."""
    data = request.get_json()
    document = data.get("document")
    if document:
        MKS.add_document(document)
        return {"message": "Knowledge added successfully"}
    return {"error": "No document provided"}, 400

@app.route("/addWebpage", methods=["POST"])
def add_webpage():
    """Endpoint to add a webpage's content to the knowledge index."""
    data = request.get_json()
    url = data.get("URL")
    if url:
        document = get_document_text(url)
        MKS.add_document(document)
        return {"message": "Knowledge added successfully"}
    return {"error": "No URL provided"}, 400

if __name__ == "__main__":
    app.run(debug=True)
