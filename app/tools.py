import os
import httpx
from app.ascii_diagrammer import generate_ascii_diagram
from elasticsearch import Elasticsearch
# from google.adk import tool
from pydantic import BaseModel, Field

# --- Elasticsearch Client Setup ---
# Initialize the Elasticsearch client using environment variables

try:
    
    ES_ENDPOINT_URL = os.environ["ES_ENDPOINT_URL"]
    ES_API_KEY = os.environ["ES_API_KEY"]

    # Connect using the 'hosts' parameter
    es_client = Elasticsearch(
        hosts=[ES_ENDPOINT_URL],
        api_key=ES_API_KEY
    )
    
    print("Elasticsearch client initialized.")
except KeyError:
    print("Elasticsearch environment variables not set. ES tools will fail.")
    es_client = None

# --- HTTP Client for MCP/Cost APIs ---
http_client = httpx.AsyncClient(timeout=30.0)


# This map defines which index to use for which platform.
PLATFORM_INDEX_MAP = {
    "aws": "aws",
    "gcp": "gcp",
    "azure": "azure"
}


async def query_best_practices(
    target_platform: str,
    requirement: str
) -> str:
    """
    Queries the internal Elasticsearch knowledge base for security
    guidelines and architecture best practices.
    
    Args:
        target_platform: The cloud provider (e.g., "aws", "gcp", "azure").
        requirement: The user's high-level goal (e.g., "secure database").

    Returns:
        A string containing the retrieved best practice documents.
    """
    if not es_client:
        return "Error: Elasticsearch client is not configured."

    index_name = PLATFORM_INDEX_MAP.get(target_platform.lower())
    
    if not index_name:
        return (
            f"Error: Invalid target platform '{target_platform}'. "
            f"Valid platforms are: {list(PLATFORM_INDEX_MAP.keys())}"
        )

    print(f"Querying RAG for: {target_platform} (Index: {index_name}) - {requirement}")

    try:
        
        # We are using ELSER's `semantic_search` (which uses the `text_expansion` query)
        # to find documents that are semantically related to the 'requirement'.
        response = es_client.search(
            index=index_name,
            query={
                "text_expansion": {
                "content_vector": {
                    "model_id": ".elser_model_2_linux-x86_64",
                    "model_text": requirement
                  }
                }
            },
            size=5
        )
        
        
        hits = response.body['hits']['hits']
        if not hits:
            return "No specific best practices found. Proceeding with general knowledge."

        # Format results for the LLM
        context = "--- RETRIEVED BEST PRACTICES ---\n"
        for i, hit in enumerate(hits):
            # We now return the 'content' of the chunk
            context += f"Doc {i+1} (Source: {hit['_source'].get('source_title', 'N/A')}, Page: {hit['_source'].get('page_number', 'N/A')}):\n"
            context += f"{hit['_source'].get('content', 'No content')}\n---\n"
        
        print("RAG query successful. Returning context.")
        return context

    except Exception as e:
        print(f"Error querying Elasticsearch: {e}")
        return f"Error connecting to knowledge base: {e}"

