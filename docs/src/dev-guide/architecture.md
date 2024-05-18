# Nesis Architecture
The Nessus project is divided into four components.

1. Frontend - This contains the ReactJS frontend and Node Express server (aka frontend-backend).
2. API Backend - This is the backend API responsible for handling; 
       1. Authentication.
       2. User management.
       3. Enforcing Role based access control.
       4. Process scheduling.
       5. And more.
3. RAG Engine - This is response for;
       7. Converting documents into embeddings.
       8. Interfacing with any OpenAI compatible endpoints.
4. Vector DB - For storing vector embeddings.
5. LLM Inference Engine - This is the LLM service that powers the AI process.


## Sequence

This is a simple sequence showing how requests flow when a user chats with their private documents.

``` mermaid
sequenceDiagram
  autonumber
  actor User
  User->>Frontend: quesion
  Frontend->>API: token, query
  API->>API: validate token
  API->>API: check CREATE action on prediction (rbac)
  API->>API: collect datasources valid (READ) for user (rbac)
  alt no datasources exists
    API->>Frontend: 403
    Frontend->>User: error message
  else datasources exists:
    API->>API: add to datasource collection
  end
  alt no CREATE prediction policy for user
    API->>Frontend: 403
    Frontend->>User: error message
  end
  API->>RAG: send request(context=True, filter=[datasources])
  RAG->>VectorDB: query for document chunks
  Note right of RAG: query *must* filter on 'datasource(s)'
  VectorDB->>RAG: document chunks (filtered on datasource(s))
  RAG->>RAG: create prompt with context (document chunks)
  RAG->>LLM: prompt with chunks as context
  LLM->>RAG: response
  RAG->>API: response
  API->>API: save response as prediction (remember CREATE on predictions)
  API->>Frontend: response
  Frontend->>User: success message
```


???+ note "Document Ingestion"

    Documents are ingested by creating adding your document repository as a datasource and a manual 
    (one time only) or scheduled task.


## RAG Engine
### Overview
The RAG Engine is responsible for;

1. Orchestrating the conversion of documents into embeddings using the ingestion process. Currently supported formats include pdf, mp3, mp4, tiff, png, jp[e]g, docx, pptx, epub.
2. Persisting embeddings into vector store (See vector database section [below](#vector-database)).
3. Receiving user queries (always) with context enabled and finding the necessary (filter=[datasource=?]) document chunks from the VectorDB.
4. Formulating an OpenAI prompt with context from 3.
5. Sending the formatted prompt to OpenAI.

### Vector Database
A vector database component is critical to the functionality of the RAG engine. It stores vector embeddings and offers retrieval of 
document chucks from these embeddings.

Nesis currently supports three vector databases;

1. Postgres with pgvector extension. We have <a href="https://github.com/ametnes/postgresql" target="_blank">modified</a> the bitnami postgres image and added the pgvector extension.
2. <a href="https://github.com/chroma-core/chroma" target="_blank">Chromadb</a>.
3. <a href="https://github.com/qdrant/qdrant" target="_blank">Qdrant</a>.

### Local Embeddings
Nesis supports generating embeddings locally using HuggingFace embeddings models. The environment variable `NESIS_RAG_EMBEDDING_MODE` controls this.

!!! warning "Huggingface vs OpenAI's Embeddings"

    Huggingface (HF) embeddings use a dimension of 384 while OpenAI's default embeddings size varies.
    The env variable `NESIS_RAG_EMBEDDING_DIMENSIONS` can be used to alter the dimention of embeddings
    to suit your needs.

    You may need to create a HF token in order to access any HF models. If you encounter an access denied during he ingestion process
    set the `HF_TOKEN` with your HF token.

### OpenAI Embeddings

Nesis can also use OpenAI to generate embeddings. By setting the environment variable `NESIS_RAG_EMBEDDING_MODE=openai`, Nesis would use the configured OpenAI
endpoint to generate embeddings.

!!! note

    To use OpenAI embeddings, an `OPENAI_API_KEY` would have to be supplied.


### LLM
Nesis supports any OpenAI compatible LLM service. By setting the `OPENAI_API_KEY` and `OPENAI_API_BASE` environment variables, you are able
to configure which OpenAI API to use.

When running Nesis in your private network you will need to provide your own private LLM service. 

???+ tip "Fully private LLM service"

    <a href="https://cloud.ametnes.com/" target="_blank">Ametnes</a> provides a fully managed private LLM service that runs enterily in your private network. Your data stays completely
    ring-fenced in your private environment allowing you to achive full privacy.


## Backend API
TODO

## Frontend
TODO
