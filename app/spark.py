import os
from models import User, Project, Base, IngestProjectCSV, Semester, UserProject
from schema import _Project
from slacker import Slacker
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from pandas import DataFrame

class Spark:
    
    # =============================================================================================
    # SQLAlchemy functionality
    # =============================================================================================
    
    def __init__(self, URL: str, token: str):
        self.URL = URL
        self.engine = create_engine(self.URL, echo=False)
        self.slacker = Slacker(token)
        
    def s(self):
        return sessionmaker(bind=self.engine)()
        
    @contextmanager
    def scope(self):
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
            
    # =============================================================================================
    # auto spark functionality
    # =============================================================================================        
    
    # ---------------------------------------------------------------------------------------------
    # ingestion of csv files into holding tables
    # ---------------------------------------------------------------------------------------------
    
    def ingest_csv(self, df: DataFrame, colmap: dict[str, str], table: str):
        """ingest csv"""
        
        tomap = {
            csv_col: \
                db_col for csv_col, db_col in colmap.items() 
                if csv_col != db_col and csv_col in df.columns
        }
        if tomap: df = df.rename(columns=tomap)
    
        if self.engine: df.to_sql(table, self.engine, if_exists='append', index=False)
    
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
        
    # ---------------------------------------------------------------------------------------------
    # processing of csv files into holding tables
    # ---------------------------------------------------------------------------------------------
    
    def process_ingest_project_csv(self):
        """Process project csv"""
        with self.scope() as session:
            for row in session.query(IngestProjectCSV).all():
                
                semester = session.query(Semester).filter(Semester.semester_name == row.semester.lower()).first()
                
                if not semester:
                    print(f"Semester {row.semester} not found")
                    continue
                
                project_data = _Project(
                    project_name=row.project_name,
                    project_tag=row.project_tag,
                    semester_id=semester.semester_id,
                    github_url=row.github_url,
                    slack_channel=row.slack_channel
                )
                project = Project(**project_data.model_dump())
                session.add(project)
                
                if row.generate_github:
                    # generate github
                    pass
                if row.generate_slack:
                    channel_name = row.project_tag
                    channel_id = self.slacker.create_channel(channel_name=channel_name, is_private=False)
                    
            session.commit()
        
if __name__ == "__main__":
    TEST_POSTGRES = os.getenv("TEST_POSTGRES_URL") or ""
    TEST_SLACK_TOKEN = os.getenv("TEST_SLACK_BOT_TOKEN") or ""
    spark = Spark(TEST_POSTGRES, TEST_SLACK_TOKEN)
    #df = pd.read_csv("./ingestprojects.csv")
    #spark.ingest_project_csv(df)
    spark.process_ingest_project_csv()