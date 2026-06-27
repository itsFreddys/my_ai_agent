from http.server import BaseHTTPRequestHandler
import json
import os
import datetime
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.tools import tool
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_classic.agents import create_tool_calling_agent, AgentExecutor
# made revert to a earlier version
# Load environment variables
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")

system_prompt = """
You are an AI assistant for Jose Pantoja Morales. 
1. Use the provided tools to answer questions about his history, education, and projects.
2. If a question is NOT about Jose or his professional background, set 'is_relevant' to False and reply None for the summary.
3. Keep the summary under 30 words.
4. Output ONLY in the format: {format_instructions}
"""
irrelevant_reply = "I am sorry, but I can only answer questions related to Jose Pantoja Morales and his professional background."

# --- Agent Initialization ---
def read_bio():
    with open("bio.md", "r") as file:
        return file.read()

@tool
def get_personal_info(query: str) -> str:
    """Use this tool to answer questions about Jose Pantoja's education, history, projects, and skills."""
    return read_bio()

def collect_query_data(query: str, raw_result) -> json:
    """
    Use this tool to append/write to a file what the user's query was and the return statement.
    """
    timestamp = datetime.datetime.now().isoformat(sep=' ', timespec='seconds')
    output_text = raw_result['output'][0]['text']
    json_data = json.loads(output_text)
    is_relevant = json_data['is_relevant']
    summary = json_data['summary'] if is_relevant  else irrelevant_reply
    
    print(f"LOG | {timestamp} | query: {query} | summary: {summary} | revelancy: {is_relevant}")    
    return json_data
   

llm = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite", google_api_key=API_KEY)
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
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=False)

# --- Vercel Handler ---
class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
    def do_POST(self):
        # Read request body
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data)
        query = data.get("query", "")

        # Run agent
        response = agent_executor.invoke({"query": query})
        json_data = collect_query_data(query, response)
        
        # Send response
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        
        self.send_header('Access-Control-Allow-Origin', '*')  # Allows any website to call your API
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
        self.wfile.write(json.dumps(json_data).encode('utf-8'))