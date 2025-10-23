import os
import glob
from dotenv import load_dotenv
from elasticsearch import Elasticsearch, helpers
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from tqdm import tqdm # For a nice progress bar

# --- Configuration ---
load_dotenv()
ES_ENDPOINT_URL = os.environ["ES_ENDPOINT_URL"]
ES_API_KEY = os.environ["ES_API_KEY"]
ELSER_MODEL = ".elser_model_2_linux-x86_64"

# Maps your doc folders to your Elastic indexes
PLATFORM_INDEX_MAP = {
    "aws": "aws",
    "gcp": "gcp",
    "azure": "azure"
}

# --- 1. Define the ELSER Ingest Pipeline ---
def create_ingest_pipeline(client: Elasticsearch):
    """
    Creates an Elasticsearch ingest pipeline that uses the ELSER
    model to create a sparse vector from the 'content' field.
    """
    pipeline_id = "elser-ingest-pipeline"
    try:
        client.ingest.put_pipeline(
            id=pipeline_id,
            description="A pipeline to generate ELSER sparse vectors from 'content'",
            processors=[
                {
                    "inference": {
                        "model_id": ELSER_MODEL,
                        "target_field": "content_vector",
                        "field_map": {
                            "content": "text_field"
                        },
                        "inference_config": {
                            "text_expansion": {}
                        },
                        "on_failure": [
                            {
                                "set": {
                                    "field": "ingest.failure",
                                    "value": "{{ _ingest.on_failure_message }}"
                                }
                            }
                        ]
                    }
                }
            ]
        )
        print(f"Ingest pipeline '{pipeline_id}' created successfully.")
        return pipeline_id
    except Exception as e:
        if "resource_already_exists_exception" in str(e):
            print(f"Ingest pipeline '{pipeline_id}' already exists.")
            return pipeline_id
        else:
            print(f"Failed to create ingest pipeline: {e}")
            raise

# --- 2. Define the Index Mapping ---
def create_index_with_mapping(client: Elasticsearch, index_name: str, pipeline_id: str):
    """
    Creates an index with the correct mapping for ELSER and
    sets it to use the default ingest pipeline.
    """
    mapping = {
        "properties": {
            "content": {
                "type": "text",
                "fields": {
                    "keyword": { "type": "keyword", "ignore_above": 256 }
                }
            },
            # This is where the ELSER vector will be stored
            "content_vector": {
                "type": "sparse_vector"
            },
            "source_title": { "type": "keyword" },
            "page_number": { "type": "integer" }
        }
    }
    
    try:
        if not client.indices.exists(index=index_name):
            client.indices.create(
                index=index_name,
                mappings=mapping,
                settings={
                    # This tells the index to use our pipeline on ALL new docs
                    "index.default_pipeline": pipeline_id 
                }
            )
            print(f"Index '{index_name}' created with correct mapping.")
        else:
            print(f"Index '{index_name}' already exists.")
    except Exception as e:
        print(f"Failed to create index '{index_name}': {e}")
        raise

# --- 3. Chunk Documents using LangChain ---
def process_and_chunk_pdf(file_path: str) -> list[dict]:
    """
    Loads a PDF, splits it into chunks, and formats for Elasticsearch.
    """
    print(f"\nProcessing file: {file_path}")
    loader = PyPDFLoader(file_path)
    documents = loader.load()
    
    # This splitter is good at keeping paragraphs and sections together
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, # Max characters per chunk
        chunk_overlap=100  # Overlap between chunks
    )
    chunks = text_splitter.split_documents(documents)
    
    chunk_docs = []
    for i, doc in enumerate(chunks):
        # Create the JSON document that will be sent to Elasticsearch
        chunk_docs.append({
            "content": doc.page_content,
            "source_title": os.path.basename(file_path),
            "page_number": doc.metadata.get("page", 0) + 1
        })
    print(f"File split into {len(chunk_docs)} chunks.")
    return chunk_docs

# --- 4. Main Ingestion Function ---
def main_ingest():
    try:
        # --- MODIFIED ---
        # Get the URL instead of the Cloud ID
        ES_ENDPOINT_URL = os.environ["ES_ENDPOINT_URL"]
        
        # Connect using the 'hosts' parameter
        client = Elasticsearch(
            hosts=[ES_ENDPOINT_URL], 
            api_key=ES_API_KEY
        )
        # --- END MODIFIED ---
        
        client.info() # Test connection
        print("Connected to Elasticsearch successfully!")
    except Exception as e:
        print(f"Failed to connect to Elasticsearch: {e}")
        return

    # First, create the pipeline that all indexes will use
    pipeline_id = create_ingest_pipeline(client)

    # Now, loop through each platform (aws, gcp, azure)
    for platform, index_name in PLATFORM_INDEX_MAP.items():
        print(f"\n--- Processing platform: {platform.upper()} (Index: {index_name}) ---")
        
        # Create the index with the correct mapping
        create_index_with_mapping(client, index_name, pipeline_id)
        
        doc_folder_path = os.path.join("docs", platform)
        pdf_files = glob.glob(os.path.join(doc_folder_path, "*.pdf"))
        
        if not pdf_files:
            print(f"No PDF files found in {doc_folder_path}. Skipping.")
            continue

        all_chunks = []
        for file_path in pdf_files:
            chunks = process_and_chunk_pdf(file_path)
            all_chunks.extend(chunks)

        if not all_chunks:
            print(f"No chunks generated for {platform}. Skipping bulk ingest.")
            continue
        
        # Prepare actions for bulk helper
        actions = [
            {
                "_index": index_name,
                "_source": chunk
            }
            for chunk in all_chunks
        ]

        # Use helpers.bulk for efficient uploading
        print(f"Uploading {len(actions)} chunks to '{index_name}'...")
        try:
            success, failed = helpers.bulk(client, actions, raise_on_error=False)
            print(f"Bulk upload complete. Success: {success}, Failed: {failed}")
            if failed:
                print(f"Failed documents: {failed}")
        except Exception as e:
            print(f"Bulk upload failed: {e}")

    print("\n--- Ingestion process finished. ---")


if __name__ == "__main__":
    main_ingest()