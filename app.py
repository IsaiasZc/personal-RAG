import gradio as gr
import chromadb
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.llms.openai import OpenAI
from llama_index.core import Settings, VectorStoreIndex
from llama_index.embeddings.openai import OpenAIEmbedding
from chromadb.config import Settings as StChroma



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

embed_model = Settings.embed_model

chroma_client = chromadb.PersistentClient(
    path="./notebooks/chroma_recipe", settings=StChroma(allow_reset=True)
)
chroma_collection = chroma_client.get_or_create_collection(name="recipes")

vector_store = ChromaVectorStore(chroma_collection=chroma_collection)


index = VectorStoreIndex.from_vector_store(
    vector_store=vector_store,
    embed_model=embed_model,
)

query_engine = index.as_query_engine()

def conversation(query, history=None):
    """Conversational agent that provides nutrition advice based on a dataset of recipes."""

    role_instruction = (
    "You are a professional nutritionist and your goal is to provide accurate and personalized nutrition advice. "
    "Your responses should be clear, helpful, and based on the recipes and nutritional data available in the dataset. "
    "When asked about specific ingredients, provide detailed nutritional information, benefits, and suggestions on how to incorporate them into meals. "
    "When asked about caloric content or dietary requirements, offer advice on daily intake, portion control, and balancing macronutrients. "
    "If the user asks for a recipe or meal plan, suggest options from the dataset that align with their preferences or dietary needs. "
    "Make sure to organize meal plans in a structured and easy-to-follow manner. "
    "Always ensure that the information is clear and understandable for a general audience, using simple language when necessary."
)

    conversation_history = "\n".join([f"User: {q}\nBot: {r}" for q, r in history[-5:]])

    modified_query = f"{role_instruction}\n{conversation_history}\nUser: {query}"

    print("history\n"+str(history[-5:])+"\n")
    response = query_engine.query(modified_query)
    return response.response


demo = gr.ChatInterface(conversation)

demo.launch()
