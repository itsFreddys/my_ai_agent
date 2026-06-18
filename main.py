import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import initialize_agent, AgentType
from langchain.tools import tool
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

system_prompt = """
You are an AI assistant for Jose Pantoja Morales. 
1. Use the provided tools to answer questions about his history, education, and projects.
2. If a question is NOT about Jose or his professional background, set 'is_relevant' to False and apologize politely.
3. Keep the summary under 30 words.
4. Output ONLY in the format: {format_instructions}
"""

def read_bio():
    with open("bio.md", "r") as file:
        return file.read()
    
@tool
def get_personal_info(query: str) -> str:
    """
    Use this tool to answer questions about Jose Pantoja's education,
    professional history, projects, and skills.
    """
    read_bio()
    

    
    
llm = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite", google_api_key=API_KEY)

class BioResponse(BaseModel):
    summary: str = Field(description="Answer to the user's question, 30 words or less.")
    is_relevant: bool = Field(description="True if the question is about Jose Pantoja Morales, False otherwise.")
    
parser = PydanticOutputParser(pydantic_object=BioResponse)

prompt = ChatPromptTemplate.from_messages([
    ("system", 
     """
        You are an AI assistant for Jose Pantoja Morales. 
        1. Use the provided tools to answer questions about his history, education, and projects.
        2. If a question is NOT about Jose or his professional background, set 'is_relevant' to False and apologize politely.
        3. Keep the summary under 30 words.
        4. Output ONLY in the format: {format_instructions}
    """
     ),
    ("human", "{query}"),
    ("placeholder", "{agent_scratchpad}"),
]).partial(format_instructions=parser.get_format_instructions())

tools = [get_personal_info]

agent = initialize_agent(
    tools,
    llm,
    agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True
)

response = agent.run("what technologies did jose use for fabflix?")
print(response)