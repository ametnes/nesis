# nesis

![Version: 0.1.2](https://img.shields.io/badge/Version-0.1.2-informational?style=flat-square) ![Type: application](https://img.shields.io/badge/Type-application-informational?style=flat-square) ![AppVersion: 0.0.1](https://img.shields.io/badge/AppVersion-0.0.1-informational?style=flat-square)

A Helm chart for Nesis Enterprise Knowledge Discovery

## Requirements

| Repository | Name | Version |
|------------|------|---------|
| https://charts.bitnami.com/bitnami | memcached | 6.12.1 |
| https://charts.bitnami.com/bitnami | postgresql | 12.12.7 |

## Values

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| affinity | object | `{}` | Global affinity |
| api.autoscaling.enabled | bool | `false` |  |
| api.autoscaling.maxReplicas | int | `11` |  |
| api.autoscaling.minReplicas | int | `3` |  |
| api.autoscaling.targetCPU | string | `""` |  |
| api.autoscaling.targetMemory | string | `""` |  |
| api.config | object | `{}` |  |
| api.customLivenessProbe | object | `{}` |  |
| api.customReadinessProbe | object | `{}` |  |
| api.existingSecret | string | `""` |  |
| api.extraEnvs[0].name | string | `"KUBE_NAMESPACE"` |  |
| api.extraEnvs[0].valueFrom.fieldRef.fieldPath | string | `"metadata.namespace"` |  |
| api.image.pullPolicy | string | `"Always"` |  |
| api.image.repository | string | `"ametnes/nesis"` |  |
| api.image.tag | string | `"latest-api"` |  |
| api.ingress.annotations | object | `{}` |  |
| api.ingress.className | string | `""` |  |
| api.ingress.enabled | bool | `false` |  |
| api.ingress.hosts[0].host | string | `"chart-example.local"` |  |
| api.ingress.hosts[0].paths[0].path | string | `"/"` |  |
| api.ingress.hosts[0].paths[0].pathType | string | `"ImplementationSpecific"` |  |
| api.ingress.tls | list | `[]` |  |
| api.livenessProbe.enabled | bool | `true` |  |
| api.livenessProbe.initialDelaySeconds | int | `5` |  |
| api.livenessProbe.port | string | `"http-api"` |  |
| api.livenessProbe.timeoutSeconds | int | `10` |  |
| api.readinessProbe.enabled | bool | `true` |  |
| api.readinessProbe.initialDelaySeconds | int | `5` |  |
| api.readinessProbe.port | string | `"http-api"` |  |
| api.readinessProbe.timeoutSeconds | int | `1` |  |
| api.replicaCount | int | `1` |  |
| api.resources.limits.cpu | string | `"512m"` |  |
| api.resources.limits.memory | string | `"512Mi"` |  |
| api.resources.requests.cpu | string | `"512m"` |  |
| api.resources.requests.memory | string | `"512Mi"` |  |
| api.secrets | object | `{}` |  |
| api.service.annotations | object | `{}` |  |
| api.service.port | int | `6000` |  |
| api.service.type | string | `"ClusterIP"` |  |
| frontend.autoscaling.enabled | bool | `false` | Enable/disable frontend autoscaling |
| frontend.autoscaling.maxReplicas | int | `11` |  |
| frontend.autoscaling.minReplicas | int | `3` |  |
| frontend.autoscaling.targetCPU | string | `""` |  |
| frontend.autoscaling.targetMemory | string | `""` |  |
| frontend.config | object | `{}` | config: Default configuration for optim as environment variables. These get injected directly in the container. |
| frontend.customLivenessProbe | object | `{}` |  |
| frontend.customReadinessProbe | object | `{}` |  |
| frontend.existingSecret | string | `""` | existingSecret: Specifies an existing secret to be used as environment variables. These get injected directly in the container. |
| frontend.extraEnvs | list | `[{"name":"KUBE_NAMESPACE","valueFrom":{"fieldRef":{"fieldPath":"metadata.namespace"}}}]` | extraEnvs: Extra environment variables |
| frontend.image.pullPolicy | string | `"Always"` |  |
| frontend.image.repository | string | `"ametnes/nesis"` |  |
| frontend.image.tag | string | `"latest-frontend"` |  |
| frontend.ingress.annotations | object | `{}` |  |
| frontend.ingress.className | string | `""` |  |
| frontend.ingress.enabled | bool | `false` |  |
| frontend.ingress.hosts[0].host | string | `"chart-example.local"` |  |
| frontend.ingress.hosts[0].paths[0].path | string | `"/"` |  |
| frontend.ingress.hosts[0].paths[0].pathType | string | `"ImplementationSpecific"` |  |
| frontend.ingress.tls | list | `[]` |  |
| frontend.livenessProbe.enabled | bool | `true` |  |
| frontend.livenessProbe.initialDelaySeconds | int | `5` |  |
| frontend.livenessProbe.port | string | `"http-frontend"` |  |
| frontend.livenessProbe.timeoutSeconds | int | `10` |  |
| frontend.readinessProbe.enabled | bool | `true` |  |
| frontend.readinessProbe.initialDelaySeconds | int | `5` |  |
| frontend.readinessProbe.port | string | `"http-frontend"` |  |
| frontend.readinessProbe.timeoutSeconds | int | `1` |  |
| frontend.replicaCount | int | `1` | Frontend replica count |
| frontend.resources.limits.cpu | string | `"256m"` |  |
| frontend.resources.limits.memory | string | `"512Mi"` |  |
| frontend.resources.requests.cpu | string | `"256m"` |  |
| frontend.resources.requests.memory | string | `"512Mi"` |  |
| frontend.service.annotations | object | `{}` |  |
| frontend.service.port | int | `8000` |  |
| frontend.service.type | string | `"ClusterIP"` |  |
| fullnameOverride | string | `""` | Fullname override |
| imagePullSecrets | list | `[]` | Global image pull secrets |
| memcached.enabled | bool | `true` |  |
| memcached.resources.limits.cpu | string | `"250m"` |  |
| memcached.resources.limits.memory | string | `"256Mi"` |  |
| memcached.resources.requests.cpu | string | `"250m"` |  |
| memcached.resources.requests.memory | string | `"256Mi"` |  |
| nameOverride | string | `""` | Override the charts name partially |
| nodeSelector | object | `{}` | Global node selector |
| podAnnotations | object | `{}` |  |
| podSecurityContext | object | `{}` |  |
| postgresql.auth.postgresPassword | string | `"password"` |  |
| postgresql.enabled | bool | `true` |  |
| postgresql.primary.initdb.password | string | `"password"` |  |
| postgresql.primary.initdb.scripts."createdb.sql" | string | `"CREATE DATABASE nesis;\nCREATE DATABASE embeddings;"` |  |
| postgresql.primary.initdb.user | string | `"postgres"` |  |
| postgresql.primary.persistence.enabled | bool | `true` |  |
| postgresql.primary.persistence.size | string | `"1Gi"` |  |
| postgresql.primary.resources.limits.cpu | string | `"250m"` |  |
| postgresql.primary.resources.limits.memory | string | `"256Mi"` |  |
| postgresql.primary.resources.requests.cpu | string | `"250m"` |  |
| postgresql.primary.resources.requests.memory | string | `"256Mi"` |  |
| rag.autoscaling.enabled | bool | `false` |  |
| rag.autoscaling.maxReplicas | int | `11` |  |
| rag.autoscaling.minReplicas | int | `3` |  |
| rag.autoscaling.targetCPU | string | `""` |  |
| rag.autoscaling.targetMemory | string | `""` |  |
| rag.config | string | `nil` |  |
| rag.enabled | bool | `true` |  |
| rag.extraEnv[0].name | string | `"PYTORCH_MPS_HIGH_WATERMARK_RATIO"` |  |
| rag.extraEnv[0].value | string | `"0.0"` |  |
| rag.extraEnv[1].name | string | `"HF_HUB_CACHE"` |  |
| rag.extraEnv[1].value | string | `"/app/nesis/local_data/models"` |  |
| rag.extraEnv[2].name | string | `"HF_HOME"` |  |
| rag.extraEnv[2].value | string | `"/app/nesis/local_data/models"` |  |
| rag.extraEnv[3].name | string | `"NESIS_RAG_DATA_MODELS_FOLDER"` |  |
| rag.extraEnv[3].value | string | `"/app/nesis/local_data/models"` |  |
| rag.image.pullPolicy | string | `"Always"` |  |
| rag.image.repository | string | `"ametnes/nesis"` |  |
| rag.image.tag | string | `"latest-rag"` |  |
| rag.persistence.accessModes[0] | string | `"ReadWriteOnce"` |  |
| rag.persistence.enabled | bool | `true` |  |
| rag.persistence.path | string | `"/app/nesis/local_data"` |  |
| rag.persistence.size | string | `"10Gi"` |  |
| rag.persistence.storageClass | string | `nil` |  |
| rag.podSecurityContext.fsGroup | int | `7554` |  |
| rag.replicaCount | int | `1` |  |
| rag.resources.limits.cpu | int | `1` |  |
| rag.resources.limits.memory | string | `"1Gi"` |  |
| rag.resources.requests.cpu | int | `1` |  |
| rag.resources.requests.memory | string | `"1Gi"` |  |
| rag.securityContext.runAsGroup | int | `7554` |  |
| rag.securityContext.runAsUser | int | `7554` |  |
| rag.service.annotations | string | `nil` |  |
| rag.service.loadBalancerSourceRanges | list | `[]` |  |
| rag.service.port | int | `8080` |  |
| rag.service.type | string | `"ClusterIP"` |  |
| securityContext | object | `{}` |  |
| serviceAccount.annotations | object | `{}` |  |
| serviceAccount.create | bool | `true` |  |
| tolerations | list | `[]` | Global tolerations |

----------------------------------------------
Autogenerated from chart metadata using [helm-docs v1.13.1](https://github.com/norwoodj/helm-docs/releases/v1.13.1)
