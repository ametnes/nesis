
<p align="center">
  <img height="100" src="https://raw.githubusercontent.com/ametnes/nesis/main/nesis/frontend/client/src/images/Nesis.svg" alt="Nesis" title="Nesis">
</p>

<p align="center">
   <a href="https://github.com/ametnes/nesis/actions/workflows/test_frontend.yml" target="_blank"><img src="https://github.com/ametnes/nesis/actions/workflows/test_frontend.yml/badge.svg" alt="Test Frontend"/></a>
   <a href="https://github.com/ametnes/nesis/actions/workflows/test_api.yml" target="_blank"><img src="https://github.com/ametnes/nesis/actions/workflows/test_api.yml/badge.svg" alt="Test Frontend"/></a>
   <a href="https://github.com/ametnes/nesis/actions/workflows/test_rag.yml" target="_blank"><img src="https://github.com/ametnes/nesis/actions/workflows/test_rag.yml/badge.svg" alt="Test Frontend"/></a>
   <a href="./LICENSE" target="_blank"><img src="https://img.shields.io/badge/License-Apache_2.0-blue.svg" alt="License"/></a>
</p>

---
# 👋 What is Nesis❓

Nesis is an open-source enterprise knowledge discovery solution that connects to multitudes of datasources, collecting 
information and making it available in a conversation manner. Nesis leverages generative AI to aggregate document chunks
collected from different documents in multiple formats such as pdf, docx, xlsx and turn them into meaning human-readable compositions. Allowing you to;

1. Converse with your document via a simple chat interface.
2. Conveniently view comparisons between documents.
3. Summarise large documents.

# Demo

https://github.com/ametnes/nesis/assets/86433807/64ea0ad8-5615-4111-8f6e-61ce7d3ad2fc

## 📜 Documentation
Read the Nesis documentation [here](https://ametnes.github.io/nesis)

## 🎰 Main features
Nesis is built to handle large amounts of data at scale. Enabling connectivity to multitudes of datasources, 
Nesis is able to transform data from various formats into vector embeddings to be used by your LLM of choice.

Enterprise ready knowledge discovery solution that empowers users to
1. 🗣Interact with vast document repositories in a conversational AI style.
2. 🛂Role based access control access to the document repositories, ensuring that the enterprise user only views information they are allowed to.
3. 🗄Connect to vast number of repositories. Currently, S3, Windows Shares, MinIO
4. ☁ 🏢Can be deployed in your cloud or on-premises.
5. 🔐User session management.

## Getting started
To get started with Nesis

### Deploy with Docker Compose
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
      - *username* = `YOUR_USERNAME`
      - *password* = `YOUR_PASSWORD`


4. Upload some documents into your minio `documents` bucket.

5. Back on your Nesis page, register the minio datasource with
   1. Navigate to **Settings** -> **Datasource** -> **Add**
   2. Enter the details;
   
      1. Type: **S3 Compatible**
      4. Name: **documents**
      5. Host: **http://minio:9000/**
      6. Username: `YOUR_USERNAME`
      7. Password: `YOUR_PASSWORD`
      8. Click **Create**
      9. Then, run an adhoc ingestion by clicking the **Ingest** button of the datasource.

- *Note*: Replace `YOUR_USERNAME` and `YOUR_PASSWORD` with the correct values of your `username` and `password`.


### Deploy with Kubernetes
To deploy Nesis into your kubernetes cluster, run
```commandline
helm upgrade --install my-nesis-instance helm -f helm/values-local.yaml
```
All possible values configuration is documented in the helm [README.md](./helm/README.md) file

## What does Nesis mean?
Nesis is derived from the greek noun gnosis which means knowledge.

## Feedback and Feature Request
💡If you'd like to see a specific feature implemented, feel free to open up a feature request ticket.
If enough users support to have the feature, we will be sure to include it in our roadmap.

🐞If you find any functionality not working as expected, please feel free to open a bug report.

🌟 If you think that this project has been useful to you, please give it a star.

## Origins
This project has been inspired by other open-source projects. Here is a list of some of them;

- [privateGPT](https://github.com/imartinez/privateGPT)
- [localGPT](https://github.com/PromtEngineer/localGPT)
- [llama-cpp](https://github.com/abetlen/llama-cpp-python)
- [Unstructured](https://github.com/Unstructured-IO/unstructured)
- [llama-index](https://github.com/run-llama/llama_index)
