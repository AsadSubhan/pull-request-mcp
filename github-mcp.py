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
# with open("mcp_initialize.json", "w", encoding="utf-8") as f:
#     json.dump(init_response, f, indent=4)  

print("mcp initialized.")


# Send initialized notification
### =========================================== 

initialized_notification = {
  "jsonrpc": "2.0",
  "method": "notifications/initialized"
}

proc.stdin.write(json.dumps(initialized_notification) + "\n")
proc.stdin.flush()


# Get tools list from MCP Server
### =========================================== 

toollist_request = {
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/list",
    "params": {}
}

proc.stdin.write(json.dumps(toollist_request) + "\n")
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
# with open("mcp_tools_list.json", "w", encoding="utf-8") as f:
#     json.dump(tool_list_response, f, indent=4)  

print("mcp tools list retrieved.")


# Get profile information using get_me tool
### ===========================================

getprofile_request = {
    "jsonrpc": "2.0",
    "id": "getmeRequest",
    "method": "tools/call",
    "params": {
        "name": "get_me",
        "arguments": {}
    }
}

proc.stdin.write(json.dumps(getprofile_request) + "\n")
proc.stdin.flush()

while True:
    getme_str = proc.stdout.readline()
    getme_response = json.loads(getme_str)

    if "id" not in getme_response:
        continue

    if getme_response["id"] == "getmeRequest":
        break

# print(json.dumps(getme_response, indent=2))

# Get list of pull requests from a repository using list_pull_requests tool
### ===========================================

listpr_request = {
    "jsonrpc": "2.0",
    "id": "listprRequest",
    "method": "tools/call",
    "params": {
        "name": "list_pull_requests",
        "arguments": {
            "owner": "asadsubhan0",
            "repo": "AuthGHPages"
        }
    }
}

proc.stdin.write(json.dumps(listpr_request) + "\n")
proc.stdin.flush()

while True:
    listpr_str = proc.stdout.readline()
    listpr_response = json.loads(listpr_str)

    if "id" not in listpr_response:
        continue

    if listpr_response["id"] == "listprRequest":
        break

# extract the text field
pr_text = listpr_response["result"]["content"][0]["text"]

# convert the string into a real Python list
pr_list = json.loads(pr_text)
# print(json.dumps(pr_list, indent=2))

pr_number = pr_list[0]["number"]
print(f"Latest PR number: {pr_number}")


# Get pull request details
### ===========================================

getpr_request = {
    "jsonrpc": "2.0",
    "id": "getprRequest",
    "method": "tools/call",
    "params": {
        "name": "pull_request_read",
        "arguments": {
            "method": "get",
            "owner": "asadsubhan0",
            "pullNumber": pr_number,
            "repo": "AuthGHPages"
        }
    }
}


proc.stdin.write(json.dumps(getpr_request) + "\n")
proc.stdin.flush()

while True:
    getpr_str = proc.stdout.readline()
    getpr_response = json.loads(getpr_str)

    if "id" not in getpr_response:
        continue

    if getpr_response["id"] == "getprRequest":
        break

# extract the text field
getpr_text = getpr_response["result"]["content"][0]["text"]

# convert the string into a real Python list
getpr_list = json.loads(getpr_text)
# print(json.dumps(getpr_list, indent=2))

head_sha = getpr_list["head"]["sha"]

# Get diff of pull request
### ==============================

getdiff_request = {
    "jsonrpc": "2.0",
    "id": "getdiffRequest",
    "method": "tools/call",
    "params": {
        "name": "pull_request_read",
        "arguments": {
            "method": "get_diff",
            "owner": "asadsubhan0",
            "pullNumber": pr_number,
            "repo": "AuthGHPages"
        }
    }
}

proc.stdin.write(json.dumps(getdiff_request) + "\n")
proc.stdin.flush()

while True:
    getdiff_str = proc.stdout.readline()
    getdiff_response = json.loads(getdiff_str)

    if "id" not in getdiff_response:
        continue

    if getdiff_response["id"] == "getdiffRequest":
        break

# extract the text field
getdiff_text = getdiff_response["result"]["content"][0]["text"]
# print(getdiff_text)


# Get files of pull request
### =============================

getfiles_request = {
    "jsonrpc": "2.0",
    "id": "getfilesRequest",
    "method": "tools/call",
    "params": {
        "name": "pull_request_read",
        "arguments": {
            "method": "get_files",
            "owner": "asadsubhan0",
            "pullNumber": pr_number,
            "repo": "AuthGHPages"
        }
    }
}

proc.stdin.write(json.dumps(getfiles_request) + "\n")
proc.stdin.flush()

while True:
    getfiles_str = proc.stdout.readline()
    getfiles_response = json.loads(getfiles_str)

    if "id" not in getfiles_response:
        continue

    if getfiles_response["id"] == "getfilesRequest":
        break

# extract the text field
getfiles_text = getfiles_response["result"]["content"][0]["text"]

# convert the string into a real Python list
getfiles_list = json.loads(getfiles_text)
# print(json.dumps(getfiles_list, indent=2))

filename = getfiles_list[0]["filename"]
status = getfiles_list[0]["status"]

# Get file content of the changed files in pull request
### =============================

getfilecontent_request = {
    "jsonrpc": "2.0",
    "id": "getfilecontentRequest",
    "method": "tools/call",
    "params": {
        "name": "get_file_contents",
        "arguments": {
            "owner": "asadsubhan0",
            "repo": "AuthGHPages",
            "path": filename,
            "ref": head_sha
        }
    }
}


proc.stdin.write(json.dumps(getfilecontent_request) + "\n")
proc.stdin.flush()

while True:
    getfilecontent_str = proc.stdout.readline()
    getfilecontent_response = json.loads(getfilecontent_str)

    if "id" not in getfilecontent_response:
        continue

    if getfilecontent_response["id"] == "getfilecontentRequest":
        break

# extract the text field
getfilecontent_text = getfilecontent_response["result"]["content"][1]["resource"]["text"]

print(getfilecontent_text)












