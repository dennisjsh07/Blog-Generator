from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage


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

    # translation node
    def translation(self, state: BlogState):
        """
        Translate the content to the specified language.
        """
        translation_prompt = """
        Translate the following blog into {current_language}.

        Return JSON:

        {{
            "title": "...",
            "content": "..."
        }}

        TITLE:
        {title}

        CONTENT:
        {content}
        """

        translated_blog = self.llm.with_structured_output(Blog).invoke(
            translation_prompt.format(
                current_language=state["current_language"],
                title=state["blog"]["title"],
                content=state["blog"]["content"],
            )
        )

        return {"blog": translated_blog}

    # route node
    def route(self, state: BlogState):
        return {"current_language": state["current_language"]}

    # route_decision conditional node
    def route_decision(self, state: BlogState):
        """
        Route the content to the respective translation function.
        """
        if state["current_language"] == "hindi":
            return "hindi"
        elif state["current_language"] == "french":
            return "french"
        else:
            return state["current_language"]

    ## build graph
    def build_topic_graph(self):
        """
        Build a graph to generate blogss based on topic
        """
        # add nodes
        self.graph.add_node("title_creation", self.title_creation)
        self.graph.add_node("content_generation", self.content_generation)

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
        # add nodes
        self.graph.add_node("title_creation", self.title_creation)
        self.graph.add_node("content_generation", self.content_generation)
        self.graph.add_node(
            "hindi_translation",
            lambda state: self.translation({**state, "current_language": "hindi"}),
        )
        self.graph.add_node(
            "french_translation",
            lambda state: self.translation({**state, "current_language": "french"}),
        )
        self.graph.add_node("route", self.route)

        # add edges
        self.graph.add_edge(START, "title_creation")
        self.graph.add_edge("title_creation", "content_generation")
        self.graph.add_edge("content_generation", "route")
        self.graph.add_conditional_edges(
            "route",
            self.route_decision,
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
graph = graph_builder.build_topic_graph().compile()
