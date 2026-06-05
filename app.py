from fastapi import FastAPI, Request
from src.graphs.graph_builder import GraphBuilder
from langchain_groq import ChatGroq

import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

os.environ["LANGSMITH_API_KEY"] = os.getenv("LANGCHAIN_API_KEY")


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/blogs")
async def create_blogs(request: Request):
    # get the input body
    data = await request.json()
    topic = data.get("topic", "")
    language = data.get("language", "")

    # if topic is present invoke the graph and return the response
    os.environ["GROQ_API_KEY"] = groq_api_key = os.getenv("GROQ_API_KEY")
    llm = ChatGroq(api_key=groq_api_key, model="llama-3.1-8b-instant")
    graph_builder = GraphBuilder(llm)

    if topic and language:
        graph = graph_builder.setup_graph(usecase="language")
        state = graph.invoke(
            {
                "topic": topic,
                "current_language": language.lower(),
            }
        )

    elif topic:
        graph = graph_builder.setup_graph(usecase="topic")
        state = graph.invoke({"topic": topic})

    return {"data": state}
