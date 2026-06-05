from src.states.blogstate import BlogState, Blog
from langchain_core.messages import HumanMessage, SystemMessage


class BlogNode:
    def __init__(self, llm):
        self.llm = llm

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
        Translate the blog into the target language.
        """
        current_language = state["current_language"]
        title = state["blog"]["title"]
        content = state["blog"]["content"]

        title_prompt = """Translate this title into {lang}.

        Title:
        {t}

        Return only the translated title."""

        content_prompt = """Translate the following content into {lang}.

        Preserve markdown formatting.

        Content:
        {c}"""

        translated_title = self.llm.invoke(
            title_prompt.format(lang=current_language, t=title)
        )
        translated_content = self.llm.invoke(
            content_prompt.format(lang=current_language, c=content)
        )

        return {
            "blog": {
                "title": translated_title.content,
                "content": translated_content.content,
            }
        }

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
