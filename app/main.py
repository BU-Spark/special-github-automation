# =========================================== imports =============================================

from io import StringIO
from fastapi import FastAPI, HTTPException, Request, WebSocket, File, UploadFile, BackgroundTasks 
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
TEST_GITHUB_PAT = os.getenv('TEST_GITHUB_PAT')
SPARK_GITHUB_PAT = os.getenv('SPARK_GITHUB_PAT')

# app
app = FastAPI()

#automation = gh.Automation(TEST_GITHUB_PAT, 'spark-tests')
#github = git.Github(TEST_GITHUB_PAT, 'spark-tests')

automation = gh.Automation(SPARK_GITHUB_PAT, 'BU-Spark')
github = git.Github(SPARK_GITHUB_PAT, 'BU-Spark')

aiocache.caches.set_config({
    'default': {
        'cache': 'aiocache.SimpleMemoryCache',
        'serializer': {'class': 'aiocache.serializers.JsonSerializer'},
    },
})

# cors
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*", "https://special-github-automation.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(middleware.BasicAuthMiddleware, 
    allowed=["/", "/refresh", "/ping", "/airtable-sync"]
)

# ========================================= functionality =========================================

async def deletecache():
    cache = aiocache.caches.get('default') 
    await cache.clear()

# root route
@app.get("/")
async def root(): return {"/": "/"}

# sanity check
@app.get("/ping")
async def ping(): return {"status": "pong"}

# route to check authentication status (uses middleware)
@app.post("/authenticate")
async def authenticate(): return {"status": "authenticated"}

# route to refresh the cache
@app.post("/refresh")
async def refresh(): 
    cache = aiocache.caches.get('default') 
    await cache.clear()
    return {"status": "cache cleared"}
    
# route called re-invite expired collaborators that re-invites expired collaborators based on a cron job
@app.post("/reinvite_expired_collaborators")
async def reinvite_expired_collaborators(request: Request):
    try:
        r = automation.reinvite_all_expired_users_to_repos()
        print(r)
        return {"status": r}
    except Exception as e: return {"status": "failed", "error": str(e)}
    
# route called airtable-sync that takes in the csv and runs an upload and ingest  
@app.post("/airtable-sync")
async def airtable_sync(request: Request, background_tasks: BackgroundTasks):
    try:
        data = await request.json()
        await deletecache()      
        db.ucsv(pd.read_csv(StringIO(data["csv"])))
        background_tasks.add_task(db.ingest)
        return {"status": "success"}
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

# ===================================== client functionality ======================================

@app.post("/upload/csv")
async def upload_file(file: UploadFile = File(...)):
    try: await deletecache() ; return {"status": db.ucsv(pd.read_csv(file.file))}
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/upload/projects")
async def upload_projects(file: UploadFile = File(...)):
    try: await deletecache() ; return {"status": db.uprojects(pd.read_csv(file.file))}
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.post("/ingest/csv")
async def ingest():
    try: await deletecache() ; return {"status": db.ingest()}
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/ingest/projects")
async def ingest_projects():
    try: await deletecache() ; return {"status": db.ingest_projects()}
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

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
    
@app.get("/get_csv_projects")
@cached(ttl=180, alias="default", key="csv_projects")
async def get_csv_projects():
    try: return {"csv_projects": db.gcsvprojects()}
    except HTTPException as e: raise HTTPException(status_code=500, detail=str(e))
    
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

@app.get("/get_results")
@cached(ttl=180, alias="default", key="results")
async def get_results():
    try: return {"results": db.results()}
    except Exception as e: return {"status": "failed", "error": str(e)}

@app.get("/git/get_all_repos")
async def get_all_repos():
    try: return {"repos": github.get_all_repos()}
    except Exception as e: return {"status": "failed", "error": str(e)}

# ======================================== run the app =========================================
    
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True)

# ==============================================================================================