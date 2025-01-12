import uuid
import json
from marqo import Client
import pprint

def create_random_index_if_exists(base_index_name):
    # Initialize Marqo client
    client = Client(url='http://localhost:8882')  # Replace with your Marqo server URL

    try:
        # Check if the index already exists
        client.index(base_index_name).get_stats()
        print(f"Index '{base_index_name}' already exists.")

        # Generate a new unique name
        unique_index_name = f"{base_index_name}-{uuid.uuid4().hex[:8]}"
        client.create_index(unique_index_name, model="hf/e5-base-v2")
        print(f"Created a new unique index: '{unique_index_name}'.")
        return unique_index_name

    except Exception:
        # If the index doesn't exist, create it
        print(f"Index '{base_index_name}' does not exist. Creating it now.")
        client.create_index(base_index_name, model="hf/e5-base-v2")
        return base_index_name

def load_documents_to_index(input_file, index_name):
    # Initialize Marqo client
    client = Client(url='http://localhost:8882')  # Replace with your Marqo server URL

    # Load documents from the file
    with open(input_file, 'r', encoding='utf-8') as f:
        documents = json.load(f)
    
    # Specify tensor fields based on your data
    # Does not include "_id" field in document because that is not meant to be vectorized
    tensor_fields = ["Title", "Description"]  # Fields to vectorize for search

    # Add documents to the index
    result = client.index(index_name).add_documents(documents, tensor_fields=tensor_fields)

    if 'errors' in result and result['errors']:
        print("Errors detected:")
        print(result)
    else:
        print("Documents added successfully.")
        print(f"Loaded {len(documents)} documents into the index '{index_name}'")


index_name = create_random_index_if_exists("my-test-index")
output_file = "/home/ai-makina/Documents/GitHub/RAG_NOTION_LLAMA/marqo/code_samples/index_documents.json"  # Replace with your file name

# Load documents back into the index
load_documents_to_index(output_file, index_name)