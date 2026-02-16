import os
import subprocess
import json
import time
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(override=True)

GITHUB_TOKEN=os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")
api_key=os.getenv("API_KEY")
endpoint = os.getenv("FOUNDRY_MODEL_ENDPOINT")
deployment_name = os.getenv("MODEL_DEPLOYMENT_NAME")
GITHUB_HOST = os.getenv("GITHUB_HOST")
GITHUB_OWNER = os.getenv("GITHUB_OWNER")
GITHUB_REPO = os.getenv("GITHUB_REPO")

client = OpenAI(
    base_url=f"{endpoint}",
    api_key=api_key
)

# Start a Docker container running the GitHub MCP server
### =========================================== 

proc = subprocess.Popen(
    [
        "docker", "run", "-i", "--rm",
        "-e", f"GITHUB_PERSONAL_ACCESS_TOKEN={GITHUB_TOKEN}",
        "-e", f"GITHUB_HOST={GITHUB_HOST}",
        "ghcr.io/github/github-mcp-server:latest"
    ],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    encoding="utf-8",
    errors="replace"
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
            "owner": GITHUB_OWNER,
            "repo": GITHUB_REPO
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
            "owner": GITHUB_OWNER,
            "pullNumber": pr_number,
            "repo": GITHUB_REPO
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
            "owner": GITHUB_OWNER,
            "pullNumber": pr_number,
            "repo": GITHUB_REPO
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
            "owner": GITHUB_OWNER,
            "pullNumber": pr_number,
            "repo": GITHUB_REPO
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


llm_payload = {
    "pull_request_diff": getdiff_text,
    "files": []
}

for idx, file_info in enumerate(getfiles_list):
    filename = file_info["filename"]
    status = file_info["status"]

    if status == "removed":
        print(f"Skipping removed file: {filename}")
        continue

    print(f"\n=== Processing file {idx + 1}: {filename} ({status}) ===")

    request_id = f"getfilecontentRequest_{idx}"

    getfilecontent_request = {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": "tools/call",
        "params": {
            "name": "get_file_contents",
            "arguments": {
                "owner": GITHUB_OWNER,
                "repo": GITHUB_REPO,
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

        if getfilecontent_response["id"] == request_id:
            break

    file_content = getfilecontent_response["result"]["content"][1]["resource"]["text"]  
    llm_payload["files"].append({
        "filename": filename,
        "status": status,
        "content": file_content
    })

# print("LLM Payload:", json.dumps(llm_payload, indent=2))


system_prompt = """You are a senior software engineer performing a pull request review.

You will be given:
1. The full pull request diff (this is the primary source of truth)
2. A list of changed files, each with:
   - filename
   - change status (added, modified)
   - full file content (for additional context)

Review the pull request with the following goals:
- Identify bugs, logical errors, and edge cases
- Flag security issues, performance concerns, and bad practices
- Suggest improvements to readability, maintainability, and structure
- Call out missing validations, error handling, or tests when relevant
- Avoid commenting on unchanged code unless it directly affects the changes

Rules:
- Use the diff as the primary signal
- Use full file content only for understanding context
- Do NOT repeat the diff or file content in your response
- Do NOT make speculative comments without evidence from the diff
- Be concise but specific

Output format:

File: <filename>
- [Severity: Critical|Major|Minor|Suggestion] <comment>

Overall Review:
- <comment>
"""

user_prompt = f"""
Pull Request Data (JSON):
{json.dumps(llm_payload, indent=2)}
"""

response = client.responses.create(
    model=deployment_name,
    input=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ],
    temperature=0.2
)

# Extract model output safely
review_text = response.output[0].content[0].text
# print(review_text)


post_review_request = {
    "jsonrpc": "2.0",
    "id": "postReviewRequest",
    "method": "tools/call",
    "params": {
        "name": "pull_request_review_write",
        "arguments": {
            "method": "create",
            "event": "COMMENT",
            "owner": GITHUB_OWNER,
            "repo": GITHUB_REPO,
            "pullNumber": pr_number,
            "body": review_text
        }
    }
}

proc.stdin.write(json.dumps(post_review_request) + "\n")
proc.stdin.flush()

while True:
    resp_str = proc.stdout.readline()
    resp = json.loads(resp_str)

    if "id" not in resp:
        continue

    if resp["id"] == "postReviewRequest":
        break

print("✅ PR review posted successfully")
