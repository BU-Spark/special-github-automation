import datetime
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
import enum

# Enums
class SemesterEnum(str, enum.Enum):
    Spring = 'Spring'
    Summer = 'Summer'
    Fall = 'Fall'
    Winter = 'Winter'

class StatusEnum(str, enum.Enum):
    started = 'started'
    invited = 'invited'
    pull = 'pull'
    push = 'push'

class UserBase(BaseModel):
    name: Optional[str]
    email: EmailStr
    buid: str
    github: Optional[str]

class UserCreate(UserBase):
    pass

class User(UserBase):
    user_id: int

    class Config:
        orm_mode = True

class SemesterBase(BaseModel):
    semester_name: str
    year: int = 2077
    semester: Optional[SemesterEnum]

class SemesterCreate(SemesterBase):
    pass

class Semester(SemesterBase):
    semester_id: int

    class Config:
        orm_mode = True

class ProjectBase(BaseModel):
    project_name: str
    semester_id: Optional[int]
    github_url: Optional[str]

class ProjectCreate(ProjectBase):
    pass

class Project(ProjectBase):
    project_id: int
    created_at: datetime.datetime

    class Config:
        orm_mode = True

class UserProjectBase(BaseModel):
    project_id: int
    user_id: int
    status: Optional[StatusEnum]

class UserProjectCreate(UserProjectBase):
    pass

class UserProject(UserProjectBase):
    created_at: datetime.datetime

    class Config:
        orm_mode = True

class CSVBase(BaseModel):
    semester: Optional[str]
    course: Optional[str]
    project: Optional[str]
    organization: Optional[str]
    team: Optional[str]
    role: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    full_name: Optional[str]
    email: Optional[EmailStr]
    buid: Optional[str]
    github_username: Optional[str]
    status: Optional[str]
    project_github_url: Optional[str]

class CSVCreate(CSVBase):
    pass

class CSV(CSVBase):
    id: int

    class Config:
        orm_mode = True

class CSVProjectBase(BaseModel):
    semester: Optional[str]
    project: Optional[str]
    project_github_url: Optional[str]
    status: Optional[str]

class CSVProjectCreate(CSVProjectBase):
    pass

class CSVProject(CSVProjectBase):
    id: int

    class Config:
        orm_mode = True
