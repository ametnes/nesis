
<p align="center">
  <img height="100" src="https://raw.githubusercontent.com/ametnes/nesis/main/nesis/frontend/client/src/images/NesisIcon.svg" alt="Nesis" title="Nesis">
</p>

![Frontend](https://github.com/ametnes/nesis/actions/workflows/test_frontend.yml/badge.svg) ![API](https://github.com/ametnes/nesis/actions/workflows/test_api.yml/badge.svg)  ![RAG](https://github.com/ametnes/nesis/actions/workflows/test_rag.yml/badge.svg) [![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

## Built with ❤️ by [**_Ametnes_**](https://cloud.ametnes.com/)

---
# 👋 What is Nesis❓

Enterprise ready knowledge discovery solution that empowers users to
1. Interact with vast document repositories in a conversational AI style.
2. Control access to the document repositories using Role Based Access Controls.
3. Connects to vast number of repositories such as S3, Windows Shares, MinIO
4. Can be deployed in your cloud or on-premises.


## Overview
Nesis is an open-source enterprise knowledge discovery solution that connects to multitudes of datasource, collecting
information and making it available in a conversation manner. Nesis leverages generative AI to aggregate information
collected from documents in multiple formats such as pdf, docx, xlsx.

## Main features
Nesis is built to handle large amounts of data at scale. Enabling connectivity to multitudes of datasources, 
Nesis is able to transform data in various formats into vector embeddings to be used by your LLM of choice.

## Deployment
Nesis is packaged with container technology and is able to run within any containerized orchestrated environment such as docker compose and kubernetes.

## What does Nesis mean
Nesis is derived from the greek noun gnosis which means knowledge.

## Getting started
To get started with Nesis

1. Obtain your **OPENAI_API_KEY** and update the compose.yml file entry.
2. Start all services locally with the provided docker compose file.

   ```commandline
   docker-compose -f compose.yml up
   ```

2. Then connect to your instance via http://localhost:58000 and login with email/password = some.email@domain.com/password
3. Connect to your minio instance via http://localhost:59001/ and login username/password = your_username/your_password
4. Upload some document in your minio `documents` bucket
5. Back in your Nesis page, register the minio datasource with
   1. Navigate to **Settings** -> **Datasource**
   2. Enter the details;
   
      1. Type: **S3 Compatible**
      4. Name: **documents**
      5. Host: **http://minio:9000/**
      6. Username: **your_username**
      7. Password: **your_password**
      8. Click **Create**
9. After about 5 minutes, the background process will start indexing documents and then you should be able to query your documents.

## Feedback and Feature Request
💡If you'd like to see a specific feature implemented, feel free to open up a feature request ticket.
If enough users support to have the feature, we will be sure to include it in our roadmap.

🐞If you find any functionality not working as expected, please feel free to open an bug report.

🌟 If you think that this project has been useful to you, please give it a star, this way we know
that we are building what you really want.
