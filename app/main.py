# =========================================== imports =============================================

from fastapi import FastAPI, HTTPException, Request, WebSocket, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import pandas as pd
import github_rest as gh
import github as git
import database as db
import middleware as middleware
import os
import aiocache
from dotenv import load_dotenv
from aiocache import Cache
from aiocache.serializers import JsonSerializer
from aiocache.decorators import cached

# =========================================== app setup ===========================================

# env
load_dotenv()
GITHUB_PAT = os.getenv('GITHUB_PAT')

# app
app = FastAPI()
automation = gh.Automation(GITHUB_PAT, 'spark-tests')
github = git.Github(GITHUB_PAT, 'spark-tests')
aiocache.caches.set_config({
    'default': {
        'cache': 'aiocache.SimpleMemoryCache',
        'serializer': {'class': 'aiocache.serializers.JsonSerializer'},
    },
})

# cors
app.add_middleware(CORSMiddleware,
    allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)
app.add_middleware(middleware.BasicAuthMiddleware, 
    allowed=["/", "/refresh"]
)

# ========================================= functionality =========================================

async def deletecache():
    cache = aiocache.caches.get('default') 
    await cache.clear()

# root route
@app.get("/")
async def root(): return {"/": "/"}

# route to check authentication status (uses middleware)
@app.post("/authenticate")
async def authenticate(): return {"status": "authenticated"}

# route to refresh the cache
@app.post("/refresh")
async def refresh(): 
    cache = aiocache.caches.get('default') 
    await cache.clear()
    return {"status": "cache cleared"}

# ============================================ retool  ===========================================

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

@app.post("/upload/csv")
async def upload_file(file: UploadFile = File(...)):
    try:
        await deletecache()
        status = db.ucsv(pd.read_csv(file.file))
        return {"status": status}
    except Exception as e: return {"status": "failed", "error": str(e)}
    
@app.post("/upload/projects")
async def upload_projects(file: UploadFile = File(...)):
    try: await deletecache() ; return {"status": db.uprojects(pd.read_csv(file.file))}
    except Exception as e: return {"status": "failed", "error": str(e)}

@app.post("/ingest/csv")
async def ingest():
    try: 
        await deletecache()
        status = db.ingest()
        return {"status": status}
    except Exception as e: return {"status": "failed", "error": str(e)}
    
@app.post("/ingest/projects")
async def ingest_projects():
    try: await deletecache() ; return {"status": db.ingest_projects()}
    except Exception as e: return {"status": "failed", "error": str(e)}

@app.post("/process")
async def process():
    try: await deletecache() ; return {"status": db.process()}
    except Exception as e: return {"status": "failed", "error": str(e)}

@app.get("/get_info")
@cached(ttl=180, alias="default", key="info")
async def get_info():
    try: return {"info": db.information()}
    except Exception as e: return {"status": "failed", "error": str(e)}
    
@app.get("/get_csv")
@cached(ttl=180, alias="default", key="csv")
async def get_csv():
    try: return {"csv": db.gcsv()}
    except Exception as e: return {"status": "failed", "error": str(e)}
    
@app.get("/get_projects")
@cached(ttl=180, alias="default", key="projects")
async def get_projects():
    try: return {"projects": db.projects()}
    except Exception as e: return {"status": "failed", "error": str(e)}
    
@app.post("/set_projects")
async def set_projects(request: Request):
    data = await request.json()
    await deletecache()
    
    results: list = []
    projects: list[tuple[str, str]] = data["projects"]
    action: str = data["action"]
    
    if action not in ['push', 'pull']: return {"status": "failed", "error": "action must be 'push' or 'pull'"}
    
    try:
        for project in projects:
            try:
                project_name = project[0]
                repo_url = project[1]
                users = db.get_users_in_project(project_name)
                for user in users:
                    github_username = user["github"]
                    gh_status, gh_msg = github.change_user_permission_on_repo(repo_url, github_username, action)
                    if gh_status != 200 and gh_status != 204:
                        results.append(f"FAILED: {project_name} - {github_username} -> {gh_status} {gh_msg}")
                        continue
                    else:
                        db_status, db_msg = db.change_users_project_status(project_name, github_username, action)
                        results.append(f"PROCESSED: {project_name} - {github_username} -> gh {gh_status} {gh_msg} | db {db_status} {db_msg}")
                    
            except Exception as e: 
                print(e)
                results.append(f"failed to modify {project_name}")
                continue
        return {"results": results}
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.post("/git/set_projects")
async def set_projects(request: Request):
    data = await request.json()
    
    results: list = []
    projects: list[tuple[str, str]] = data["projects"]
    action: str = data["action"]
    
    if action not in ['push', 'pull']: return {"status": "failed", "error": "action must be 'push' or 'pull'"}
    
    try:
        for project in projects:
            try:
                project_name = project[0]
                repo_url = project[1]
                response = github.change_all_user_permission_on_repo(repo_url, action)
                for res in response:
                    results.append(f"{project_name} -> {res}")
                    
            except Exception as e: 
                print(e)
                results.append(f"failed to modify {project_name}")
                continue
        return {"results": results}
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.get("/git/get_all_repos")
async def get_all_repos():
    try: return {"repos": github.get_all_repos()}
    except Exception as e: return {"status": "failed", "error": str(e)}

# ======================================== run the app =========================================
    
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True)

# ==============================================================================================