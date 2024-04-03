# =========================================== imports =============================================

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
    try:
        automation.set_repo_users(repo_url, usernames)
        return {"status": "success"}
    except Exception as e:
        return {"status": "failed", "error": str(e)}

# ======================================== run the app =========================================
    
if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=5000, reload=True)

# ==============================================================================================