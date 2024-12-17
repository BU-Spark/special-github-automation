from typing import Optional
from pydantic import BaseModel

class _Project(BaseModel):
    course: Optional[str]
    project_name: str
    project_tag: str
    semester_id: int
    github_url: Optional[str]
    slack_channel: Optional[str]
    
class _User(BaseModel):
    first_name: Optional[str]
    last_name: Optional[str]
    email: str
    buid: Optional[str]
    github_username: Optional[str]