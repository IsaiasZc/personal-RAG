import gradio as gr
from llama_index.llms.openai import OpenAI
from llama_index.core import SQLDatabase
from sqlalchemy import create_engine
from llama_index.core.prompts import PromptTemplate
from llama_index.core.query_engine import NLSQLTableQueryEngine
import dotenv

dotenv.load_dotenv()

# create the engine and the LLM
llm_gpt = OpenAI(model="gpt-4o-mini", temperature=0.1)

engine = create_engine("sqlite:///data/out/recipes.db")
sql_database = SQLDatabase(
    engine=engine, include_tables=["recipes"], sample_rows_in_table_info=2
)


# Tune the model
PROMPT_MODEL = """
Given an input question, synthesize a response from the query results.

If the question is about a recipe, provide the recipe details in a friendly and helpful manner.
If the answer is not in the database, respond kindly with "I’m sorry, I don't have that information at the moment, but I’d love to help you with something else."
If the question is not about a recipe, respond warmly with "I specialize in recipes, and I'd be delighted to assist you with any culinary questions you have!"

You are a friendly and gentle chatbot with a warm personality.

Query: {query_str}
SQL: {sql_query}
SQL Response: {context_str}
Response:
"""

response_synthesis_prompt = PromptTemplate(
    template=PROMPT_MODEL,
)

## SQL prompt template
SQL_PROMPT_MODEL = """
Given an input question, first create a syntactically correct {dialect} query to run, then look at the results of the query and return the answer. You can order the results by a relevant column to return the most interesting examples in the database.

Never query for all the columns from a specific table, only ask for a few relevant columns given the question.

Remember you are a chatbot to make recipes, sometimes you will need to choose a menu for a specific occasion, or find a recipe based on a specific ingredient. realiza varias consultas SQL si es necesario para obtener diferentes comidas de diferentes categorias.

Pay attention to use only the column names that you can see in the schema description. Be careful to not query for columns that do not exist. Pay attention to which column is in which table. Also, qualify column names with the table name when needed. You are required to use the following format, each taking one line:

Question: Question here
SQLQuery: SQL Query to run
SQLResult: Result of the SQLQuery
Answer: Final answer here

Only use tables listed below.
{schema}

To assist in understanding user queries that may not match exactly with the database terms, try to infer the most relevant keywords or synonyms based on the context of the user's question.

You are a friendly and gentle chatbot with a warm personality. Always respond in a kind and helpful manner.

Question: {query_str}
SQLQuery:
"""

text_to_sql_prompt = PromptTemplate(
    template=SQL_PROMPT_MODEL,
    type="text-to-sql",
)



# create the query engine with the configuration
query_engine = NLSQLTableQueryEngine(
    sql_database=sql_database,
    tables=["recipes"],
    llm=llm_gpt,
    response_synthesis_prompt=response_synthesis_prompt,
    text_to_sql_prompt=text_to_sql_prompt,
)


def conversation(query, history=None):
    response = query_engine.query(query)
    return response.response


demo = gr.ChatInterface(conversation)

demo.launch()
