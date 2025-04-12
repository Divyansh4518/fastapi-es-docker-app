import os
import uuid
import time
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from elasticsearch import Elasticsearch, exceptions as es_exceptions
from dotenv import load_dotenv

# Load environment variables (optional, good practice)
load_dotenv()

# Get Elasticsearch host from environment variable or use default
ELASTICSEARCH_HOST = os.getenv("ELASTICSEARCH_HOST", "http://elasticsearch-service:9567") # Use container name 'elasticsearch-service'
INDEX_NAME = "wikipedia_india"

app = FastAPI()

# --- Elasticsearch Connection ---
es_client = None

def get_es_client():
    """Initializes and returns the Elasticsearch client, retrying on connection errors."""
    global es_client
    if es_client and es_client.ping():
        return es_client

    print(f"Attempting to connect to Elasticsearch at {ELASTICSEARCH_HOST}...")
    retries = 5
    delay = 5
    for i in range(retries):
        try:
            client = Elasticsearch(
                [ELASTICSEARCH_HOST],
                basic_auth=('elastic', 'changeme') if "https://elastic" in ELASTICSEARCH_HOST else None, # Add basic auth if needed for future ES versions
                verify_certs=False if "https://" in ELASTICSEARCH_HOST else True, # Disable cert verification if using https without proper certs (dev only)
                timeout=30, max_retries=3, retry_on_timeout=True
            )
            if client.ping():
                print("Successfully connected to Elasticsearch.")
                es_client = client
                # Ensure index exists (optional, can be done manually or here)
                # ensure_index_exists(es_client)
                return es_client
            else:
                print(f"Ping failed. Retrying ({i+1}/{retries})...")
        except es_exceptions.ConnectionError as e:
            print(f"Connection Error: {e}. Retrying ({i+1}/{retries})...")
        except Exception as e:
            print(f"An unexpected error occurred during ES connection: {e}")

        time.sleep(delay)

    raise HTTPException(status_code=503, detail="Could not connect to Elasticsearch after multiple retries.")

# --- Pydantic Models for Request Bodies ---
class SearchRequest(BaseModel):
    query: str

class InsertRequest(BaseModel):
    text: str

# --- API Endpoints ---
@app.on_event("startup")
async def startup_event():
    """Attempt to connect to Elasticsearch on startup."""
    get_es_client() # Initialize connection

@app.post("/search")
async def search_documents(request: SearchRequest):
    """Performs a match search on the 'text' field."""
    client = get_es_client()
    if not client:
         raise HTTPException(status_code=503, detail="Elasticsearch not available")

    try:
        # Use match query for full-text search
        search_body = {
            "query": {
                "match": {
                    "text": request.query
                }
            },
            "size": 1 # Get only the top hit as requested by "best score"
        }
        response = client.search(index=INDEX_NAME, body=search_body)

        hits = response.get("hits", {}).get("hits", [])
        if not hits:
            return {"message": "No matching documents found.", "best_hit": None}

        # Return the document with the highest score
        best_hit = hits[0]['_source']
        best_score = hits[0]['_score']
        return {"message": "Found document(s)", "best_hit": best_hit, "score": best_score}

    except es_exceptions.NotFoundError:
         raise HTTPException(status_code=404, detail=f"Index '{INDEX_NAME}' not found.")
    except es_exceptions.TransportError as e:
         # Log the detailed error for debugging
         print(f"Elasticsearch TransportError: {e.info}")
         raise HTTPException(status_code=500, detail=f"Elasticsearch search error: {e.error}")
    except Exception as e:
         # Log the detailed error for debugging
         import traceback
         print(f"Unexpected error during search: {traceback.format_exc()}")
         raise HTTPException(status_code=500, detail=f"An internal server error occurred: {str(e)}")


@app.post("/insert")
async def insert_document(request: InsertRequest):
    """Inserts a document with a generated ID."""
    client = get_es_client()
    if not client:
         raise HTTPException(status_code=503, detail="Elasticsearch not available")

    doc_id = str(uuid.uuid4()) # Generate a unique ID
    document = {
        "id": doc_id, # Store generated ID also as keyword field if needed
        "text": request.text
    }

    try:
        response = client.index(index=INDEX_NAME, id=doc_id, document=document, refresh="wait_for") # Use generated ID
        # refresh='wait_for' makes the document searchable immediately for testing
        if response.get('result') == 'created' or response.get('result') == 'updated':
             return {"message": "Document inserted successfully", "id": doc_id, "es_response": response}
        else:
             raise HTTPException(status_code=500, detail=f"Failed to insert document. ES Response: {response}")

    except es_exceptions.NotFoundError:
         raise HTTPException(status_code=404, detail=f"Index '{INDEX_NAME}' not found. Please create it first.")
    except es_exceptions.TransportError as e:
         print(f"Elasticsearch TransportError: {e.info}")
         raise HTTPException(status_code=500, detail=f"Elasticsearch insert error: {e.error}")
    except Exception as e:
         import traceback
         print(f"Unexpected error during insert: {traceback.format_exc()}")
         raise HTTPException(status_code=500, detail=f"An internal server error occurred: {str(e)}")

# Helper function (optional: can be called on startup or managed manually)
# def ensure_index_exists(client):
#     """Creates the index with mapping if it doesn't exist."""
#     try:
#         if not client.indices.exists(index=INDEX_NAME):
#             print(f"Index '{INDEX_NAME}' not found. Creating index...")
#             mapping = {
#                 "mappings": {
#                     "properties": {
#                         "id": {"type": "keyword"},
#                         "text": {"type": "text"}
#                     }
#                 }
#             }
#             client.indices.create(index=INDEX_NAME, body=mapping)
#             print(f"Index '{INDEX_NAME}' created successfully.")
#         else:
#             print(f"Index '{INDEX_NAME}' already exists.")
#     except es_exceptions.TransportError as e:
#         print(f"Error checking/creating index: {e}")
#     except Exception as e:
#         print(f"Unexpected error during index check/creation: {e}")

# Note: Running with uvicorn is handled by the Dockerfile CMD
