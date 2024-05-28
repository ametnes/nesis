# Local Development Guide

This guide walks you through how to start developing Nesis on your local workstation. You can
get an overview of the components that make up Nesis and its architecture [here](./architecture.md).

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

### Using your IDE

## Start supporting services

Supporting services include

1. Postgres (for the backend database as well as the vector database).
2. Memcached for caching and locking services.
3. _Optional_ Minio for document storage.
4. _Optional_ Samba for document storage.

To start the supporting service, in a separate terminal, run
```bash
 docker-compose -f compose-dev.yml up
```

Set up your python virtualenv
```bash
python -m venv .venv
source .venv/bin/activate
```

If you do not have `source`, you can activate the virtualenv with
```bash
. .venv/bin/activate
```
### Windows Users
If you are on Windows, here is what you have to follow:

1. Press the `[windows]` button and then type `PowerShell`.
2. Run as Administrator.
3. Copy and paste the following command and hit `[Enter]`:

    ```powershell
    Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope LocalMachine
    ```
### Set Up Your Python Virtual Environment

1. Navigate to the root of the nesis project.

2. Run the following command to create a virtual environment:

    ```bash
    python -m venv .venv
    ```

3. Activate the virtual environment.

    On Windows, use:

    ```bash
    .venv\Scripts\activate
    ```

## Start the RAG Engine
Install dependencies
```bash
pip install -r nesis/rag/requirements.txt -r nesis/rag/requirements-huggingface.txt --default-timeout=1200
```

Start the service
```bash
export NESIS_RAG_EMBEDDING_DIMENSIONS=384 
export OPENAI_API_KEY=<your-openai-api-key>
python nesis/rag/core/main.py
```

!!! warning "Huggingface vs OpenAI's Embeddings"

    Huggingface embeddings use a dimension of 384 while OpenAI's default embeddings size varies.
    The env variable `NESIS_RAG_EMBEDDING_DIMENSIONS` can be used to alter the dimention of embeddings
    to suit your needs.

#### On Windows

1. **Check Python Version**

   Make sure you are using Python version 3.8.1 to 3.11:

   ```bash
   python --version
   ```

   If your Python version is outside this range, consider downgrading it.

2. **Install Microsoft Visual C++**

   Ensure Microsoft Visual C++ 14.0 or greater is installed.

3. **Install Dependencies**

   ```bash
   pip install -r nesis/rag/requirements.txt -r nesis/rag/requirements-huggingface.txt --default-timeout=1200
   ```

4. **Install PyTorch**

   Visit [PyTorch's official website](https://pytorch.org/) and get the appropriate installation command based on your OS. For example:

   ```bash
   cd nesis/rag
   pip3 install torch torchvision torchaudio
   ```

5. **Set Environment Variables**

   - **Command Prompt:**

     ```bash
     set NESIS_RAG_EMBEDDING_DIMENSIONS=384
     set OPENAI_API_KEY=<your-openai-api-key>
     ```

   - **PowerShell:**

     ```bash
     $env:NESIS_RAG_EMBEDDING_DIMENSIONS = 384
     $env:OPENAI_API_KEY = "<your-openai-api-key>"
     ```

6. **Set Up Relative Package Imports**

   Follow the guidance from [this video](https://youtu.be/Mgp6-ZMEcE0?si=Zm7qXInv1ch_xXaH).

   Create a `setup.py` file in the root directory with the following content:

   ```python
   from setuptools import setup, find_packages

   setup(name='gusml', version='1.0', packages=find_packages())
   ```

   Then run:

   ```bash
   pip install -e .
   ```

7. **Install Additional Packages**

   ```bash
   pip install llama_index
   pip install fastapi
   pip install transformers
   pip install unstructured
   pip install pdfminer.six
   pip install pillow_heif
   pip install opencv-python
   pip install pdf2image
   ```

8. **Start the RAG Engine**

   ```bash
   python nesis/rag/core/main.py
   ```

## Start API Service
Install dependencies
```bash
pip install -r nesis/api/requirements.txt
```

Start the service
```bash
export NESIS_ADMIN_EMAIL="some.email@domain.com"
export NESIS_ADMIN_PASSWORD="password"
export NESIS_API_DATABASE_CREATE="true"
python nesis/api/core/main.py
```

### Starting API Service on Windows

#### Step 1: Download and Install PostgreSQL

Download PostgreSQL from the official website and follow the installation instructions. Make sure to remember the password you set during installation.

#### Step 2: Create a PostgreSQL Database

1. Open pgAdmin or use psql (command line) to create a database named eg `nesis_api_db` with password eg "&nbsp;&nbsp;"(two spaces).

#### Step 3: Set Up Environment Variables
These are set basing on your posgreSQL database configurations
```powershell
# Set PostgreSQL database URL for API connection
$Env:NESIS_API_DATABASE_URL = "postgresql+psycopg2://postgres:  @localhost:5432/nesis_api_db"

# Set PostgreSQL URL for tasks job stores (if applicable)
$Env:NESIS_API_TASKS_JOB_STORES_URL = "postgresql+psycopg2://postgres:  @localhost:5432/nesis_api_db"

# Verify if the environment variables are set correctly
Get-Item Env:NESIS_API_DATABASE_URL
Get-Item Env:NESIS_API_TASKS_JOB_STORES_URL
```
Ensure to Adjust the database URL (`$Env:NESIS_API_DATABASE_URL`) and task job stores URL (`$Env:NESIS_API_TASKS_JOB_STORES_URL`) according to your PostgreSQL configuration.

##### Set admin email, password, and database creation flag
```powershell
# Set admin email, password, and database creation flag
$Env:NESIS_ADMIN_EMAIL="some.email@domain.com"
$Env:NESIS_ADMIN_PASSWORD="password"
$Env:NESIS_API_DATABASE_CREATE="true"
```
#### Step 4: Install Python Dependencies

Install the Python dependencies required for your API service:

```bash
pip install psycopg2
pip install -r nesis/api/requirements.txt
```
#### Step 5: Start the API Service
```bash
python nesis/api/core/main.py
```



## Start the frontend
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