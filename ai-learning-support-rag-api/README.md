# AI Learning Support RAG API

## Overview
The AI Learning Support RAG API is a FastAPI-based application designed to facilitate the upload and retrieval of PDF documents for educational purposes. The application supports multi-tenancy through metadata filtering, ensuring data isolation between different courses and groups.

## Project Structure
The project is organized as follows:

```
ai-learning-support-rag-api
├── app
│   ├── main.py                # Entry point for the FastAPI application
│   ├── api
│   │   └── v1
│   │       ├── health.py      # Health check endpoint
│   │       ├── upload.py      # Endpoint for uploading PDF files
│   │       └── retrieve.py     # Placeholder for retrieving documents
│   ├── core
│   │   ├── config.py          # Configuration settings
│   │   └── security.py        # Security-related configurations
│   ├── schemas
│   │   ├── upload.py          # Pydantic schema for upload requests
│   │   └── retrieve.py        # Pydantic schema for retrieve requests
│   ├── services
│   │   ├── pdf_parser.py      # PDF parsing logic
│   │   ├── chunker.py         # Text chunking logic
│   │   ├── embeddings.py       # Embedding generation logic
│   │   ├── vector_store.py     # Vector database interactions
│   │   └── local_storage.py    # Local file storage management
│   └── db
│       └── qdrant_client.py    # Database client interactions with Qdrant
├── tests
│   ├── test_health.py         # Tests for health check endpoint
│   ├── test_upload.py         # Tests for upload endpoint
│   ├── test_retrieve.py       # Tests for retrieve endpoint
│   └── test_multi_tenant_isolation.py # Tests for multi-tenant isolation
├── storage
│   ├── pdfs                   # Directory for storing uploaded PDFs
│   │   └── .gitkeep
│   └── vectors                # Directory for storing vector embeddings
│       └── .gitkeep
├── docker-compose.yml         # Docker configuration for services
├── Dockerfile                 # Instructions for building the Docker image
├── pyproject.toml             # Project dependencies and configuration
├── uv.lock                    # Locked dependencies
├── .env.example               # Example environment variables
└── README.md                  # Project documentation
```

## Setup Instructions
1. **Clone the Repository**
   ```bash
   git clone <repository-url>
   cd ai-learning-support-rag-api
   ```

2. **Install Dependencies**
   Ensure you have Python 3.8 or higher installed. Then, install the project dependencies using:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Application**
   You can run the FastAPI application using Uvicorn:
   ```bash
   uvicorn app.main:app --reload
   ```

4. **Access the API**
   The API will be available at `http://localhost:8000`. You can access the documentation at `http://localhost:8000/docs`.

## Current Implementation Status
- Project structure has been created with folders for `app`, `tests`, and `storage`.
- Main FastAPI application is implemented in `app/main.py`.
- Health check endpoint is set up in `app/api/v1/health.py`.
- PDF upload endpoint is implemented in `app/api/v1/upload.py`.
- Placeholder retrieval endpoint is created in `app/api/v1/retrieve.py`.
- Configuration settings are defined in `app/core/config.py`.
- Pydantic schemas for upload and retrieve requests are created in `app/schemas/`.
- Local storage mechanism for raw PDFs is implemented in `app/services/local_storage.py`.
- Test files for health, upload, retrieve, and multi-tenant isolation are created in the `tests` folder.

## Future Work
- Implement PDF parsing logic in `app/services/pdf_parser.py`.
- Implement text chunking logic in `app/services/chunker.py`.
- Implement embedding generation logic in `app/services/embeddings.py`.
- Implement vector database interactions in `app/services/vector_store.py`.
- Enhance security configurations in `app/core/security.py`.