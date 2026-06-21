import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.tools import tool
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_classic.agents import create_tool_calling_agent, AgentExecutor


print(" after imports")
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")
print("after api key")

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
    return read_bio()
    

    
    
llm = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite", google_api_key=API_KEY)
print("created llm")
class BioResponse(BaseModel):
    summary: str = Field(description="Answer to the user's question, 30 words or less.")
    is_relevant: bool = Field(description="True if the question is about Jose Pantoja Morales, False otherwise.")
    
parser = PydanticOutputParser(pydantic_object=BioResponse)

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", "{query}"),
    ("placeholder", "{agent_scratchpad}"),
]).partial(format_instructions=parser.get_format_instructions())

tools = [get_personal_info]

agent = create_tool_calling_agent(llm, tools, prompt)

print("agent init")
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=False)

response = agent_executor.invoke({"query": "what technologies did jose use for fabflix?"})
print(response)