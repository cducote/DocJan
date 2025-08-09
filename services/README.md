# Confluence Document Processing Service

A containerized FastAPI service for efficiently connecting to Confluence, loading all accessible documents, vectorizing them, and detecting duplicates. Extracted from the original Streamlit application for better separation of concerns and cloud deployment.

## Architecture

- **FastAPI Application** (`services/main.py`): REST API endpoints for all operations
- **Confluence Service** (`services/confluence_service.py`): Core logic for connecting to Confluence and loading documents  
- **Vector Store Service** (`services/vector_store_service.py`): Embedding generation and ChromaDB operations
- **Configuration** (`services/config.py`): Centralized configuration management

## Features

- ✅ Connect to Confluence with credentials
- ✅ Discover all accessible spaces
- ✅ Load all pages from selected spaces (no limits, efficient batching)
- ✅ Generate embeddings using OpenAI API
- ✅ Store vectors in ChromaDB for fast similarity search
- ✅ Detect and track duplicate documents
- ✅ Background processing with status tracking
- ✅ Docker containerization ready
- ✅ Local development support

## Quick Start

### Local Development (without Docker)

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment:**
   ```bash
   cp services/.env.example services/.env
   # Edit services/.env with your credentials
   ```

3. **Run the service:**
   ```bash
   cd services
   python main.py
   ```

4. **Access the API:**
   - API docs: http://localhost:8000/docs
   - Health check: http://localhost:8000/health

### Docker Development

1. **Create environment file:**
   ```bash
   cp services/.env.example .env
   # Edit .env with your credentials
   ```

2. **Run with Docker Compose:**
   ```bash
   docker-compose up --build
   ```

3. **Access the API:**
   - API docs: http://localhost:8000/docs
   - Health check: http://localhost:8000/health

## API Endpoints

### Core Operations

- `POST /test-connection` - Test Confluence credentials
- `POST /spaces` - Get all accessible Confluence spaces
- `POST /process` - Start document processing (background job)
- `GET /status/{processing_id}` - Get processing status

### Data Management

- `GET /connection-status` - Get system connection status
- `GET /duplicates` - Get detected duplicate document pairs
- `DELETE /clear` - Clear all documents from vector store

### System

- `GET /health` - Health check endpoint

## Environment Variables

Required:
- `OPENAI_API_KEY` - OpenAI API key for embeddings

Optional:
- `CONFLUENCE_BASE_URL` - Default Confluence URL
- `CONFLUENCE_USERNAME` - Default Confluence username
- `CONFLUENCE_API_TOKEN` - Default Confluence API token
- `CHROMA_PERSIST_DIRECTORY` - ChromaDB storage directory (default: ./chroma_store)
- `DEFAULT_SIMILARITY_THRESHOLD` - Similarity threshold for duplicates (default: 0.65)
- `API_HOST` - API host (default: 0.0.0.0)
- `API_PORT` - API port (default: 8000)

## Usage Example

```python
import requests

# Test connection
response = requests.post("http://localhost:8000/test-connection", json={
    "base_url": "https://company.atlassian.net/wiki",
    "username": "user@company.com",
    "api_token": "your_token"
})

# Get spaces
spaces = requests.post("http://localhost:8000/spaces", json={
    "base_url": "https://company.atlassian.net/wiki",
    "username": "user@company.com", 
    "api_token": "your_token"
}).json()

# Process documents
processing = requests.post("http://localhost:8000/process", json={
    "credentials": {
        "base_url": "https://company.atlassian.net/wiki",
        "username": "user@company.com",
        "api_token": "your_token"
    },
    "space_keys": ["SD", "TECH"],
    "similarity_threshold": 0.65
})

processing_id = processing.json()["processing_id"]

# Check status
status = requests.get(f"http://localhost:8000/status/{processing_id}")
```

## Deployment

### EKS Deployment

1. **Build and push Docker image:**
   ```bash
   docker build -t your-registry/confluence-processor:latest .
   docker push your-registry/confluence-processor:latest
   ```

2. **Create Kubernetes manifests** (examples in `k8s/` directory)

3. **Deploy to EKS:**
   ```bash
   kubectl apply -f k8s/
   ```

### Environment Configuration

For production deployment, set environment variables via:
- Kubernetes ConfigMaps/Secrets
- AWS Parameter Store
- Docker environment variables

## Development

### Project Structure

```
services/
├── main.py                 # FastAPI application
├── confluence_service.py   # Confluence operations
├── vector_store_service.py # Vector store operations
├── config.py              # Configuration management
└── .env.example           # Environment template

docker-compose.yml         # Local development
Dockerfile                # Container build
requirements.txt          # Python dependencies
```

### Adding New Features

1. **Service Layer**: Add business logic to appropriate service class
2. **API Layer**: Add endpoints to `main.py` 
3. **Configuration**: Add new config variables to `config.py`
4. **Testing**: Add tests and update documentation

## Monitoring and Logs

- Health check endpoint: `/health`
- Processing status tracking via `/status/{id}`
- Application logs via Docker/Kubernetes logs
- Background job monitoring through status endpoints

## Troubleshooting

### Common Issues

1. **ChromaDB Permission Errors**: Ensure proper directory permissions for `CHROMA_PERSIST_DIRECTORY`
2. **OpenAI Rate Limits**: Implement retry logic or reduce batch sizes
3. **Confluence Connection Issues**: Verify API tokens and network connectivity
4. **Memory Issues**: Reduce `DEFAULT_BATCH_SIZE` for large document sets

### Debug Mode

Set `LOG_LEVEL=DEBUG` for verbose logging during development.
