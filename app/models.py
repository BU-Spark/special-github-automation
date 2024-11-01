from sqlalchemy import (
    Column,
    Integer,
    Text,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    Enum,
    PrimaryKeyConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import enum

Base = declarative_base()

# Enums
class SemesterEnum(enum.Enum):
    Spring = 'Spring'
    Summer = 'Summer'
    Fall = 'Fall'
    Winter = 'Winter'

class StatusEnum(enum.Enum):
    started = 'started'
    invited = 'invited'
    pull = 'pull'
    push = 'push'

class User(Base):
    __tablename__ = 'user'

    user_id = Column(Integer, primary_key=True)
    name = Column(Text)
    email = Column(Text, nullable=False, unique=True)
    buid = Column(Text, nullable=False, unique=True)
    github = Column(Text, unique=True)

    # Relationship to UserProject
    projects = relationship('UserProject', back_populates='user')

class Semester(Base):
    __tablename__ = 'semester'

    semester_id = Column(Integer, primary_key=True)
    semester_name = Column(Text, nullable=False, unique=True)
    year = Column(Integer, nullable=False, default=2077)
    semester = Column(Enum(SemesterEnum))

    # Relationship to Project
    projects = relationship('Project', back_populates='semester')

class Project(Base):
    __tablename__ = 'project'

    project_id = Column(Integer, primary_key=True)
    project_name = Column(Text, nullable=False, unique=True)
    semester_id = Column(Integer, ForeignKey('semester.semester_id'))
    github_url = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationship to Semester
    semester = relationship('Semester', back_populates='projects')

    # Relationship to UserProject
    users = relationship('UserProject', back_populates='project')

class UserProject(Base):
    __tablename__ = 'user_project'
    __table_args__ = (
        PrimaryKeyConstraint('project_id', 'user_id'),
    )

    project_id = Column(
        Integer,
        ForeignKey('project.project_id', onupdate='CASCADE', ondelete='CASCADE'),
        primary_key=True,
    )
    user_id = Column(
        Integer,
        ForeignKey('user.user_id', onupdate='CASCADE', ondelete='CASCADE'),
        primary_key=True,
    )
    status = Column(Enum(StatusEnum))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    user = relationship('User', back_populates='projects')
    project = relationship('Project', back_populates='users')

class CSV(Base):
    __tablename__ = 'csv'

    id = Column(Integer, primary_key=True)
    semester = Column(Text)
    course = Column(Text)
    project = Column(Text)
    organization = Column(Text)
    team = Column(Text)
    role = Column(Text)
    first_name = Column(Text)
    last_name = Column(Text)
    full_name = Column(Text)
    email = Column(Text)
    buid = Column(Text)
    github_username = Column(Text)
    status = Column(Text)
    project_github_url = Column(Text)

class CSVProjects(Base):
    __tablename__ = 'csv_projects'

    id = Column(Integer, primary_key=True)
    semester = Column(Text)
    project = Column(Text)
    project_github_url = Column(Text)
    status = Column(Text)
