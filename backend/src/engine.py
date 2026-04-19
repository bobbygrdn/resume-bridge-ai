from qdrant_client import QdrantClient, AsyncQdrantClient, models
from llama_index.core import StorageContext
from llama_index.vector_stores.qdrant import QdrantVectorStore
from dotenv import load_dotenv

from llama_index.core import Document, VectorStoreIndex
from src.schema import ResumeProfile
from src.logging_utils import log_queue

load_dotenv()

client = QdrantClient(url="http://qdrant:6333")
aclient = AsyncQdrantClient(url="http://qdrant:6333")

def init_storage(collection_name: str = "resume_collection"):
    try:
        vector_store = QdrantVectorStore(
            client=client,
            aclient=aclient,
            collection_name=collection_name
        )
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        print(f"✅ Successfully connected to Qdrant collection: '{collection_name}'")
        return storage_context
    except Exception as e:
        print(f"❌ Connection Failed: {str(e)}")
        raise e

try:
    default_storage_context = init_storage()
except Exception:
    default_storage_context = None



async def process_resume_pdf(text: str, storage_context, user_id: str):
    """
    1. Checks if the collection exists.
    2. Deletes only points for the specific user_id.
    3. Persists the new identity.
    """
    collections = client.get_collections().collections
    if any(c.name == "resume_collection" for c in collections):
        client.delete(
            collection_name="resume_collection",
            points_selector=models.FilterSelector(
                filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="user_id",
                            match=models.MatchValue(value=user_id)
                        )
                    ]
                )
            )
        )
        await log_queue.put(f"🧹 Cleared old points for user: {user_id}")

    profile = extraction_program(text=text)

    metadata = profile.model_dump()
    metadata["user_id"] = user_id

    doc = Document(text=text, metadata=metadata)
    
    VectorStoreIndex.from_documents([doc], storage_context=storage_context)

    return profile