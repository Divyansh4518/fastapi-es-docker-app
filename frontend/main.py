import os
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import requests
import json  # Import json for pretty printing

# Determine Backend URL from environment variable or use default
BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8001") # Use container name 'backend' and internal port 8001

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# In-memory storage for the last message (replace with better state management if needed)
last_message = "Welcome! Use the forms above to interact with Elasticsearch."

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Serves the main HTML page."""
    global last_message
    # Display the last message and clear it for the next interaction
    message_to_display = last_message
    # Keep the welcome message persistent until an action is performed
    # if not message_to_display.startswith("Welcome!"):
    #      last_message = "Waiting for next action..." # Reset after display unless it's welcome
    return templates.TemplateResponse("index.html", {"request": request, "message": message_to_display})

@app.post("/search", response_class=HTMLResponse)
async def search_docs(request: Request, query: str = Form(...)):
    """Sends search query to backend and displays result."""
    global last_message
    try:
        response = requests.post(f"{BACKEND_URL}/search", json={"query": query})
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
        result_data = response.json()
        # Format the output nicely
        last_message = f"Search Results for '{query}':\n\n{json.dumps(result_data, indent=2)}"
    except requests.exceptions.RequestException as e:
        last_message = f"Error contacting backend: {e}"
    except Exception as e:
        last_message = f"An error occurred: {e}"

    # Redirect back to the main page to display the message
    # Using GET after POST pattern (Redirect-After-Post)
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/", status_code=303)


@app.post("/insert", response_class=HTMLResponse)
async def insert_doc(request: Request, text: str = Form(...)):
    """Sends document text to backend for insertion."""
    global last_message
    try:
        response = requests.post(f"{BACKEND_URL}/insert", json={"text": text})
        response.raise_for_status()
        result_data = response.json()
        last_message = f"Insertion Status:\n\n{json.dumps(result_data, indent=2)}"
    except requests.exceptions.RequestException as e:
        last_message = f"Error contacting backend: {e}"
    except Exception as e:
        last_message = f"An error occurred: {e}"

    # Redirect back to the main page
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/", status_code=303)

# Note: In a production scenario, use a proper ASGI server like uvicorn or hypercorn
# The Dockerfile CMD will handle running uvicorn
