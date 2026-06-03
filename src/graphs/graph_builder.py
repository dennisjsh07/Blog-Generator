from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict
from pydantic import BaseModel, Field


class Blog(BaseModel):
    title: str = Field(description="the title of the blog post")
    content: str = Field(description="Main content of the blog post")


class BlogState(TypedDict):
    topic: str
    blog: Blog
    current_language: str


class GraphBuilder:
    def __init__(self, llm):
        self.graph = StateGraph(BlogState)
        self.llm = llm

    ## create nodes
    # title creation node
    def title_creation(self, state: BlogState):
        """
        create the title for the blog
        """

        # check if topic key exists and its value is not empty
        if "topic" in state and state["topic"]:
            prompt = """
                   You are an expert blog content writer. Use Markdown formatting. Generate
                   a blog title for the {topic}. This title should be creative, SEO friendly and concise
                   Not more than a single sentence
                   """
            system_message = prompt.format(topic=state["topic"])
            response = self.llm.invoke(system_message)
            return {"blog": {"title": response.content}}

    # content generation node
    def content_generation(self, state: BlogState):
        """
        create the content for the blog
        """

        # check if topic key exists and its value is != empty
        if "topic" in state and state["topic"]:
            prompt = """You are expert blog writer. Use Markdown formatting.
            Generate a detailed blog content with detailed breakdown for the {topic}"""
            system_message = prompt.format(topic=state["topic"])
            response = self.llm.invoke(system_message)
            return {
                "blog": {"title": state["blog"]["title"], "content": response.content}
            }

    ## build graph
    def build_topic_graph(self):
        # add nodes
        self.graph.add_node("title_creation", self.title_creation)
        self.graph.add_node("content_generation", self.content_generation)

        # add edges
        self.graph.add_edge(START, "title_creation")
        self.graph.add_edge("title_creation", "content_generation")
        self.graph.add_edge("content_generation", END)

        return self.graph

    ## setup the graph
    def setup_graph(self, usecase):
        if usecase == "topic":
            self.build_topic_graph()

        return self.graph.compile()


## below code is for langsmith langgraph studio
from langchain_groq import ChatGroq
import os
from dotenv import load_dotenv

load_dotenv()

os.environ["GROQ_API_KEY"] = groq_api_key = os.getenv("GROQ_API_KEY")
llm = ChatGroq(api_key=groq_api_key, model="llama-3.1-8b-instant")

# get the graph
graph_builder = GraphBuilder(llm)
graph = graph_builder.build_topic_graph().compile()
