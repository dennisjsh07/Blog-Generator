from langgraph.graph import StateGraph, START, END
from src.states.blogstate import BlogState, Blog
from src.nodes.blog_node import BlogNode


class GraphBuilder:
    def __init__(self, llm):
        self.graph = StateGraph(BlogState)
        self.llm = llm

    ## build graph
    def build_topic_graph(self):
        """
        Build a graph to generate blogss based on topic
        """

        self.blog_node = BlogNode(self.llm)
        # add nodes
        self.graph.add_node("title_creation", self.blog_node.title_creation)
        self.graph.add_node("content_generation", self.blog_node.content_generation)

        # add edges
        self.graph.add_edge(START, "title_creation")
        self.graph.add_edge("title_creation", "content_generation")
        self.graph.add_edge("content_generation", END)

        return self.graph

    ## build language translation graph
    def build_language_graph(self):
        """
        Build a graph for blog generation with inputs topic and language
        """

        self.blog_node = BlogNode(self.llm)
        # add nodes
        self.graph.add_node("title_creation", self.blog_node.title_creation)
        self.graph.add_node("content_generation", self.blog_node.content_generation)
        self.graph.add_node(
            "hindi_translation",
            lambda state: self.blog_node.translation({**state, "current_language": "hindi"}),
        )
        self.graph.add_node(
            "french_translation",
            lambda state: self.blog_node.translation({**state, "current_language": "french"}),
        )
        self.graph.add_node("route", self.blog_node.route)

        # add edges
        self.graph.add_edge(START, "title_creation")
        self.graph.add_edge("title_creation", "content_generation")
        self.graph.add_edge("content_generation", "route")
        self.graph.add_conditional_edges(
            "route",
            self.blog_node.route_decision,
            {"hindi": "hindi_translation", "french": "french_translation"},
        )
        self.graph.add_edge("hindi_translation", END)
        self.graph.add_edge("french_translation", END)

        return self.graph

    ## setup the graph
    def setup_graph(self, usecase):
        if usecase == "topic":
            self.build_topic_graph()
        if usecase == "language":
            print("language block")
            self.build_language_graph()

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
graph = graph_builder.build_language_graph().compile()
