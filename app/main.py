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
automation = gh.Automation(GITHUB_PAT, 'spark-tests')

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
    
# route called set_repo_users that takes in a repo https url, and a list of usernames
@app.post("/set_repo_users")
async def set_repo_users(request: Request):
    data = await request.json()
    usernames: list[str] = data["usernames"]
    https_url: str = data["repo_url"]
    ssh_url = https_url.replace("https://github.com/", "git@github.com:")
    
    print("setting repo with:", ssh_url, usernames)
    try:
        r = automation.set_repo_users(ssh_url, desired_users=usernames)
        print(r)
        return {"status": r}
    except Exception as e:
        return {"status": "failed", "error": str(e)}

# route called check_invited_collaborators that takes in a repo https url and returns a list of invited collaborators
@app.post("/check_invited_collaborators")
async def check_invited_collaborators(request: Request):
    data = await request.json()
    https_url = data["repo_url"]
    ssh_url = https_url.replace("https://github.com/", "git@github.com:")
    
    print("checking invited collaborators for:", ssh_url)
    try:
        invited_collaborators = automation.get_users_invited_repo(ssh_url)
        print(invited_collaborators)
        return {"invited_collaborators": invited_collaborators}
    except Exception as e:
        return {"status": "failed", "error": str(e)}
    
# route called re-invite expired collaborators that re-invites expired collaborators based on a cron job
@app.post("/reinvite_expired_collaborators")
async def reinvite_expired_collaborators(request: Request):
    try:
        r = automation.reinvite_all_expired_users_to_repos()
        print(r)
        return {"status": r}
    except Exception as e:
        return {"status": "failed", "error": str(e)}
    
    
# route called add_user_to_repos that takes in a username and a list of repo https urls
@app.post("/add_user_to_repos")
async def add_user_to_repos(request: Request):
    data = await request.json()
    username: str = data["username"]
    https_urls: list[str] = data["projects"]
    ssh_urls = [url.replace("https://github.com/", "git@github.com:") for url in https_urls]
    print(username, ssh_urls)
    
    try:
        r = automation.add_user_to_repos(ssh_urls, username, "push")
        print(r)
        return {"status": r}
    except Exception as e:
        return {"status": "failed", "error": str(e)}

# ======================================== run the app =========================================
    
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True)

# ==============================================================================================