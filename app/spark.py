import os
import time
from typing import Any, Generator, List, Literal
from schema import _Project, _User, _UserProject
from models import User, Project, Base, IngestProjectCSV, IngestUserProjectCSV, Semester, UserProject, Outcome, Status
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

class Spark:
    
    # ======================================================================================================================
    # SQLAlchemy functionality
    # ======================================================================================================================
    
    def __init__(self, PGURL: str, org: str, slacker: Slacker, git: Github, drive: Drive):
        self.PGURL = PGURL
        self.org = org
        self.engine = create_engine(self.PGURL, echo=False)
        self.slacker = slacker
        self.drive = drive
        self.git = git
        self.log = log.SparkLogger(name="Spark-s", output=True, persist=True)
        
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
    
    def clear_ingestion_tables(self):
        """clear ingestion tables"""
        
        session = self.s()
        session.query(IngestProjectCSV).delete()
        session.query(IngestUserProjectCSV).delete()
        session.commit()
        session.close()
    
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
                self.log.info(f"ingested row into {table}: {row['project_tag']}")
            except (IntegrityError, Exception) as e:
                msg = str(e.orig if isinstance(e, IntegrityError) else e).strip().replace("\n", "")
                self.log.error(f"failure ingesting row into {table}: {msg}")
                continue
    
    def ingest_project_csv(self, df: DataFrame):
        """ingest project csv"""
        
        colmap: dict[str, str] = {
            "Course": "course",
            "Project Name": "project_name",
            "Project Tag": "project_tag",
            "Semester": "semester",
            "GitHub Repository": "github_url",
            "Slack": "slack_channel",
            "Drive": "drive_url",
            "Generate GitHub": "generate_github",
            "Generate Slack": "generate_slack"
        }

        self.ingest_csv(df, colmap, "ingest_project_csv")
        
    def ingest_user_project_csv(self, df: DataFrame):
        """ingest user project csv"""
        
        colmap: dict[str, str] = {
            "Project Name": "project_name",
            "Project Tag": "project_tag",
            "First Name": "first_name",
            "Last Name": "last_name",
            "Email": "email",
            "BUID": "buid",
            "GitHub Username": "github_username"
        }

        self.ingest_csv(df, colmap, "ingest_user_project_csv")
        
    # ----------------------------------------------------------------------------------------------------------------------
    # processing of csv files into holding tables
    # ----------------------------------------------------------------------------------------------------------------------
    
    def process_ingest_project_csv(self):
        """
            Takes the ingest_project_csv and converts the rows to projects. 
            Creates the necessary slack channels & github repos automatically.
        """
        
        session = self.s()
            
        semesters = {semester.semester_name.lower(): semester for semester in session.query(Semester).all()}
        
        for row in session.query(IngestProjectCSV).all():
            self.log.info(f"processing project csv row {row.project_tag}...")
            try:
                results = []

                semester = semesters.get(row.semester.lower())
                if not semester or (not row.github_url and not row.generate_github):
                    row.result = "failure: semester discrepancy." if not semester else \
                        "failure: missing github url or generate flag."
                    row.outcome = Outcome.failure
                    self.log.error(f"failure processing project csv row {row.project_tag}: {row.result}")
                    session.commit()
                    continue
                
                if row.generate_github:
                    if not row.github_url:
                        code, m = self.git.create_repo(row.project_tag)
                        if code != 201 and "name already exists on this account" not in str(m):
                            row.outcome = Outcome.failure
                            results.append(f"failure: {m}")
                            self.log.error(f"failure creating github repo for {row.project_tag}: {m}")
                            session.commit()
                            continue
                        row.github_url = f"https://github.com/{self.org}/{row.project_tag}.git"
                        self.log.info(f"created github repo {row.github_url} for project {row.project_tag}.")
                    else:
                        row.outcome = Outcome.warning
                        results.append("warning: github repo already exists.")
                        self.log.warning(f"skipping creating repo for {row.project_tag}: repo already exists.")
                
                if row.generate_slack:
                    if not row.slack_channel:
                        ####################################################################################################
                        # CUSTOM SLACK CHANNEL NAME LOGIC GOES HERE
                        ####################################################################################################
                        try:
                            slack_prefix = "i-sp25-"
                            slack_course = (row.course or "").replace("/", "-").replace(" ", "-")
                            slack_tag = row.project_tag

                            slack_f_name = slack_prefix + (slack_course + "-" if slack_course else "") + slack_tag
                            slack_lower_name = slack_f_name.lower()
                            
                            slack_channel_id = self.slacker.create_channel(
                                slack_lower_name,
                                True
                            )
                            slack_channel_name = self.slacker.get_channel_name(slack_channel_id)
                            if slack_channel_name != "undefined-slack-channel":
                                row.slack_channel = slack_channel_name
                                self.log.info(f"created or fetched slack channel {slack_channel_id} for project {row.project_tag}.")
                            else:
                                self.log.error(f"slack channel creation error for {row.project_tag}: {slack_channel_name}")
                        except Exception as e:
                            row.outcome = Outcome.warning
                            results.append(f"warning: {e}")
                            self.log.warning(f"slack channel creation error for {row.project_tag}: {e}")
                    else:
                        row.outcome = Outcome.warning
                        results.append("warning: slack channel already exists.")
                        self.log.warning(f"skipping creating slack for {row.project_tag}: channel already exists.")
                        
                if not row.github_url:
                    row.outcome = Outcome.failure
                    results.append("failure: missing github url.")
                    self.log.error(f"failure processing project csv row {row.project_tag}: missing github url.")
                    session.commit()
                    continue

                if results: 
                    row.result = " <> ".join(results)
                else: 
                    row.outcome = Outcome.success
                    row.result = "all systems operational."
                
                project_data = _Project(
                    course=row.course,
                    project_name=row.project_name,
                    project_tag=row.project_tag,
                    semester_id=semester.semester_id,
                    github_url=row.github_url,
                    drive_url=row.drive_url,
                    slack_channel=row.slack_channel
                )
                project = Project(**project_data.model_dump())
                session.add(project)
                
                session.commit()
            
            except (IntegrityError, Exception) as e:
                print(e)
                session.rollback()
                msg = str(e.orig if isinstance(e, IntegrityError) else e).strip().replace("\n", "")
                session.query(IngestProjectCSV).filter(IngestProjectCSV.id == row.id).update({
                    IngestProjectCSV.outcome: Outcome.failure,
                    IngestProjectCSV.result: f"failure: {msg}"
                })
                session.commit()
                self.log.error(f"integrity failure processing project csv row {row.project_tag}: {msg}")
        
        session.close()
        
    def process_ingest_user_project_csv(self):
        """Takes the ingest_user_project_csv and converts the rows to users and user_projects."""
        
        session = self.s()
        
        for row in session.query(IngestUserProjectCSV).all():
            self.log.info(f"processing user {row.email} for project {row.project_tag}...")
            try:
                project = session.query(Project).filter(Project.project_tag == row.project_tag).first()
                
                if not (project and row.email and row.github_username):
                    row.outcome = Outcome.failure
                    row.result = "failure: missing project, email, or github username."
                    self.log.error(f"failure processing {row.project_tag}: missing project, email, or github.")
                    session.commit()
                    continue
                
                user = session.query(User).filter(
                    (User.email == row.email) | (User.github_username == row.github_username)
                ).first()
                if not user:
                    user_data = _User(
                        first_name=row.first_name,
                        last_name=row.last_name,
                        email=row.email,
                        buid=row.buid,
                        github_username=row.github_username
                    )
                    user = User(**user_data.model_dump())
                    session.add(user)
                    session.flush()
                
                user_project_data = _UserProject(
                    project_id=project.project_id,
                    user_id=user.user_id,
                    status_github=Status.started,   
                    status_slack=Status.started,
                    status_drive=Status.started,
                    github_result=None,
                    slack_result=None,
                    drive_result=None,
                    created_at=None
                )
                user_project = UserProject(**user_project_data.model_dump())
                session.add(user_project)
                
                row.outcome = Outcome.success
                row.result = "all systems operational."
                
                session.commit()
                
            except (IntegrityError, Exception) as e:
                session.rollback()
                msg = str(e.orig if isinstance(e, IntegrityError) else e).strip().replace("\n", "")
                session.query(IngestUserProjectCSV).filter(IngestUserProjectCSV.id == row.id).update({
                    IngestUserProjectCSV.outcome: Outcome.failure,
                    IngestUserProjectCSV.result: f"failure: {msg}"
                })
                session.commit()
                self.log.error(f"failure processing project csv row {row.project_tag}: {msg}")
                
        session.close()
    
    # ----------------------------------------------------------------------------------------------------------------------
    # core automation functionality
    # ----------------------------------------------------------------------------------------------------------------------
        
    def automate_github(self, tags: List[str] = [], start_state: Status = Status.started, end_state: Status = Status.push):
        """
            Automates the handling of permissioning users for projects.
        """
        
        session = self.s()
        
        # get all user projects from the tags if the tags are provided otherwise get all user projects
        user_projects = session.query(UserProject).join(Project).filter(
            Project.project_tag.in_(tags or [up.project.project_tag for up in session.query(UserProject).all()]),
            UserProject.status_github == start_state
        ).all()
        
        def permission_lookup(status: Status) -> Literal['pull', 'triage', 'push', 'maintain', 'admin']:
            if status == Status.push:       return 'push'
            else: return "pull"
        
        for user_project in user_projects:
            try:
                project = user_project.project
                user = user_project.user
                self.log.info(f"automating from {start_state} to {end_state} for {user.email} on {project.project_tag}...")
                
                if not self.git.check_user_exists(user.github_username):
                    user_project.status_github = Status.failed
                    user_project.github_result = "failure: github user does not exist."
                    self.log.error(f"failure automating {user.email} on {project.project_tag}: github user does not exist.")
                    session.commit()
                    continue
                else: self.log.info(f"found github user {user.github_username}.")
                
                if end_state == Status.removed:
                    code, m = self.git.remove_user_from_repo(repo_url=project.github_url, user=user.github_username)
                    if code != 204:
                        user_project.status_github = Status.failed
                        user_project.github_result = f"failure: {m}"
                        self.log.error(f"failure automating {user.email} on {project.project_tag}: {m}")
                        session.commit()
                        continue
                    user_project.status_github = end_state
                    user_project.github_result = "all systems operational."
                    self.log.info(f"automated {user.email} on {project.project_tag} to {end_state}.")
                    session.commit()
                    continue
                
                if self.git.check_user_is_collaborator(repo_url=project.github_url, user=user.github_username) or \
                    user.github_username in self.git.get_users_invited_on_repo(repo_url=project.github_url):
                    self.git.change_user_permission_on_repo(
                        repo_url=project.github_url,
                        user=user.github_username,
                        permission=permission_lookup(end_state)
                    )
                    user_project.status_github = end_state
                    user_project.github_result = "already a collaborator - all systems operational."
                    self.log.info(f"user {user.email} already a collaborator on {project.project_tag} with {end_state}.")
                    session.commit()
                    continue
                
                if start_state == Status.started or \
                    (start_state == Status.removed and end_state == Status.push) or \
                    (start_state == Status.failed and end_state == Status.push):
                    code, m = self.git.add_user_to_repo(
                        repo_url=project.github_url,
                        user=user.github_username,
                        permission=permission_lookup(end_state)
                    )
                    if code != 201:
                        user_project.status_github = Status.failed
                        user_project.github_result = f"failure: {m}"
                        self.log.error(f"failure automating {user.email} on {project.project_tag}: {m}")
                        session.commit()
                        continue
                    else: self.log.info(f"added {user.email} to {project.project_tag}.")
                    user_project.status_github = end_state
                    user_project.github_result = "all systems operational."
                    self.log.info(f"automated {user.email} on {project.project_tag} to {end_state}.")
                    session.commit()
                    continue
                
            except (IntegrityError, Exception) as e:
                session.rollback()
                msg = str(e.orig if isinstance(e, IntegrityError) else e).strip().replace("\n", "")
                user_project.status_github = Status.failed
                user_project.github_result = f"failure: {msg}"
                session.commit()
                self.log.error(f"automation failed {user_project.user.email} on {user_project.project.project_tag}: {msg}")
                
        session.close() 
    
    def automate_slack(self, tags: List[str] = []):
        """Automates adding users to slack channels."""
        
        session = self.s()
        
        user_projects = session.query(UserProject).join(Project).filter(
            Project.project_tag.in_(tags or [up.project.project_tag for up in session.query(UserProject).all()]),
            UserProject.status_slack.in_([Status.started, Status.failed])
        ).all()
        
        for user_project in user_projects:
            time.sleep(1)
            try:
                project = user_project.project
                user = user_project.user
                self.log.info(f"automating slack for {user.email} on {project.project_tag}...")
                
                if not project.slack_channel:
                    user_project.status_slack = Status.failed
                    user_project.slack_result = "failure: slack channel does not exist."
                    self.log.error(f"failed as slack channel does not exist for {project.project_tag}.")
                    session.commit()
                    continue
                    
                slack_uid = self.slacker.get_user_id(email=user.email)
                if not slack_uid:
                    user_project.status_slack = Status.failed
                    user_project.slack_result = "failure: slack user does not exist."
                    self.log.error(f"failed as slack user does not exist for {user.email}.")
                    session.commit()
                    continue
                
                slack_channel_id = self.slacker.get_channel_id(channel_name=project.slack_channel)
                self.slacker.invite_users_to_channel(
                    channel_id=slack_channel_id,
                    user_ids=slack_uid,
                    retries=3
                )
                user_project.status_slack = Status.push
                user_project.slack_result = "all systems operational."
                self.log.info(f"automated slack for {user.email} on {project.project_tag}.")
                session.commit()
                
            except (IntegrityError, Exception) as e:
                session.rollback()
                msg = str(e.orig if isinstance(e, IntegrityError) else e).strip().replace("\n", "")
                
                if "already_in_channel" in msg:
                    user_project.status_slack = Status.push
                    user_project.slack_result = "user already in channel."
                    self.log.warning(
                        f"skipping as user already in channel for \
                        {user_project.user.email} on {user_project.project.project_tag}."
                    )
                    session.commit()
                else:
                    user_project.status_slack = Status.failed
                    user_project.slack_result = f"failure: {msg}"
                    session.commit()
                    self.log.error(
                        f"automation failed {user_project.user.email} on {user_project.project.project_tag}: {msg}"
                    )
    
    def automate_drive(self, tags: List[str] = []):
        """Automates sharing google drive folders."""
        
        session = self.s()
        
        user_projects = session.query(UserProject).join(Project).filter(
            Project.project_tag.in_(tags or [up.project.project_tag for up in session.query(UserProject).all()]),
            UserProject.status_drive == Status.started
        ).all()
        
        for user_project in user_projects:
            try:
                project = user_project.project
                user = user_project.user
                self.log.info(f"automating drive for {user.email} on {project.project_tag}...")
                
                if not project.drive_url:
                    user_project.status_drive = Status.failed
                    user_project.drive_result = "failure: drive url does not exist."
                    self.log.error(f"failed as drive url does not exist for {project.project_tag}.")
                    session.commit()
                    continue
                    
                ############################################################################################################
                # CUSTOM GOOGLE DRIVE SHARING LOGIC GOES HERE
                ############################################################################################################
                
                self.drive.share(project.drive_url, user.email)
                
                user_project.status_drive = Status.push
                user_project.drive_result = "all systems operational."
                self.log.info(f"automated drive for {user.email} on {project.project_tag}.")
                session.commit()
                
            except (IntegrityError, Exception) as e:
                session.rollback()
                msg = str(e.orig if isinstance(e, IntegrityError) else e).strip().replace("\n", "")
                user_project.status_drive = Status.failed
                user_project.drive_result = f"failure: {msg}"
                session.commit()
                self.log.error(
                    f"automation failed {user_project.user.email} on {user_project.project.project_tag}: {msg}"
                )
    
if __name__ == "__main__":
    # POSTGRES = os.getenv("POSTGRES_URL") or ""
    SLACK_TOKEN = os.getenv("SLACK_BOT_TOKEN") or ""
    GITHUB_ORG = "BU-Spark"
    GITHUB_TOKEN = os.getenv("SPARK_GITHUB_PAT") or ""
    
    POSTGRES = os.getenv("TEST_POSTGRES_URL") or ""
    #SLACK_TOKEN = os.getenv("TEST_SLACK_BOT_TOKEN") or ""
    #GITHUB_ORG = "auto-spark"
    #GITHUB_TOKEN = os.getenv("TEST_GITHUB_PAT") or ""
    
    github = Github(GITHUB_TOKEN, GITHUB_ORG)
    slacker = Slacker(SLACK_TOKEN)
    drive = Drive()
    spark = Spark(POSTGRES, GITHUB_ORG, slacker, github, drive)
    
    #ingestproject = pd.read_csv("./ingestproject.csv")
    #spark.ingest_project_csv(ingestproject)
    
    #ingestuserproject = pd.read_csv("./ingestuserproject.csv")
    #spark.ingest_user_project_csv(ingestuserproject)
    
    print("---")
    print("---")
    print("---")
    
    #spark.process_ingest_project_csv()
    #spark.process_ingest_user_project_csv()
    
    spark.automate_github(tags=["commonwealth-climate"], start_state=Status.failed, end_state=Status.push)
    
    ds519channels = [
        #"i-sp25-ds519-488-d4-constituent-app",
        "i-sp25-ds519_488-social-justice-app",
        #"i-sp25-ds519-488-bva",
        #"i-sp25-ds519-488-community-service-hours",
        #"i-sp25-ds519-488-auto-mech-challenge",
        #"i-sp25-ds519-488-mass-courts-v3",
        "i-sp25-ds519_488-cmovf",
        "i-sp25-ds519_488-academico-ai",
        "i-sp25-ds519_488-mola"
    ]
    ds519tags = [
        #"constituent-app",
        "social-justice-app",
        #"bva",
        #"community-service-hours",
        #"auto-mech-challenge",
        #"mass-courts-v3",
        "cmovf",
        "academico-ai",
        "mola"
    ]
    #spark.automate_slack(tags=ds519tags)
    
    ds549channels = [
        "i-sp25-ds549-coffeechat-matchmaker",
        "i-sp25-ds549-wlfc-archive"
    ]
    ds549tags = [
        "wlfc-archive",
        "coffeechat-matchmaker"
    ]
    
    #spark.automate_slack(tags=ds549tags)
    
    #saadid = slacker.get_user_id("saad7@bu.edu")
    #langid = slacker.get_user_id("langd0n@bu.edu")
    #omarid = slacker.get_user_id("oea@bu.edu")
    
    #for c in ds519channels:
    #    print(c)
    #    slacker.invite_users_to_channel(
    #        slacker.get_channel_id(c),
    #        [saadid, langid, omarid]
    #    )
        