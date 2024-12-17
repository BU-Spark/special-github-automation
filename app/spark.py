import os
from typing import Any, Generator
from schema import _Project
from models import User, Project, Base, IngestProjectCSV, Semester, UserProject, Outcome
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

class Spark:
    
    # ======================================================================================================================
    # SQLAlchemy functionality
    # ======================================================================================================================
    
    def __init__(self, PGURL: str, org: str, slacker: Slacker, git: Github):
        self.PGURL = PGURL
        self.org = org
        self.engine = create_engine(self.PGURL, echo=False)
        self.slacker = slacker
        self.git = git
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
            
    # ======================================================================================================================
    # auto spark functionality
    # ======================================================================================================================        
    
    # ----------------------------------------------------------------------------------------------------------------------
    # ingestion of csv files into holding tables
    # ----------------------------------------------------------------------------------------------------------------------
    
    def ingest_csv(self, df: DataFrame, colmap: dict[str, str], table: str):
        """ingest csv"""
        
        tomap = {
            csv_col: \
                db_col for csv_col, db_col in colmap.items() 
                if csv_col != db_col and csv_col in df.columns
        }
        if tomap: df = df.rename(columns=tomap)
        if not self.engine: raise Exception("no engine.")
        for _, row in df.iterrows():
            try:
                row_df = pd.DataFrame([row])
                row_df.to_sql(table, self.engine, if_exists='append', index=False)
            except Exception as e:
                self.log.error(f"failure ingesting row into {table}: {e}")
                continue
    
    def ingest_project_csv(self, df: DataFrame):
        """ingest project csv"""
        
        colmap: dict[str, str] = {
            "Project Name": "project_name",
            "Project Tag": "project_tag",
            "Semester": "semester",
            "GitHub Repository": "github_url",
            "Slack": "slack_channel",
            "Generate GitHub": "generate_github",
            "Generate Slack": "generate_slack"
        }

        self.ingest_csv(df, colmap, "ingest_project_csv")
        
    def ingest_user_project_csv(self, df: DataFrame):
        """ingest user project csv"""
        
        colmap: dict[str, str] = {
            
        }

        self.ingest_csv(df, colmap, "ingest_user_project_csv")
        
    # ----------------------------------------------------------------------------------------------------------------------
    # processing of csv files into holding tables
    # ----------------------------------------------------------------------------------------------------------------------
    
    def process_ingest_project_csv(self):
        """Process project csv"""
        
        session = self.s()
            
        semesters = {semester.semester_name.lower(): semester for semester in session.query(Semester).all()}
        
        for row in session.query(IngestProjectCSV).all():
            self.log.info(f"processing project csv row {row.project_tag}...")
            try:
                results = []

                semester = semesters.get(row.semester.lower())
                if not semester:
                    row.outcome = Outcome.failure
                    row.result = "failure: semester discrepancy."
                    self.log.error(f"failure processing project csv row {row.project_tag}: semester discrepancy.")
                    continue
                
                if row.generate_github:
                    if not row.github_url:
                        self.git.create_repo(row.project_tag)
                        row.github_url = f"https://github.com/{self.org}/{row.project_tag}"
                        self.log.info(f"created github repo {row.github_url} for project {row.project_tag}.")
                    else:
                        row.outcome = Outcome.warning
                        results.append("warning: github repo already exists.")
                        self.log.warning(f"skipping creating repo for {row.project_tag}: repo already exists.")
                
                if row.generate_slack:
                    if not row.slack_channel:
                        slack_channel_id = self.slacker.create_channel(row.project_tag)
                        row.slack_channel = slack_channel_id
                        self.log.info(f"created slack channel {slack_channel_id} for project {row.project_tag}.")
                    else:
                        row.outcome = Outcome.warning
                        results.append("warning: slack channel already exists.")
                        self.log.warning(f"skipping creating slack for {row.project_tag}: channel already exists.")

                if results: 
                    row.result = " <> ".join(results)
                else: 
                    row.outcome = Outcome.success
                    row.result = "all systems operational."
                
                project_data = _Project(
                    project_name=row.project_name,
                    project_tag=row.project_tag,
                    semester_id=semester.semester_id,
                    github_url=row.github_url,
                    slack_channel=row.slack_channel
                )
                project = Project(**project_data.model_dump())
                session.add(project)
                
                session.commit()
            
            except (IntegrityError, Exception) as e:
                session.rollback()
                msg = str(e.orig if isinstance(e, IntegrityError) else e).strip().replace("\n", "")
                session.query(IngestProjectCSV).filter(IngestProjectCSV.id == row.id).update({
                    IngestProjectCSV.outcome: Outcome.failure,
                    IngestProjectCSV.result: f"failure: {msg}"
                })
                session.commit()
                self.log.error(f"failure processing project csv row {row.project_tag}: {msg}")
        
if __name__ == "__main__":
    TEST_POSTGRES = os.getenv("TEST_POSTGRES_URL") or ""
    TEST_SLACK_TOKEN = os.getenv("TEST_SLACK_BOT_TOKEN") or ""
    TEST_GITHUB_ORG = "auto-spark"
    TEST_GITHUB_TOKEN = os.getenv("TEST_GITHUB_PAT") or ""
    
    github = Github(TEST_GITHUB_TOKEN, TEST_GITHUB_ORG)
    slacker = Slacker(TEST_SLACK_TOKEN)
    spark = Spark(TEST_POSTGRES, TEST_GITHUB_ORG, slacker, github)
    #df = pd.read_csv("./ingestprojects.csv")
    #spark.ingest_project_csv(df)
    spark.process_ingest_project_csv()