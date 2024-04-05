import logging
import typing

from injector import inject, singleton
from llama_index.core import VectorStoreIndex
from llama_index.core.indices.vector_store import VectorIndexRetriever
from llama_index.core.vector_stores.types import (
    VectorStore,
    MetadataFilters,
    MetadataFilter,
)

from nesis.rag.core.open_ai.extensions.context_filter import ContextFilter
from nesis.rag.core.paths import local_data_path
from nesis.rag.core.settings.settings import Settings

logger = logging.getLogger(__name__)


@typing.no_type_check
def _chromadb_metadata_filter(
    context_filter: ContextFilter | None,
) -> dict | None:
    if context_filter is None or not any(
        [context_filter.docs_ids, context_filter.filters]
    ):
        return {}  # No filter

    if context_filter.docs_ids is not None:
        if len(context_filter.docs_ids) < 1:
            return {"doc_id": "-"}  # Effectively filtering out all docs
        else:
            doc_filter_items = []
            if len(context_filter.docs_ids) > 1:
                doc_filter = {"$or": doc_filter_items}
                for doc_id in context_filter.docs_ids:
                    doc_filter_items.append({"doc_id": doc_id})
            else:
                doc_filter = {"doc_id": context_filter.docs_ids[0]}
            return doc_filter

    if context_filter.filters is not None:
        filters = {}
        for key, value in context_filter.filters.items():
            if isinstance(value, list):
                filters[key] = {"$in": value}
        return filters


@typing.no_type_check
def _qdrant_metadata_filter(
    context_filter: ContextFilter | None,
) -> list | None:
    if context_filter is None or context_filter.filters is None:
        return {}  # No filter
    else:
        filters = []
        for key, value in context_filter.filters.items():
            if isinstance(value, list):
                for item in value:
                    filters.append({"key": key, "match": {"value": item}})
            else:
                filters.append({"key": key, "match": {"value": value}})
        return filters


@singleton
class VectorStoreComponent:
    vector_store: VectorStore

    @inject
    def __init__(self, settings: Settings) -> None:
        match settings.vectorstore.database:
            case "chroma":
                try:
                    import chromadb  # type: ignore
                    from nesis.rag.core.components.vector_store.batched_chroma import (
                        BatchedChromaVectorStore,
                    )
                    from chromadb.config import (  # type: ignore
                        Settings as ChromaSettings,
                    )
                except ImportError as e:
                    raise ImportError(
                        "'chromadb' is not installed."
                        "To use PrivateGPT with Chroma, install the 'chroma' extra."
                        "`poetry install --extras chroma`"
                    ) from e

                chroma_settings = ChromaSettings(anonymized_telemetry=False)
                chroma_client = chromadb.PersistentClient(
                    path=str((local_data_path / "chroma_db").absolute()),
                    settings=chroma_settings,
                )
                chroma_collection = chroma_client.get_or_create_collection(
                    "make_this_parameterizable_per_api_call"
                )  # TODO

                self.vector_store = typing.cast(
                    VectorStore,
                    BatchedChromaVectorStore(
                        chroma_client=chroma_client, chroma_collection=chroma_collection
                    ),
                )

            case "qdrant":
                from llama_index.vector_stores.qdrant import QdrantVectorStore
                from qdrant_client import QdrantClient

                if settings.qdrant is None:
                    logger.info(
                        "Qdrant config not found. Using local filesystem for persistence."
                    )
                    client = QdrantClient(
                        path=str((local_data_path / "qdrant_db").absolute())
                    )
                else:
                    client = QdrantClient(
                        **settings.qdrant.model_dump(exclude_none=True)
                    )
                self.vector_store = typing.cast(
                    VectorStore,
                    QdrantVectorStore(
                        client=client,
                        collection_name="make_this_parameterizable_per_api_call",
                    ),  # TODO
                )
            case "pgvector":
                from llama_index.vector_stores.postgres import PGVectorStore
                from sqlalchemy.engine import make_url

                if settings.pgvector.url:
                    params = make_url(settings.pgvector.url)
                    settings.pgvector.database = (
                        params.database or settings.pgvector.database
                    )
                    settings.pgvector.host = params.host or settings.pgvector.host
                    settings.pgvector.port = params.port or settings.pgvector.port
                    settings.pgvector.user = params.username or settings.pgvector.user
                    settings.pgvector.password = (
                        params.password or settings.pgvector.password
                    )

                self.vector_store = typing.cast(
                    VectorStore,
                    PGVectorStore.from_params(
                        embed_dim=settings.pgvector.dimensions,  # openai embedding dimension
                        database=settings.pgvector.database,
                        host=settings.pgvector.host,
                        password=settings.pgvector.password,
                        port=settings.pgvector.port,
                        user=settings.pgvector.user,
                        table_name=settings.pgvector.table,
                    ),
                )

            case _:
                # Should be unreachable
                # The settings validator should have caught this
                raise ValueError(
                    f"Vectorstore database {settings.vectorstore.database} not supported"
                )

    @staticmethod
    def get_retriever(
        index: VectorStoreIndex,
        context_filter: ContextFilter | None = None,
        similarity_top_k: int = 2,
    ) -> VectorIndexRetriever:
        metadata_filters = None
        if context_filter is not None and context_filter.filters is not None:
            metadata_filters = MetadataFilters(
                filters=[
                    MetadataFilter(key=key, value=value, operator="==")
                    for key, value_list in context_filter.filters.items()
                    for value in value_list
                ],
                condition="or",
            )
        return VectorIndexRetriever(
            index=index,
            similarity_top_k=similarity_top_k,
            filters=metadata_filters,
        )

    def close(self) -> None:
        if hasattr(self.vector_store.client, "close"):
            self.vector_store.client.close()
