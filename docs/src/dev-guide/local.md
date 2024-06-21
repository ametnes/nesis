# Local Development Guide

This guide walks you through how to start developing Nesis on your local workstation. You can
get an overview of the components that make up Nesis and its architecture [here](./how-it-works.md).

## Prerequisites
1. We use docker and docker-compose to support our development process. If you don't have docker installed
   locally, please for the [Install Docker Engine](https://docs.docker.com/engine/install/){target="_blank"} link for instructions on how
   install docker on your local workstation.
2. If you rather not install docker, you will need to have access to a Postgres and Memcached instance.
3. _Optional:_ The RAG Engine needs access to an LLM endpoint such as an OpenAI's endpoint or a private LLM endpoint 
in order to start querying your documents. You will need to set the `OPENAI_API_KEY` and the `OPENAI_API_BASE`environment variables.
4. Recently, Huggingface requires a `HF_TOKEN` to download embedding models. You may need to obtain and set your `HF_TOKEN`.
5. You need to have python 3.11 for the API and RAG Engine microservices.
6. You also need to have node and npm installed.


!!! note "A word on vector databases"

    Nesis' RAG Engine requires a vector database to store vector embeddings. In order to contain the number of
    components, we use pgvector packaged into an extended Bitnami Postgres docker image `ametnes/postgresql:16-debian-12` 
    [here](https://github.com/ametnes/postgresql){target="_blank"}. You are however free to use other vector databases.
    Curently, we support `chromadb` and `qdrant`.


## Quick Start

Start by checking out the repository.

```bash
git checkout https://github.com/ametnes/nesis.git
cd nesis
```

### Using Docker

#### Build all the docker images locally.

```bash
{
    docker build --build-arg PUBLIC_URL=/ --build-arg PROFILE=PROD -t ametnes/nesis:latest-frontend . -f nesis/frontend/Dockerfile
    docker build -t ametnes/nesis:latest-api . -f nesis/api/Dockerfile
    docker build -t ametnes/nesis:latest-rag . -f nesis/rag/Dockerfile
}
```

#### Use the docker compose file to run the services locally. In your terminal, run

```bash
docker-compose up
```

#### Access the frontend locally.

1. Point your browser to [http://localhost:58000/](http://localhost:58000/)
2. Login with

      1. Email: `some.email@domain.com`
      2. Password: `password`

# Using your IDE

#### Start supporting services

### Start Supporting Services

Supporting services include:

1. Postgres (for the backend database as well as the vector database).
2. Memcached for caching and locking services.
3. _Optional_ Minio for document storage.
4. _Optional_ Samba for document storage.

To start the supporting services, in a separate terminal, run:

```bash
docker-compose -f compose-dev.yml up
```

### Set Up Your Python Virtual Environment

#### On Linux or macOS

1. Create a virtual environment:
    ```bash
    python -m venv .venv
    ```
2. Activate the virtual environment:
    ```bash
    source .venv/bin/activate
    ```

If you do not have `source`, you can activate the virtualenv with:
    ```bash
    . .venv/bin/activate
    ```

#### On Windows

1. Press the **Windows** button and type **PowerShell**.
2. Run as Administrator.
3. Set the execution policy to allow scripts to run:
    ```powershell
    Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope LocalMachine
    ```

4. Navigate to the root of the nesis project.
5. Create a virtual environment:
    ```powershell
    python -m venv .venv
    ```
6. Activate the virtual environment:
    ```powershell
    .venv\Scripts\activate
    ```

# Starting the RAG Engine

### Install Dependencies

```bash
pip install -r nesis/rag/requirements.txt -r nesis/rag/requirements-huggingface.txt --default-timeout=1200
```

### Start the Service

```bash
export NESIS_RAG_EMBEDDING_DIMENSIONS=384 
export OPENAI_API_KEY=<your-openai-api-key>
python nesis/rag/core/main.py
```

!!! warning "Huggingface vs OpenAI's Embeddings"
    Huggingface embeddings use a dimension of 384 while OpenAI's default embeddings size varies.
    The env variable `NESIS_RAG_EMBEDDING_DIMENSIONS` can be used to alter the dimension of embeddings
    to suit your needs.

### <u>Starting the RAG Engine On Windows</u>

### Check Python Version

Make sure you are using Python version 3.8.1 to 3.11:

```bash
python --version
```

If your Python version is outside this range, consider downgrading it.

### Install Microsoft Visual C++

Ensure Microsoft Visual C++ 14.0 or greater is installed.

### Install Dependencies

```bash
pip install -r nesis/rag/requirements.txt -r nesis/rag/requirements-huggingface.txt --default-timeout=1200
```

### Install PyTorch

   Visit [PyTorch's official website](https://pytorch.org/) and get the appropriate installation command based on your OS. For example:

```bash
cd nesis/rag
pip3 install torch torchvision torchaudio
```

### Set Environment Variables

#### Command Prompt:

```cmd
set NESIS_RAG_EMBEDDING_DIMENSIONS=384
set OPENAI_API_KEY=<your-openai-api-key>
```

#### PowerShell:

```powershell
$env:NESIS_RAG_EMBEDDING_DIMENSIONS = 384
$env:OPENAI_API_KEY = "<your-openai-api-key>"
```

### Set PYTHONPATH in PowerShell

Set the `PYTHONPATH` environment variable directly in PowerShell before running your script:

```powershell
# Place path to the root of the project, e.g., "E:\coding\new wave latest\nesis german\nesis-fork-3"
$env:PYTHONPATH = "<your-project-absolute-path>"
```

Then run:

```powershell
python nesis/rag/core/main.py
```

# Start API Service

Since the terminal of the rag engine will be occupied, you will need to open a new terminal and again set up your Python virtual environment there.

Windows users after setting up your Python virtual environment dont forget to Set the `PYTHONPATH` environment variable directly in PowerShell before running your script:

```powershell
# Place path to the root of the project, e.g., "E:\coding\new wave latest\nesis german\nesis-fork-3"
$env:PYTHONPATH = "<your-project-absolute-path>"
```

### 1. Install Dependencies

With the virtual environment activated, install the required dependencies:

```bash
pip install -r nesis/api/requirements.txt
```

### 2. Configure and Start the Service

Set up the necessary environment variables and start the service. Replace `<path-to-config.yml>` with the path to your actual `config.yml` file eg `--config=nesis/api/config.yml`.

```bash
export NESIS_ADMIN_EMAIL="some.email@domain.com"
export NESIS_ADMIN_PASSWORD="password"
export NESIS_API_DATABASE_CREATE="true"
python nesis/api/core/main.py --config=<path-to-config.yml>
```



# Start the frontend
Install dependencies
```bash
cd nesis/frontend
npm install --legacy-peer-deps --prefix client
npm install --legacy-peer-deps
```

Start the frontend-backend service with
```bash
npm run start:server:local
```

In a separate terminal, start the frontend with
```bash
cd nesis/frontend
npm run start:client
```

#### Access the frontend locally.

1. Point your browser to [http://localhost:3000/](http://localhost:3000/)
2. Login with

      1. Email: `some.email@domain.com`
      2. Password: `password`


## All done
You should now be ready to start developing Nesis