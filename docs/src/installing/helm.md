# Nesis Helm Chart

For your production deployment, use the provided helm chart. Save the overrides values file on your local.

## Installing to Kubernetes

```yaml title="overrides.yml" linenums="1"
api:
  env:
    - name: NESIS_ADMIN_EMAIL
      value: test@domain.com
    - name: NESIS_ADMIN_PASSWORD
      value: password
rag:
  persistence:
    enabled: true
    size: 10Gi
  config: null
  extraEnv:
    - name: OPENAI_API_KEY
      value: <your-openai-api-key>
    - name: HF_TOKEN
      value: <your-hf-token>
    # - name: OPENAI_API_BASE
    #   value: http://
minio:
  enabled: true

```

Then add the helm repository with

```commandline linenums="1"
helm repo add ametnes https://ametnes.github.io/helm
helm repo update
```

Lastly, install Nesis into your kubernetes cluster with

```commandline linenums="1"
helm upgrade --install nesis ametnes/nesis -f /path/to/overrides.yml
```

Shortly after, you should see all services running as shown using `kubectl get po` below
```commandline
NAME                               READY   STATUS    RESTARTS   AGE
nesis-api-664679c8f9-9vzhb         1/1     Running   0          45s
nesis-frontend-5f69fcb4d5-cpnd7    1/1     Running   0          45s
nesis-memcached-7d7855657d-zxd82   1/1     Running   0          45s
nesis-minio-6d458bc7-cpgql         1/1     Running   0          45s
nesis-postgresql-0                 1/1     Running   0          45s
nesis-rag-757584f46c-9kqtf         1/1     Running   0          45s
```

???+ note "RAG Configuration"

    1. You need to set the `OPENAI_API_KEY` and `OPENAI_API_BASE` environment variables before you can start chatting
    with your documents.
    2. We noticed that some Huggingface embeddings models can only be used after authenticating with Huggingface. If you
    encounter 401s during embeddings generation, you need to obtain a Huggingface token and populate the `HF_TOKEN` environment
    variable.

## Testing your Nesis

1. Port forward services;
   ```commandline title="Nesis Frontend"
   kubectl port-forward svc/nesis-minio 9001
   ```

2. Point your browser to <a href="http://localhost:9001" target="_blank">http://localhost:9001</a> and login with `admin`:`password`.
   
3. In another terminal;
   ```commandline title="MinIO Frontend"
   kubectl port-forward svc/nesis-frontend 8000
   ```
   
4. Point your browser to <a href="http://localhost:8000" target="_blank">http://localhost:8000</a> and login with `test@domain.com`:`password`.
   
5. Upload documents into the MinIO bucket `private-documents`.
6. In the `Nesis Frontend` add a datasource with;
      7. Navigate to **Settings**->**Datasources**.
      8. Click **Add**.
      9. Enter
         10. **Type**: _MinIO (S3 Compatible)_
         11. **Name**: _ds-private-documents_
         11. **Entpoint**: _http://nesis-minio:9000_
         11. **User**: _admin_
         11. **Password**: _password_
         11. **Dataobjects**: _private-documents_
      12. Click **Save**.
13. In the datasource list, find the datasource you just created and click the _**Ingest**_ button.
14. View logs of your services using `kubetail` with
    ```commandline
    kt nesis
    ```
15. Once ingestion is complete, navigate to **Documents** and you can start chating with your documents.

## Overriding Key Dependencies

The Nesis helm chart allows you to override the following components;

1. Postgres database that backs the API component.
2. Memcached caching service.
3. Vector database


???+ tip "Resource requirements"

    1. The Frontend and API microservices are lightweight and don't need alot of resources.
    2. The RAG Engine however needs to be scoped for enough memory, cpu and storage.
    3. The Postgres database needs enough memory and storage because every ingested document.

