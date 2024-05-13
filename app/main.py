# =========================================== imports =============================================

from fastapi import FastAPI, HTTPException, Request, WebSocket, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import pandas as pd
import github_rest as gh
import github as git
import database as db
import os
from dotenv import load_dotenv

# =========================================== app setup ===========================================

# env
load_dotenv()
GITHUB_PAT = os.getenv('GITHUB_PAT')

# app
app = FastAPI()
automation = gh.Automation(GITHUB_PAT, 'spark-tests')
github = git.Github(GITHUB_PAT, 'spark-tests')

# cors
app.add_middleware(CORSMiddleware,
    allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

# ============================================ routing  ===========================================

# root route
@app.get("/")
async def root(): return {"/": "/"}
    
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
    except Exception as e: return {"status": "failed", "error": str(e)}

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
    except Exception as e: return {"status": "failed", "error": str(e)}
    
# route called re-invite expired collaborators that re-invites expired collaborators based on a cron job
@app.post("/reinvite_expired_collaborators")
async def reinvite_expired_collaborators(request: Request):
    try:
        r = automation.reinvite_all_expired_users_to_repos()
        print(r)
        return {"status": r}
    except Exception as e: return {"status": "failed", "error": str(e)}
    
    
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
    except Exception as e: return {"status": "failed", "error": str(e)}

# ===================================== client functionality ======================================

# route called upload that takes in a csv
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        dataframe = pd.read_csv(file.file)
        r = db.ucsv(dataframe)
        return {"status": r}
    except Exception as e: return {"status": "failed", "error": str(e)}

# route called ingest
@app.post("/ingest")
async def ingest():
    try:
        r = db.ingest()
        return {"status": r}
    except Exception as e: return {"status": "failed", "error": str(e)}

# route called getinfo
@app.get("/get_info")
async def get_info():
    try:
        info = db.information()
        return {"info": info}
    except Exception as e: return {"status": "failed", "error": str(e)}
    
# route called getcsv
@app.get("/get_csv")
async def get_csv():
    try:
        csv = db.gcsv()
        return {"csv": csv}
    except Exception as e: return {"status": "failed", "error": str(e)}
    
# route called get projects
@app.get("/get_projects")
async def get_projects():
    try:
        projects = db.projects()
        return {"projects": projects}
    except Exception as e: return {"status": "failed", "error": str(e)}
    
# route called set_projects
@app.post("/set_projects")
async def set_projects(request: Request):
    data = await request.json()
    projects: list[tuple[str, str]] = data["projects"]
    action: str = data["action"]
    
    if action not in ['push', 'pull']: return {"status": "failed", "error": "action must be 'push' or 'pull'"}
    
    r = []
    try:
        for project in projects:
            try:
                #print(project)
                project_name = project[0]
                repo_url = project[1]
                
                users = db.get_users_in_project(project_name)
                #print(users)
                for user in users:
                    #print(user)
                    github_username = user["github"]
                    gh_status, gh_msg = github.change_user_permission_on_repo(repo_url, github_username, action)
                    if gh_status != 200 and gh_status != 204:
                        r.append(f"FAILED: {project_name} - {github_username} -> {gh_status} {gh_msg}")
                        continue
                    else:
                        db_status, db_msg = db.change_users_project_status(project_name, github_username, action)
                        r.append(f"PROCESSED: {project_name} - {github_username} -> gh {gh_status} {gh_msg} | db {db_status} {db_msg}")
                    
            except Exception as e: 
                print(e)
                r.append(f"failed to modify {project_name}")
                continue
            
        return {"results": r}
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

# ======================================== run the app =========================================
    
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True)

# ==============================================================================================