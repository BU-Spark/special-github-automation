from __future__ import annotations

from typing import Optional, List
import enum
from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    Text,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    Enum as Enum_,
    PrimaryKeyConstraint,
    TIMESTAMP,
    func
)
from sqlalchemy.orm import (
    DeclarativeBase,
    MappedColumn,
    Mapped,
    mapped_column,
    relationship
)

class Base(DeclarativeBase):
    pass

class Season(enum.Enum):
    spring = 'spring'
    summer = 'summer'
    fall = 'fall'
    winter = 'winter'

class Status(enum.Enum):
    started = 'started'
    invited = 'invited'
    pull = 'pull'
    push = 'push'

class Outcome(enum.Enum):
    success = 'success'
    failure = 'failure'
    warning = 'warning'
    unkown = 'unkown'

class Semester(Base):
    __tablename__ = 'semester'

    semester_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, nullable=False,
        # server_default=func.nextval('semester_semester_id_seq')
    )
    semester_name: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False, default=2077)
    season: Mapped[Season] = mapped_column(Enum_(Season), nullable=False)

    # Bidirectional Relationship to Project
    projects: Mapped[List[Project]] = \
        relationship("Project", back_populates="semester", cascade="all, delete-orphan")

    def __repr__(self):
        return (
            f"<Semester(semester_id={self.semester_id}, "
            f"semester_name='{self.semester_name}', "
            f"year={self.year}, season={self.season.value})>"
        )
        
    def short(self):
        lookup ={'spring': 'sp','summer': 'su','fall': 'fa','winter': 'wi'}
        return f"{lookup[self.season.value]}-{str(self.year)[-2:]}"

class User(Base):
    __tablename__ = 'user'
    
    user_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, nullable=False,
        #server_default=func.nextval('user_user_id_seq')
    )
    first_name: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    email: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    buid: Mapped[Optional[str]] = mapped_column(Text, nullable=True, unique=True)
    github_username: Mapped[Optional[str]] = mapped_column(Text, nullable=True, unique=True)
    
    # Bidirectional Relationship to UserProject
    user_projects: Mapped[List["UserProject"]] = \
        relationship("UserProject", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return (
            f"<User(user_id={self.user_id}, first_name='{self.first_name}', "
            f"last_name='{self.last_name}', email='{self.email}', "
            f"buid='{self.buid}', github_username='{self.github_username}')>"
        )
    
class Project(Base):
    __tablename__ = 'project'

    project_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, nullable=False,
        #server_default=func.nextval('project_project_id_seq')
    )
    course: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    project_name: Mapped[str] = mapped_column(Text, nullable=False)
    project_tag: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    semester_id: Mapped[int] = mapped_column(ForeignKey('semester.semester_id', ondelete='RESTRICT'), nullable=False)
    github_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True, unique=True)
    slack_channel: Mapped[Optional[str]] = mapped_column(Text, nullable=True, unique=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

    # Bidirectional Relationship to Semester
    semester: Mapped[Semester] = \
        relationship("Semester", back_populates="projects")
    user_projects: Mapped[List["UserProject"]] = \
        relationship("UserProject", back_populates="project", cascade="all, delete-orphan")

    def __repr__(self):
        return (
            f"<Project(project_id={self.project_id}, "
            f"project_name='{self.project_name}', "
            f"project_tag='{self.project_tag}', "
            f"semester_id={self.semester_id}, "
            f"github_url='{self.github_url}', "
            f"slack_channel='{self.slack_channel}', "
            f"created_at={self.created_at.isoformat()})>"
        )
        
class UserProject(Base):
    __tablename__ = 'user_project'

    project_id: Mapped[int] = \
        mapped_column(ForeignKey('project.project_id'), primary_key=True, nullable=False)
    user_id: Mapped[int] = \
        mapped_column(ForeignKey('user.user_id'), primary_key=True, nullable=False)
    status: Mapped[Optional[Status]] = mapped_column(Enum_(Status), nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True),nullable=False, server_default=func.now())

    # Relationships to User and Project
    user: Mapped["User"] = relationship("User", back_populates="user_projects")
    project: Mapped["Project"] = relationship("Project", back_populates="user_projects")

    def __repr__(self) -> str:
        return (
            f"<UserProject(project_id={self.project_id}, user_id={self.user_id}, "
            f"status={self.status}, created_at={self.created_at.isoformat()})>"
        )

class IngestProjectCSV(Base):
    __tablename__ = "ingest_project_csv"
    
    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, nullable=False,
        #server_default=func.nextval('ingest_project_csv_id_seq')
    )
    course: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    project_name: Mapped[str] = mapped_column(Text, nullable=False)
    project_tag: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    semester: Mapped[str] = mapped_column(Text, nullable=False)
    github_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True, unique=True)
    slack_channel: Mapped[Optional[str]] = mapped_column(Text, nullable=True, unique=True)
    generate_github: Mapped[Optional[bool]] = mapped_column(Integer, nullable=True, default=False)
    generate_slack: Mapped[Optional[bool]] = mapped_column(Integer, nullable=True, default=False)
    outcome: Mapped[Optional[Outcome]] = mapped_column(Enum_(Outcome), nullable=True)
    result: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    def __repr__(self) -> str:
        return (
            f"<IngestProjectCSV(id={self.id}, course='{self.course}', "
            f"project_name='{self.project_name}', project_tag='{self.project_tag}', "
            f"semester='{self.semester}', github_url='{self.github_url}', "
            f"slack_channel='{self.slack_channel}', generate_github={self.generate_github}, "
            f"generate_slack={self.generate_slack}, outcome={self.outcome}, result='{self.result}')>"
        )
        
class IngestUserProjectCSV(Base):
    __tablename__ = "ingest_user_project_csv"
    
    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, nullable=False,
        #server_default=func.nextval('ingest_user_project_csv_id_seq')
    )
    project_name: Mapped[str] = mapped_column(Text, nullable=False)
    project_tag: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    first_name: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    email: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    buid: Mapped[Optional[str]] = mapped_column(Text, nullable=True, unique=True)
    github_username: Mapped[Optional[str]] = mapped_column(Text, nullable=True, unique=True)
    outcome: Mapped[Optional[Outcome]] = mapped_column(Enum_(Outcome), nullable=True)
    result: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    def __repr__(self) -> str:
        return (
            f"<IngestUserProjectCSV(id={self.id}, project_name='{self.project_name}', "
            f"project_tag='{self.project_tag}', first_name='{self.first_name}', "
            f"last_name='{self.last_name}', email='{self.email}', buid='{self.buid}', "
            f"github_username='{self.github_username}', outcome={self.outcome}, result='{self.result}')>"
        )