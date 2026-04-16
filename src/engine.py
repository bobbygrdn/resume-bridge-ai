from qdrant_client import QdrantClient, AsyncQdrantClient
from llama_index.core import StorageContext
from llama_index.vector_stores.qdrant import QdrantVectorStore
from dotenv import load_dotenv
from llama_index.core.program import LLMTextCompletionProgram
from llama_index.llms.openai import OpenAI
from llama_index.core import Document, VectorStoreIndex
from src.schema import ResumeProfile

load_dotenv()

client = QdrantClient(url="http://localhost:6333")

aclient = AsyncQdrantClient(url="http://localhost:6333")

def init_storage(collection_name: str = "resume_collection"):
    """
    Initializes the Qdrant Vector Store and LlamaIndex Storage Context.
    This is the 'handshake' between your code and the database.
    """
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

extraction_program = LLMTextCompletionProgram.from_defaults(
    output_cls=ResumeProfile,
    prompt_template_str=(
        "You are an expert technical recruiter. Extract professional information "
        "from the following resume text. Create a compelling 'headline' that "
        "summarizes their expertise and intent.\n\n"
        "RESUME TEXT:\n{text}"
    ),
    llm=OpenAI(model="gpt-4o-mini", temperature=0)
)

async def process_resume_pdf(text: str, storage_context):
    """
    1. Extracts structured JSON from raw text.
    2. Creates a LlamaIndex Document with metadata.
    3. Persists the vector to Qdrant.
    """

    profile = extraction_program(text=text)

    doc = Document(
        text=text,
        metadata=profile.model_dump()
    )

    index = VectorStoreIndex.from_documents(
        [doc],
        storage_context=storage_context
    )

    return profile