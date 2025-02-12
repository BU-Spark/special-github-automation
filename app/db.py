import os
from typing import Any, Generator, List, Literal
from schema import _Project, _User, _UserProject, _IngestProjectCSV, _IngestUserProjectCSV
from models import (
    User, Project, Base, IngestProjectCSV, IngestUserProjectCSV, Semester, UserProject, Outcome, Status
)
from slacker import Slacker
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
import pandas as pd
from pandas import DataFrame
from github import Github
import log
from drive import Drive

class DB:
    
    # ======================================================================================================================
    # CRUD functionality
    # ======================================================================================================================
    
    def __init__(self, PGURL: str):
        self.PGURL = PGURL
        self.engine = create_engine(self.PGURL, echo=False)
        self.log = log.SparkLogger(name="Spark", output=True, persist=True)
        
    def s(self) -> Session:
        return sessionmaker(bind=self.engine)()
        
    @contextmanager
    def scope(self) -> Generator[Session, Any, None]:
        session = self.s()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
            
    def run(self, func, *args, **kwargs):
        session = self.s()
        try:
            result = func(session, *args, **kwargs)
            session.commit()
            return result
        except IntegrityError as ie:
            session.rollback()
            print(f"Integrity error: {ie.orig}")
        except Exception as e:
            session.rollback()
            print(f"Unexpected error: {e}")
        finally:
            session.close()
            
    def get_projects(self):
        with self.scope() as session:
            return [_Project.model_validate(s).model_dump() for s in session.query(Project).all()]
    
    def get_users(self):
        with self.scope() as session:
            return [_User.model_validate(s).model_dump() for s in session.query(User).all()]
    
    def get_ingest_projects(self):
        with self.scope() as session:
            return [_IngestProjectCSV.model_validate(s).model_dump() for s in session.query(IngestProjectCSV).all()]
    
    def get_ingest_user_projects(self):
        with self.scope() as session:
            return [_IngestUserProjectCSV.model_validate(s).model_dump() for s in session.query(IngestUserProjectCSV).all()]
    
if __name__ == "__main__":
    TEST_POSTGRES = os.getenv("TEST_POSTGRES_URL") or ""
    db = DB(TEST_POSTGRES)
    print(db.get_projects())
    print(db.get_users())
    print(db.get_ingest_projects())
    print(db.get_ingest_user_projects())