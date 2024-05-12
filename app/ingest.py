# import =====================================

import os
import psycopg2
import psycopg2.extras
import pandas as pd
from dotenv import load_dotenv

# env ========================================

load_dotenv()
POSTGRES_URL = os.getenv('POSTGRES_URL')

# ============================================

def connect(): return psycopg2.connect(POSTGRES_URL)

def dump(table_name):
    """ Dumps data from a specified table """
    conn = connect()
    cursor = conn.cursor()
    
    valid_tables = ['user', 'project', 'semester', 'user_project', 'csv']
    if table_name not in valid_tables:
        print("Invalid table name")
        return
    
    try:
        cursor.execute(f"SELECT * FROM \"{table_name}\"")
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        if not rows:
            print(f"No data available in {table_name}.")
            return

        print(f"{table_name}:")
        print(f"{columns}")
        for row in rows: print(row)
    except psycopg2.Error as e: print(f"An error occurred: {e}")
    finally:
        cursor.close()
        conn.close()

def ingest():
    """Ingests data from the 'csv' table to the 'user', 'project', 'semester', and 'user_project' tables."""
    conn = connect()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM csv")
    rows = cursor.fetchall()
    
    for row in rows:
        try:
            print("---")
            print("ROW:", row[:-1])
            csvid, semester, course, project, organization, team, role, fname, lname, name, email, buid, github, process_status = row
        
            # try to find the user in the user table, if not found, insert it
            user_id = None
            cursor.execute(f"SELECT * FROM \"user\" WHERE email = '{email}'")
            fetchuser = cursor.fetchone()
            if not fetchuser:
                # user table schema is (id, buid, name, email, github)
                print("- USER NOT FOUND, INSERTING", buid, name, email, github)
                cursor.execute(f"INSERT INTO \"user\" (buid, name, email, github) VALUES ('{buid}', '{name}', '{email}', '{github}') RETURNING user_id")
                user_id = cursor.fetchone()[0]
                print("> USER ID", user_id)
            else:
                print("- USER FOUND:", fetchuser)
                user_id = fetchuser[0]

            # try to find the project in the project table, if not found, insert it            
            project_id = None
            cursor.execute(f"SELECT * FROM project WHERE project_name = '{project}'")
            fetchproject = cursor.fetchone()
            if not fetchproject:                
                # get the semester_id from the semester table by using semester name
                print("- GETTING SEMESTER ID", semester)
                cursor.execute(f"SELECT * FROM semester WHERE semester_name = '{semester}'")
                semester_id = cursor.fetchone()[0]
                
                # insert the project into the project table with the schema (project_name, semester_id, github_url, created_at) with the github url being null
                print("- INSERTING PROJECT", project, semester_id)
                cursor.execute(f"INSERT INTO project (project_name, semester_id) VALUES ('{project}', {semester_id}) RETURNING project_id")
                project_id = cursor.fetchone()[0]
            else:
                print("- PROJECT FOUND:", fetchproject)
                project_id = fetchproject[0]
            
            # update the user_project table, schema is (user_id, project_id, created_at, status), use 'started' as status
            print("- INSERTING USER_PROJECT", user_id, project_id, "started")
            cursor.execute(f"INSERT INTO user_project (project_id, user_id, status) VALUES ({project_id}, {user_id}, 'started')")
            
            # now finally, update the csv table status column to "all systems operational"
            print("- UPDATING CSV WITH SUCCESS", csvid)
            cursor.execute(f"UPDATE csv SET status = 'all systems operational' WHERE id = {csvid}")

            conn.commit()  # Commit the transaction
        except psycopg2.Error as e:
            print(f"An error occurred: {e}")
            
            # update the csv table status column with the text of the error
            print("-UPDATING CSV WITH ERROR", csvid)
            conn.rollback()
            cursor.execute(f"UPDATE csv SET status = '{e}' WHERE id = {csvid}")
            conn.commit()
        
    cursor.close()
    conn.close()  # Also close the connection after processing

def information():
    """Returns a list of dictionaries containing information about the users, projects, and semesters."""
    
    result = []
    
    conn = connect()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM \"user\"")
    users = cursor.fetchall()
    
    for user in users:
        print("=====================================")
        user_id = user[0]
        print("- USER:", user)
        
        cursor.execute(f"SELECT * FROM user_project WHERE user_id = {user_id}")
        user_projects = cursor.fetchall()
        
        for user_project in user_projects:
            project_id = user_project[0]
            print("- USER_PROJECT:", user_project)
            
            cursor.execute(f"SELECT * FROM project WHERE project_id = {project_id}")
            project = cursor.fetchone()
            print("- PROJECT:", project)
            
            project_name = project[1]
            semester_id = project[2]
            github_url = project[3]
            
            cursor.execute(f"SELECT * FROM semester WHERE semester_id = {semester_id}")
            semester = cursor.fetchone()
            print("- SEMESTER:", semester)
            
            result.append({
                "buid": user[3],
                "name": user[1],
                "email": user[2],
                "github": user[4],
                "project_name": project_name,
                "github_url": github_url if github_url else "???",
                "semester": semester[1]
            })
    
    cursor.close()
    conn.close()
    print("=====================================")
    print(result)
    return result    

def tcsv():
    # get the csv table data and return it a serialized format
    conn = connect()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM csv")
    rows = cursor.fetchall()
    
    result = []
    for row in rows:
        result.append({
            "id": row[0],
            "semester": row[1],
            "course": row[2],
            "project": row[3],
            "organization": row[4],
            "team": row[5],
            "role": row[6],
            "fname": row[7],
            "lname": row[8],
            "name": row[9],
            "email": row[10],
            "buid": row[11],
            "github": row[12],
            "status": row[13]
        })
    
    cursor.close()
    conn.close()
    
    return result

def ucsv(dataframe):
    """Inserts data from a pandas DataFrame to the 'csv' PostgreSQL table."""
    conn = connect()
    cursor = conn.cursor()
    
    colmap = {
        'Semester': 'semester',
        'Course': 'course',
        'Project': 'project',
        'Organization': 'organization',
        'Team': 'team',
        'Role': 'role',
        'First Name': 'first_name',
        'Last Name': 'last_name',
        'Full Name': 'full_name',
        'Email': 'email',
        'BUID': 'buid',
        'Github Username': 'github_username',
    }
    dataframe.rename(columns=colmap, inplace=True)
    
    if 'status' not in dataframe.columns:
        dataframe['status'] = 'unprocessed' 

    # Constructing the SQL INSERT statement dynamically based on DataFrame columns
    columns = ', '.join(dataframe.columns)
    values_placeholder = ', '.join(['%s'] * len(dataframe.columns))
    insert_query = f"INSERT INTO csv ({columns}) VALUES ({values_placeholder})"
    
    print(insert_query)

    # Preparing data tuples from the dataframe
    records_list = [tuple(x) for x in dataframe.to_numpy()]

    try:
        # Execute the SQL statement
        psycopg2.extras.execute_batch(cursor, insert_query, records_list)
        conn.commit()
    except psycopg2.DatabaseError as e:
        print(f"An error occurred: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

# ========================================

if __name__ == "__main__":
    #for table in ['user', 'project', 'semester', 'user_project', 'csv']:
    #    dump(table)
    #ingest()

    information()
