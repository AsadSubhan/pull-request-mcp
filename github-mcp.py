import os
import subprocess
import json
import time
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

GITHUB_TOKEN=os.environ.get("GITHUB_PERSONAL_ACCESS_TOKEN")
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# Start a Docker container running the GitHub MCP server
### =========================================== 

proc = subprocess.Popen(
    [
        "docker", "run", "-i", "--rm",
        "-e", f"GITHUB_PERSONAL_ACCESS_TOKEN={GITHUB_TOKEN}",
        "ghcr.io/github/github-mcp-server:latest"
    ],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)

# Initialize connection
### =========================================== 

init_request = {
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "protocolVersion": "2025-03-26",
    "capabilities": {
      "roots": {
        "listChanged": True
      },
      "sampling": {}
    },
    "clientInfo": {
      "name": "github-mcp-client",
      "version": "1.0.0"
    }
  }
}

proc.stdin.write(json.dumps(init_request) + "\n")
proc.stdin.flush()

init_response_str = proc.stdout.readline()
init_response = json.loads(init_response_str)
print("Initialization Response:")
print("--------------------------------")
# print(json.dumps(init_response, indent=4))

#  Write to a file prettily
with open("mcp_initialize.json", "w", encoding="utf-8") as f:
    json.dump(init_response, f, indent=4)  

print("mcp initialized.")


# Send initialized notification
### =========================================== 

initialized_notification = {
  "jsonrpc": "2.0",
  "method": "notifications/initialized"
}

proc.stdin.write(json.dumps(initialized_notification) + "\n")
proc.stdin.flush()


# Send a request to MCP Server
### =========================================== 

request = {
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/list",
    "params": {}
}

proc.stdin.write(json.dumps(request) + "\n")
proc.stdin.flush()

while True:
    tool_list_response_str = proc.stdout.readline()
    tool_list_response = json.loads(tool_list_response_str)

    if "id" not in tool_list_response:
        continue

    if tool_list_response["id"] == 2:
        break

print("Tools List Response:")
print("--------------------------------")
# print(json.dumps(tool_list_response, indent=4))

#  Write to a file prettily
with open("mcp_tools_list.json", "w", encoding="utf-8") as f:
    json.dump(tool_list_response, f, indent=4)  

print("mcp tools list retrieved.")



# Extract list of tools from MCP response
### ===========================================

mcp_tools = tool_list_response["result"]["tools"]
# print(mcp_tools[0])

# Map each tool to openai function schema

llm_tools = [
    {
        "type": "function",
        "name": tool["name"],
        "description": tool["description"],
        "parameters": tool["inputSchema"]
    }
    for tool in mcp_tools
]


# System prompt: instructs the LLM about its role
system_prompt = """
You are a GitHub automation assistant.
You can only use the MCP tools provided.
Never make up arguments; always use the schema provided.
Return your tool calls in structured JSON.
"""

# Example user request
user_prompt = "list me all the repositories which are created in last 2 months"


# Ask LLM to suggest which tool to call with proper arguments
llm_response = client.responses.create(
    model="gpt-5.1",  
    input=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ],
    tools=llm_tools,          
    tool_choice="auto"        
)


response_json = llm_response.model_dump()

# print(json.dumps(response_json, indent=2))
tool_call = response_json["tools"][0]
print(json.dumps(tool_call, indent=2))

# tool_name = tool_call["name"]
# arguments_json = tool_call["arguments"]

# print(f"LLM selected tool: {tool_name} with arguments: {arguments_json}")           
