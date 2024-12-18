from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from models import Status

class _Project(BaseModel):
    course: Optional[str]
    project_name: str
    project_tag: str
    semester_id: int
    github_url: str
    slack_channel: Optional[str]
    
class _User(BaseModel):
    first_name: Optional[str]
    last_name: Optional[str]
    email: str
    buid: Optional[str]
    github_username: str
    
class _UserProject(BaseModel):
    project_id: int
    user_id: int
    status_github: Optional[Status]
    status_slack: Optional[Status]
    github_result: Optional[str]
    slack_result: Optional[str]
    created_at: Optional[datetime]