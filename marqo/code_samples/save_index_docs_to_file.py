import json
from marqo import Client

# To retrieve all documents from a Marqo index, you can utilize the search method with a wildcard query ("*"), which matches all documents.
# Since Marqo's search method supports pagination, you'll need to handle this to ensure you retrieve all documents, 
# especially if the index contains a large number of entries.
def save_all_documents(index_name, output_file):
    # Initialize Marqo client
    client = Client(url='http://localhost:8882')  # Replace with your Marqo server URL

    # Initialize variables for pagination
    all_documents = []
    limit = 100  # Number of documents to retrieve per request
    offset = 0   # Starting point for each batch

    while True:
        # https://docs.marqo.ai/latest/reference/api/search/search/#body
        # Retrieve a batch of documents
        response = client.index(index_name).search(
            q="*",
            limit=limit,
            offset=offset
        )

        # Extract documents from the response
        documents = response.get('hits', [])

        # Remove _highlights and _score from each document
        for doc in documents:
            doc.pop('_highlights', None)
            doc.pop('_score', None)

        all_documents.extend(documents)

        # Check if we've retrieved all documents
        if len(documents) < limit:
            break

        # Update offset for the next batch
        offset += limit

    # Save all documents to a file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_documents, f, indent=4, ensure_ascii=False)

    print(f"Saved {len(all_documents)} documents to {output_file}")

# Usage
index_name = "my-third-index"  # Replace with your index name
output_file = "index_documents.json"  # Desired output file name
save_all_documents(index_name, output_file)
