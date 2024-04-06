# =========================================== imports =============================================

from typing import List, Tuple
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import github_rest as gh
import os
from dotenv import load_dotenv

# =========================================== app setup ===========================================

# Importing the required environment variables
load_dotenv()
GITHUB_PAT = os.getenv('GITHUB_PAT')

# Creating a FastAPI instance
app = FastAPI()
automation = gh.Automation(GITHUB_PAT)

# Setting up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================ routing  ===========================================

# root route
@app.get("/")
async def root():
    return {"/": "/"}
    
# route called set_repo_users that takes in a repo ssh url, and a list of usernames
@app.post("/set_repo_users")
async def set_repo_users(request: Request):
    data = await request.json()
    repo_url = data["repo_url"]
    usernames = data["usernames"]
    
    repo_url = repo_url.replace("https://github.com/", "git@github.com:")
    
    print("setting repo with:", repo_url, usernames)
    try:
        r = automation.set_repo_users(repo_url, usernames)
        print(r)
        return {"status": "success"}
    except Exception as e:
        return {"status": "failed", "error": str(e)}

# route called check_invited_collaborators that takes in a repo ssh url and returns a list of invited collaborators
@app.post("/check_invited_collaborators")
async def check_invited_collaborators(request: Request):
    data = await request.json()
    repo_url = data["repo_url"]
    
    repo_url = repo_url.replace("https://github.com/", "git@github.com:")
    
    try:
        invited_collaborators = automation.get_users_invited_repo(repo_url)
        return {"status": "success", "invited_collaborators": invited_collaborators}
    except Exception as e:
        return {"status": "failed", "error": str(e)}
    
# route called add_user_to_projects that takes in a repo ssh url, a username, and a list of project names
@app.post("/add_user_to_projects")
async def add_user_to_projects(request: Request):
    data = await request.json()
    username = data["username"]
    projects_urls: List[str] = data["projects"]
    projects_urls = [url.replace("https://github.com/", "git@github.com:") for url in projects_urls]
    print(username)
    print(projects_urls)
    
    try:
        res = automation.add_user_to_projects(username, projects_urls)
        print(res)
        return {"status": "success"}
    except Exception as e:
        return {"status": "failed", "error": str(e)}

# ======================================== run the app =========================================
    
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True)

# ==============================================================================================