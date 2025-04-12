# FastAPI, Elasticsearch, and Docker Project

This project demonstrates a 3-tier web application using FastAPI for the frontend and backend, Elasticsearch as the search/data store, and Docker/Docker Compose for containerization and orchestration.

## Architecture

The application consists of three main services running in separate Docker containers on a shared network:

1.  **Frontend (`frontend` service):**
    *   A FastAPI application serving an HTML interface (using Jinja2 templates).
    *   Allows users to insert text documents and perform searches.
    *   Listens internally on port `8000`.
    *   Exposed to the host machine on port `9567`.
    *   Communicates with the `backend` service over the internal Docker network.
    *   Docker Image: `yourdockerhubuser/fastapi:1` (or built locally via Compose)

2.  **Backend (`backend` service):**
    *   A FastAPI application providing a REST API.
    *   Handles requests from the frontend to insert data into Elasticsearch and perform searches against it.
    *   Listens internally on port `8001`.
    *   *Not* exposed directly to the host machine.
    *   Communicates with the `elasticsearch-service` over the internal Docker network.
    *   Docker Image: `yourdockerhubuser/fastapi:2` (or built locally via Compose)

3.  **Elasticsearch (`elasticsearch-service` service):**
    *   Official Elasticsearch 7.17.15 container.
    *   Stores and indexes the text documents.
    *   Listens internally on port `9567`.
    *   *Not* exposed directly to the host machine.
    *   Uses a Docker named volume (`es-data`) for persistent data storage.
    *   Docker Image: `docker.elastic.co/elasticsearch/elasticsearch:7.17.15` (tagged as `yourdockerhubuser/elasticsearch:latest` for push)

*   **Network (`app-network`):** A custom Docker bridge network allowing containers to communicate using service names.
*   **Volume (`es-data`):** Persists Elasticsearch data even if the container is removed and recreated.

(Optional: You can embed an architectural diagram image here)

## Features

*   Insert text documents into Elasticsearch.
*   Search for documents based on keywords using Elasticsearch's `match` query.
*   Displays the best matching document and its score.
*   Web interface built with FastAPI and Jinja2.
*   Persistent data storage for Elasticsearch.
*   Fully containerized setup using Docker Compose.

## Directory Structure
.
├── .gitignore
├── backend/
│ ├── Dockerfile
│ ├── main.py
│ └── requirements.txt
├── docker-compose.yml
├── frontend/
│ ├── Dockerfile
│ ├── main.py
│ ├── requirements.txt
│ └── templates/
│ └── index.html
└── README.md

## Prerequisites

*   [Git](https://git-scm.com/downloads)
*   [Docker](https://docs.docker.com/get-docker/)
*   [Docker Compose](https://docs.docker.com/compose/install/) (usually included with Docker Desktop, might need separate install on Linux)
*   An internet connection (to pull base images and install dependencies)
*   (Optional) A Docker Hub account if you want to push the built images. Replace `yourdockerhubuser` below with your username if pushing.

## Setup and Installation (Using Docker Compose - Recommended)

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-github-username/your-repo-name.git
    cd your-repo-name
    ```

2.  **Build and Start Containers:**
    This command will build the frontend and backend images (if not already built) and start all three services (frontend, backend, elasticsearch) in detached mode. It also creates the network and volume automatically.
    ```bash
    docker-compose up --build -d
    ```
    *Wait about 60 seconds* for Elasticsearch to fully initialize before proceeding. You can check logs using `docker-compose logs -f elasticsearch-service`. Look for messages indicating it's ready or check the health status via `docker ps`.

3.  **Initial Elasticsearch Setup (Index Creation & Data Insertion):**
    The application expects an index named `wikipedia_india`. We need to create it and add some initial data. These commands use `docker-compose exec` to run commands *inside* the running `backend` container, which can talk to Elasticsearch.

    *   **Install curl in backend container (needed for setup commands):**
        ```bash
        docker-compose exec backend apt-get update && docker-compose exec backend apt-get install -y curl --no-install-recommends && docker-compose exec backend rm -rf /var/lib/apt/lists/*
        ```

    *   **Create the Elasticsearch Index:**
        ```bash
        docker-compose exec backend curl -X PUT "http://elasticsearch-service:9567/wikipedia_india?pretty" \
          -H 'Content-Type: application/json' \
          -d'
        {
          "mappings": {
            "properties": {
              "id": { "type": "keyword" },
              "text": { "type": "text" }
            }
          }
        }
        '
        ```

    *   **Insert Initial Documents:**
        ```bash
        # Doc 1
        docker-compose exec backend curl -X POST "http://localhost:8001/insert" \
          -H 'Content-Type: application/json' \
          -d'{"text": "India, officially the Republic of India (ISO: Bhārat Gaṇarājya), is a country in South Asia. It is the seventh-largest country by area; the most populous country as of June 2023; and from the time of its independence in 1947, the world'\''s most populous democracy. Bounded by the Indian Ocean on the south, the Arabian Sea on the southwest, and the Bay of Bengal on the southeast, it shares land borders with Pakistan to the west; China, Nepal, and Bhutan to the north; and Bangladesh and Myanmar to the east. In the Indian Ocean, India is in the vicinity of Sri Lanka and the Maldives; its Andaman and Nicobar Islands share a maritime border with Thailand, Myanmar, and Indonesia."}'

        # Doc 2
        docker-compose exec backend curl -X POST "http://localhost:8001/insert" \
          -H 'Content-Type: application/json' \
          -d'{"text": "Modern humans arrived on the Indian subcontinent from Africa no later than 55,000 years ago. Their long occupation, first in varying forms of isolation as hunter-gatherers, has made the region highly diverse, second only to Africa in human genetic diversity. Settled life emerged on the subcontinent in the western margins of the Indus river basin approximately 9,000 years ago, evolving gradually into the Indus Valley Civilisation of the third millennium BCE."}'

        # Add Doc 3 and Doc 4 curls here too...
        docker-compose exec backend curl -X POST "http://localhost:8001/insert" -H 'Content-Type: application/json' -d'{"text": "By 1200 BCE, an archaic form of Sanskrit, an Indo-European language, had diffused into India from the northwest. Its evidence today is found in the hymns of the Rigveda. Preserved by an oral tradition that was scrupulously faithful, the Rigveda records the dawning of Hinduism in India. The Dravidian languages of India were supplanted in the northern and western regions."}'
        docker-compose exec backend curl -X POST "http://localhost:8001/insert" -H 'Content-Type: application/json' -d'{"text": "By 400 BCE, stratification and exclusion by caste had emerged within Hinduism, and Buddhism and Jainism had arisen, proclaiming social orders unlinked to heredity. Early political consolidations gave rise to the loose-knit Maurya and Gupta Empires based in the Ganges Basin. Their collective era was suffused with wide-ranging creativity, but also marked by the declining status of women, and the incorporation of untouchability into an organised system of belief. In South India, the Middle kingdoms exported Dravidian-languages scripts and religious cultures into the kingdoms of Southeast Asia."}'

        ```
    Setup is now complete!

## Running and Testing

1.  **Access the Frontend:** Open your web browser and navigate to `http://localhost:9567` or `http://<your-vm-ip>:9567`.
2.  **Test Search:** Enter search terms like "language", "africa", "hinduism" into the search box and click "Get Best Match". Observe the results.
3.  **Test Insert:** Enter a new paragraph of text into the "Insert Document" text area and click "Insert Document".
4.  **Test Search Again:** Search for terms present in the document you just inserted.
5.  **Test Persistence:**
    *   Stop the containers: `docker-compose down`
    *   Restart the containers: `docker-compose up -d` (Wait ~60s for ES again)
    *   Access the frontend: `http://localhost:9567`
    *   Search again for the custom document you inserted earlier. It should still be found, demonstrating data persistence via the Docker volume.

## Docker Hub Images (Optional)

If you want to push the built images to Docker Hub:

1.  **Login:**
    ```bash
    docker login
    ```
2.  **Tag Images (if needed, Compose uses default tags):**
    You might need to explicitly tag the images built by Compose if you want specific tags or usernames different from the directory names.
    ```bash
    # Example if compose built 'your-repo-name_frontend' and 'your-repo-name_backend'
    # docker tag your-repo-name_frontend yourdockerhubuser/fastapi:1
    # docker tag your-repo-name_backend yourdockerhubuser/fastapi:2

    # Tag Elasticsearch image (pulled separately or built via compose)
    docker pull docker.elastic.co/elasticsearch/elasticsearch:7.17.15
    docker tag docker.elastic.co/elasticsearch/elasticsearch:7.17.15 yourdockerhubuser/elasticsearch:latest
    ```
3.  **Push Images:**
    ```bash
    # docker push yourdockerhubuser/fastapi:1
    # docker push yourdockerhubuser/fastapi:2
    # docker push yourdockerhubuser/elasticsearch:latest
    ```

*   Frontend Image: [https://hub.docker.com/r/yourdockerhubuser/fastapi](https://hub.docker.com/r/yourdockerhubuser/fastapi) (Replace with your link)
*   Backend Image: (Same repo, different tag): [https://hub.docker.com/r/yourdockerhubuser/fastapi](https://hub.docker.com/r/yourdockerhubuser/fastapi) (Replace with your link)
*   Elasticsearch Image: [https://hub.docker.com/r/yourdockerhubuser/elasticsearch](https://hub.docker.com/r/yourdockerhubuser/elasticsearch) (Replace with your link)

## Cleanup

To stop and remove the containers, network, and volume created by Docker Compose:

```bash
docker-compose down -v # The -v flag removes the named volume (es-data)
