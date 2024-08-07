import gradio as gr
import chromadb
from llama_index.vector_stores.chroma import ChromaVectorStore

from llama_index.core import Settings, VectorStoreIndex, StorageContext
from chromadb.config import Settings as StChroma


from llama_index.llms.openai import OpenAI

# from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.embeddings.openai import OpenAIEmbedding
import dotenv

dotenv.load_dotenv()

# create the engine and the LLM
# configure the llm and the embedding model
llm = OpenAI(
    model="gpt-4o-mini",
    temperature=0.5,
)

Settings.llm = llm
Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small")

chroma_client = chromadb.PersistentClient(
    path="./chroma_recipe", settings=StChroma(allow_reset=True)
)
chroma_collection = chroma_client.get_or_create_collection(name="recipes")

vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
storage_context = StorageContext.from_defaults(vector_store=vector_store)


index = VectorStoreIndex.from_vector_store(
    vector_store=vector_store,
    storage_context=storage_context,
)

query_engine = index.as_query_engine()


def conversation(query, history=None):
    response = query_engine.query(query)
    return response.response


demo = gr.ChatInterface(conversation)

demo.launch()
