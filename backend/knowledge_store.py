from typing import Union, Dict, List, Callable
import marqo

def default_chunker(document: str) -> List[Dict[str, str]]:
    """Default chunker that returns the whole document as a single chunk.

    Args:
        document (str): The input document.

    Returns:
        List[Dict[str, str]]: A list containing a single chunk with the whole document.
    """
    return [{"text": document}]

class MarqoKnowledgeStore:
    def __init__(
        self,
        client: marqo.Client,
        index_name: str,
        document_chunker: Callable[[str], List[Dict[str, str]]] = default_chunker,
        document_cleaner: Union[Callable[[str], str], None] = None,
    ) -> None:
        """Initialize the MarqoKnowledgeStore with a client, index name, and optional chunker and cleaner.

        Args:
            client (marqo.Client): The Marqo client.
            index_name (str): The name of the index.
            document_chunker (Callable[[str], List[Dict[str, str]]], optional): Function to chunk documents. Defaults to default_chunker.
            document_cleaner (Union[Callable[[str], str], None], optional): Function to clean documents. Defaults to None.
        """
        self._client = client
        self._index_name = index_name
        self._document_chunker = document_chunker
        self._document_cleaner = document_cleaner

        self._index_settings = {
            "model": "hf/all_datasets_v4_MiniLM-L6",
            "text_preprocessing": {
                "split_length": 2,
                "split_overlap": 0,
                "split_method": "sentence"
            }
        }

        self.reset_index()

    def query_for_content(
        self, query: Union[str, Dict[str, float]], content_var: str, limit: int = 5
    ) -> List[str]:
        """Query the knowledge store for content based on a query.

        Args:
            query (Union[str, Dict[str, float]]): The query string or dictionary.
            content_var (str): The key to extract content from the response.
            limit (int, optional): The maximum number of results to return. Defaults to 5.

        Returns:
            List[str]: A list of content strings that match the query.
        """
        relevance_score = 0.61

        resp = self._client.index(self._index_name).search(q=query, limit=limit)
        for res in resp["hits"]:
            if res["_score"] > relevance_score:
                # Print the response details
                for key, value in res.items():
                    print(f"{key}: {value}")
                print("Score:", res["_score"])

        # Collect knowledge based on content_var or fallback fields
        # Description and Title come from the Document title I used
        knowledge = []
        for res in resp["hits"]:
            if res["_score"] > relevance_score:
                if content_var in res:
                    knowledge.append(res[content_var])
                elif "text" in res:
                    knowledge.append(res["text"])
                elif "Description" in res:
                    knowledge.append(res["Description"])
                elif "Title" in res:
                    knowledge.append(res["Title"])

        return knowledge


    def add_document(self, document: str) -> None:
        print("Adding documents")
        """Add a document to the knowledge store.

        Args:
            document (str): The document to add.
        """
        if self._document_cleaner is not None:
            document = self._document_cleaner(document)
        chunks = self._document_chunker(document)
        for chunk in chunks:
            chunk['tensor_fields'] = ['text']  # Explicitly set tensor fields
        self._client.index(self._index_name).add_documents(chunks, tensor_fields=['text'])

    def add_documents_from_list_of_dicts(self, documents: List[Dict[str, str]]) -> None:
        print("Adding documents")
        """Add documents to knowledge store."""
        if self._document_cleaner is not None:
            # Apply document cleaner to each string field in each document
            for doc in documents:
                for key, value in doc.items():
                    if isinstance(value, str):  # Only clean string fields
                        doc[key] = self._document_cleaner(value)
        
        # Create chunks while keeping original fields in each chunk
        chunks = []
        for doc in documents:
            description_chunks = self._document_chunker(doc["Description"])
            for chunk in description_chunks:
                # Each chunk will only contain the original fields
                # Update code so that it adds all properties of "doc" and not hardcode it
                chunks.append({
                    "Title": doc["Title"],
                    "Description": doc["Description"],
                    **({"_id": doc["_id"]} if "_id" in doc else {})
                })

        
        # Add documents to the knowledge store
        result = self._client.index(self._index_name).add_documents(chunks, tensor_fields=['Description', 'Title'])

        if 'errors' in result and result['errors']:
            print("Errors detected:")
            print(result)
        else:
            print("Documents added successfully.")
            print(f"Loaded docs into index'")

    def reset_index(self) -> None:
        """Reset the index by deleting it if it exists and creating a new one.

        This method will attempt to delete the existing index. If the index is not found,
        it will print a message and create a new one. If an error occurs during deletion
        or creation, it will print the error message.
        """
        try:
            self._client.index(self._index_name).delete()
        except marqo.errors.MarqoWebError:
            print(f"Index '{self._index_name}' not found. Creating a new one.")
        except Exception as e:
            print(f"Error deleting index '{self._index_name}': {e}")

        try:
            self._client.create_index(index_name=self._index_name, **self._index_settings)
        except marqo.errors.IndexAlreadyExistsError:
            print(f"Index '{self._index_name}' already exists. Updating settings.")
            self._client.index(self._index_name).settings(**self._index_settings)
        except Exception as e:
            print(f"Error creating index '{self._index_name}': {e}")
