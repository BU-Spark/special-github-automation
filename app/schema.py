from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from models import Outcome, Status

class _Project(BaseModel):
    course: Optional[str]
    project_name: str
    project_tag: str
    semester_id: int
    github_url: str
    slack_channel: Optional[str]
    drive_url: Optional[str]
    
    model_config = {'from_attributes': True}
    
class _User(BaseModel):
    first_name: Optional[str]
    last_name: Optional[str]
    email: str
    buid: Optional[str]
    github_username: str
    
    model_config = {'from_attributes': True}
    
class _UserProject(BaseModel):
    project_id: int
    user_id: int
    status_github: Optional[Status]
    status_slack: Optional[Status]
    status_drive: Optional[Status]
    github_result: Optional[str]
    slack_result: Optional[str]
    drive_result: Optional[str]
    created_at: Optional[datetime]
    
    model_config = {'from_attributes': True}
    
class _IngestProjectCSV(BaseModel):
    id: int
    course: Optional[str]
    project_name: str
    project_tag: str
    semester: str
    github_url: Optional[str]
    slack_channel: Optional[str]
    drive_url: Optional[str]
    generate_github: Optional[bool]
    generate_slack: Optional[bool]
    outcome: Optional[Outcome]
    result: Optional[str]

    model_config = {'from_attributes': True}


class _IngestUserProjectCSV(BaseModel):
    id: int
    project_name: str
    project_tag: str
    first_name: Optional[str]
    last_name: Optional[str]
    email: Optional[str]
    buid: Optional[str]
    github_username: Optional[str]
    outcome: Optional[Outcome]
    result: Optional[str]

    model_config = {'from_attributes': True}