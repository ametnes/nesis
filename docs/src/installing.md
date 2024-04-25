# Installing Nesis
Nesis is built cloud native container from ground up. You have multiple deployment options for Nesis;

## Docker Compose
For your quick local test, a <a href="https://github.com/ametnes/nesis/blob/main/compose.yml" target="_blank">docker compose</a> file is provided which you can
run to standup a local instance of Nesis.

## Nesis Helm Chart

For your production deployment, use the provided helm chart. Save the overrides values file on your local.

### Installing to Kubernetes

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

### Testing

1. Port forward services;
   ```commandline title="Nesis Frontend"
   kubectl port-forward svc/nesis-minio 8000
   ```

2. Point your browser to [http://localhost:8000](http://localhost:8000) and login with `test@domain.com`:`password`.
   
3. In another terminal;
   ```commandline title="MinIO Frontend"
   kubectl port-forward svc/nesis-frontend 8000
   ```
   
4. Point your browser to [http://localhost:9001](http://localhost:9001) and login with `admin`:`password`.
   
5. Upload documents into the MinIO bucket `private-documents`.
6. In the `Nesis Frontend` add a datasource with;
      7. Navigate to **Settings**->**Datasources**.
      8. Click **Add**.
      9. Enter
         10. **Type**: _**MinIO (S3 Compatible)**_
         11. **Name**: _**ds-private-documents**_
         11. **Entpoint**: _**http://nesis-minio:9000**_
         11. **User**: _**admin**_
         11. **Password**: _**password**_
         11. **Dataobjects**: _**private-documents**_
      12. Click **Save**.
13. In the datasource list, find the datasource you just created and click the _**Ingest**_ button.
14. View logs of your services using `kubetail` with
    ```commandline
    kt nesis
    ```
15. Once ingestion is complete, navigate to **Documents** and you can start chating with your documents.

### Overriding Key Dependencies

The Nesis helm chart allows you to override the following components;

1. Postgres database that backs the API component.
2. Memcached caching service.
3. Vector database

## Ametnes Platform

The Ametnes Platform helps orchestrate your business applications wherever you host them. This can be in your private
data-center, in AWS, GCP or Azure.

Nesis is available on the Ametnes Platform and can be deployed in your kubernetes cluster wherever you host it.

The first step is to setup your kubernetes cluster as an Ametnes Application Location. See these detailed <a href="https://cloud.ametnes.com/docs/concepts/data-service-location/" target="_blank">instructions</a>.

### Create the service

Log into your Ametnes Cloud console at <a href="https://cloud.ametnes.com/console/signin" target="_blank">here</a>
or sign up <a href="https://cloud.ametnes.com/console/signup" target="_blank">here</a> if you do not have one.

1. Using the **Services** left menu, navigate to the service management dashboard.
2. Click **New Service**.
3. Enter the **__Nesis__** to filter from the list and select **__Create__**
4. In the displayed form, enter the following info.
    1. Enter the **Name**: `Nesis-Service-DSL1` and **Description**: `Nesis-Service-DSL1`.
    2. Select a **Version** from the list.
    3. Select the **Location**.
    4. Set the `OPENAI_API_KEY` and the `HF_TOKEN` keys.
    4. Click `Create`.

### Test connectivity

1. Using the **Services** left menu, navigate to the service management dashboard. Your service should be listed.

    !!! note "Service not showing"
        If your service list is empty, use the filter at the top right corner, to filter for ALL services.

2. After a while, your data service status will change to `ready`.
2. To the right of your service, click the `Admin` button and you will navigate to your service's details page.
3. At the bottom of the page, copy the endpoint of your service as well as your username/key and password.
4. In your browser, paste the URL `https://<your.instance.host.name>/`.
5. You should get a prompt to login.

### Clean up

#### Delete all services
1. In your Ametnes Cloud console, navigate to the **Admin** section of each service
2. Delete the service.

