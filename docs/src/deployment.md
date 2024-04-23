# Deploying Nesis
Nesis has been built around cloud native container deployment.
You have multiple deployment options for Nesis however they all 

## Docker Compose
For your quick local test, a <a href="https://github.com/ametnes/nesis/blob/main/compose.yml" target="_blank">docker compose</a> file is provided which you can
run to standup a local instance of Nesis.

## Nesis Helm Chart

For your production deployment, use the provided helm chart. Save the overrides values file on your local.

```yaml title="overrides.yml" linenums="1"
api:
  env:
    - name: NESIS_ADMIN_EMAIL
      value: test@domain.com
    - name: NESIS_ADMIN_PASSWORD
      value: password

rag:
  podSecurityContext:
    fsGroup: 2002
  securityContext:
    runAsUser: 1001
    runAsGroup: 2002

  persistence:
    enabled: true
    size: 10Gi
  
  extraEnv:
    - name: OPENAI_API_KEY
      value: sk-
    # - name: OPENAI_API_BASE
    #   value: http://
    - name: NESIS_RAG_EMBEDDING_DIMENSIONS
      value: "384"
    - name: NESIS_RAG_EMBEDDING_MODE
      value: local
    - name: HF_TOKEN
      value: hf-
  config: null

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

???+ note "RAG Configuration"

    1. You need to set the `OPENAI_API_KEY` and `OPENAI_API_BASE` environment variables before you can start chatting
    with your documents.
    2. We noticed that some Huggingface embeddings models can only be used after authenticating with Huggingface. If you
    encounter 401s during embeddings generation, you need to obtain a Huggingface token and populate the `HF_TOKEN` environment
    variable.



## Ametnes Platform
