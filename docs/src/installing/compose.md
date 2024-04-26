# Docker Compose
For your quick local test, a <a href="https://github.com/ametnes/nesis/blob/main/compose.yml" target="_blank">docker compose</a> file is provided which you can
run to standup a local instance of Nesis.

## Compose File

```yaml title="compose.yml" linenums="1"

version: '3'


networks:
  nesis:
    driver: overlay
    attachable: true

services:

  nesis_frontend:
    image: ametnes/nesis:latest-frontend
    ports:
      - "58000:8000"
    environment:
      API_URL: http://nesis_api:6000
    networks:
      - nesis
    depends_on:
      - nesis_api
  nesis_api:
    image: ametnes/nesis:latest-api
    ports:
      - "56000:6000"
    environment:
      NESIS_API_PORT: "6000"
      NESIS_API_DATABASE_URL: "postgresql://postgres:password@database:5432/nesis"
      NESIS_API_TASKS_JOB_STORES_URL: "postgresql://postgres:password@database:5432/nesis"
      NESIS_ADMIN_EMAIL: "some.email@domain.com"
      NESIS_ADMIN_PASSWORD: "password"
      NESIS_MEMCACHE_HOSTS: memcached:11211
      NESIS_API_RAG_ENDPOINT: http://nesis_rag:8080
    networks:
      - nesis
    depends_on:
      database:
        condition: service_healthy
    links:
      - database
      - memcached
      - nesis_rag
  nesis_rag:
    image: ametnes/nesis:latest-rag
    ports:
      - "58080:8080"
    environment:
      NESIS_RAG_SERVER_PORT: "8080"
      NESIS_RAG_PGVECTOR_URL: postgresql://postgres:password@database:5432/nesis
      HF_TOKEN: <your-huggingface-token>
      # 1. local mode uses hugging face. Other options
      NESIS_RAG_EMBEDDING_MODE: local
      NESIS_RAG_EMBEDDING_DIMENSIONS: "384"

      # 2. openai - for OpenAI Embeddings
      # NESIS_RAG_EMBEDDING_MODE: openai
      # NESIS_RAG_EMBEDDING_DIMENSIONS: "1536"

      # 3. sagemaker - for Sagemaker
      OPENAI_API_KEY: <your-api-key>
#      OPENAI_API_BASE: <your-api-base>
    networks:
      - nesis
    depends_on:
      - database
  memcached:
    image: bitnami/memcached:1.6.19
    ports:
      - "11211:11211"
    networks:
      - nesis
  samba:
    image: andyzhangx/samba:win-fix
    command: ["-u", "username;password", "-s", "share;/smbshare/;yes;no;no;all;none", "-p"]
    ports:
      - '2445:445'
    networks:
      - nesis
    volumes:
      - 'samba_data2:/smbshare'
    environment:
      - USERNAME=username
      - PASSWORD=password
  minio:
      image: docker.io/bitnami/minio:2022
      ports:
        - '59000:9000'
        - '59001:9001'
      networks:
        - nesis
      volumes:
        - 'minio_data:/data'
      environment:
        - MINIO_ROOT_USER=your_username
        - MINIO_ROOT_PASSWORD=your_password
        - MINIO_DEFAULT_BUCKETS=documents
  database:
    image: "ametnes/postgresql:16-debian-12"
    ports:
      - "65432:5432"
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
      POSTGRES_DB: nesis
    volumes:
      - database_data:/var/lib/postgresql/data
    restart: on-failure
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5
    networks:
      - nesis
volumes:
  minio_data:
  samba_data2:
  database_data:

```

## Steps

1. Obtain your **OPENAI_API_KEY** from https://platform.openai.com/api-keys:
      - and update the `compose.yml` file entry.

2. Start all services locally with the provided docker compose file.

   ```commandline
   docker-compose -f compose.yml up
   ```

2. Then connect to your instance via http://localhost:58000 with the following login credentials:
      - *email* = `some.email@domain.com`
      - *password* = `password`

3. Connect to your minio instance via http://localhost:59001/ with the following login credentials:
      - *username* = `your_username`
      - *password* = `your_password`


4. Upload some documents into your minio `documents` bucket.

5. Back on your Nesis page, register the minio datasource with
   1. Navigate to **Settings** -> **Datasource** -> **Add**
   2. Enter the details;
   
      1. Type: **S3 Compatible**
      2. Name: **documents**
      3. Host: **http://minio:9000/**
      4. Access Key: `your_username`
      5. Access Secret: `your_password`
      6. Buckets: **documents**
      7. Click **Create**
      8. Then, run an adhoc ingestion by clicking the **Ingest** button of the datasource.

