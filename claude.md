# Project Plan – Python Core Logic Containerization for Confluence Connector

## 1. Overview

We are migrating the backend logic of a previous Streamlit application into a standalone Python service that will:
- Connect to Confluence spaces
- Read and parse page content
- Vectorize the content using embeddings
- Store embeddings in ChromaDB

The Python service will run inside a container on AWS EKS, but should also be fully testable locally before deployment.

The frontend logic has already been moved to Next.js. This plan focuses on extracting the **pure Python business logic** from the old Streamlit application and wrapping it in a service architecture suitable for containerization.

---

## 2. Goals

- **Separation of Concerns** – Frontend in Next.js, backend logic in a containerized Python service.
- **Local Development First** – Be able to run and test all functionality on a local machine.
- **Cloud Deployment Ready** – Deploy to EKS with minimal changes from local testing configuration.
- **Reusability** – The Python service can be integrated with multiple frontends or automation tools.

---

## 3. Architecture

### 3.1 High-Level Flow
1. **Frontend Request (Next.js)** → Sends request (via REST API or gRPC) to Python service.
2. **Python Service**:
   - Authenticate with Confluence API
   - Retrieve space/page data
   - Process and clean page content
   - Generate embeddings using chosen LLM/embedding model
   - Store embeddings in ChromaDB
3. **Response** → Send status or result back to frontend.

### 3.2 Components
- **API Layer** – FastAPI or Flask to expose endpoints.
- **Confluence Connector** – Logic to fetch and process pages from Confluence.
- **Embedding Generator** – Uses OpenAI API (or other) to convert text into vectors.
- **Vector Store Interface** – Interacts with ChromaDB (local for dev, persistent in prod).
- **Configuration Layer** – Environment variables for keys, DB paths, and Confluence credentials.

---

## 4. Local Development Setup

### 4.1 Prerequisites
- Docker
- Python 3.12+
- Virtual environment (for non-container local testing) (.venv)
- ChromaDB installed locally
- Access to Confluence API credentials

### 4.2 Steps
1. **Extract Logic** – Claude will identify the Python code from the old Streamlit app that:
   - Authenticates with Confluence
   - Reads and parses pages
   - Generates embeddings
   - Saves them in ChromaDB
2. **Create FastAPI Wrapper** – Wrap the extracted logic in HTTP endpoints:
   - `/connect` – Initiates Confluence connection
   - `/vectorize` – Reads pages and stores embeddings
3. **Run Locally Without Docker** –  