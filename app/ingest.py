import psycopg2
import psycopg2.extras
import pandas as pd

# Establish connection
def connect(): return psycopg2.connect("postgresql://retool:NhGgxmX3b6oO@ep-mute-violet-06732076.us-west-2.retooldb.com/retool?sslmode=require")


def dump(table_name):
    conn = connect()
    cursor = conn.cursor()
    
    # Define a list of valid table names to prevent SQL injection
    valid_tables = ['user', 'repo', 'project', 'semester', 'project_repo', 'user_project', 'csv']
    if table_name not in valid_tables:
        print("Invalid table name")
        return
    
    safe_table_name = f'"{table_name}"'  # Use double quotes around the table name
    try:
        cursor.execute(f"SELECT * FROM {safe_table_name}")
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        if not rows:
            print(f"No data available in {table_name}.")
            return

        print(f"{table_name}:")
        print(f"Columns: {columns}")
        for row in rows:
            print(row)
        print()
    except psycopg2.Error as e:
        print(f"An error occurred: {e}")

def ingest():
    conn = connect()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM csv")
    rows = cursor.fetchall()
    
    for row in rows:
        try:
            print("---")
            print("ROW:", row)
            csvid = row[0]
            semester = row[1]
            course = row[2]
            project = row[3]
            organization = row[4]
            team = row[5]
            role = row[6]
            fname = row[7]
            lname = row[8]
            name = row[9]
            email = row[10]
            buid = row[11]
            github = row[12]
        
            # try to find the user in the user table, if not found, insert it
            user_id = None
            cursor.execute(f"SELECT * FROM \"user\" WHERE email = '{email}'")
            user = cursor.fetchone()
            if not user:
                # user table schema is (id, buid, name, email, github)
                print("-USER NOT FOUND, INSERTING", buid, name, email, github)
                cursor.execute(f"INSERT INTO \"user\" (buid, name, email, github) VALUES ('{buid}', '{name}', '{email}', '{github}') RETURNING user_id")
                user_id = cursor.fetchone()[0]
                print(">USER ID", user_id)
            else:
                print("-USER FOUND", user)
                user_id = user[0]

            # try to find the project in the project table, if not found, insert it
            # first check the project table if the project exists, if so all good, 
            # otherwise, first insert project into project table
            # then insert into repo table
            
            project_id = None
            cursor.execute(f"SELECT * FROM project WHERE project_name = '{project}'")
            tproject = cursor.fetchone()
            if not tproject:
                # project table schema is (id, project_name, project_url), insert empty project_url for now
                print("-PROJECT NOT FOUND, INSERTING", project)
                cursor.execute(f"INSERT INTO project (project_name, project_url) VALUES ('{project}', '') RETURNING id")
                project_id = cursor.fetchone()[0]
                print(">PROJECT ID", project_id)
                
                # repo table schema is (id, project_name, github_url, created_at), insert null for github_url 
                print("-INSERTING REPO", project)
                cursor.execute(f"INSERT INTO repo (project_name, github_url) VALUES ('{project}', null) RETURNING id")
                repo_id = cursor.fetchone()[0]
                print(">REPO ID", repo_id)
                
                # get the semester id from the semester table by using semester name
                print("-GETTING SEMESTER ID", semester)
                cursor.execute(f"SELECT * FROM semester WHERE friendly_name = '{semester}'")
                semester_id = cursor.fetchone()[0]
                print(">SEMESTER ID", semester_id)
                
                # project_repo table schema is (project_id, repo_id, semester_id)
                print("-INSERTING PROJECT_REPO", project_id, repo_id, semester)
                cursor.execute(f"INSERT INTO project_repo (project_id, repo_id, semester_id) VALUES ({project_id}, {repo_id}, {semester_id}) RETURNING project_id")
                project_repo_id = cursor.fetchone()[0]
                print(">PROJECT_REPO ID", project_repo_id)
            else:
                print("PROJECT FOUND", tproject)
                project_id = tproject[0]
                
            # update the user_project table
            # user_project table schema is (user_id, project_id, created_at, is_applied, is_invited) , use false for is_applied and is_invited
            print("-INSERTING USER_PROJECT", user_id, project_id)
            cursor.execute(f"INSERT INTO user_project (user_id, project_id, is_applied, is_invited) VALUES ({user_id}, {project_id}, false, false)")
            
            # now finally, update the csv table process_status column to "all systems operational"
            print("-UPDATING CSV WITH SUCCESS", csvid)
            cursor.execute(f"UPDATE csv SET process_status = 'all systems operational' WHERE id = {csvid}")

            conn.commit()  # Commit the transaction
        except psycopg2.Error as e:
            print(f"An error occurred: {e}")
            
            # update the csv table process_status column with the text of the error
            print("-UPDATING CSV WITH ERROR", csvid)
            conn.rollback()
            cursor.execute(f"UPDATE csv SET process_status = '{e}' WHERE id = {csvid}")
            conn.commit()
        
    cursor.close()
    conn.close()  # Also close the connection after processing

def information():
    # return all users (name, email, buid, github) alongside with their projects, and what their projects are (repo, semester)
    # return this in a dictionary format
    
    result = []
    
    conn = connect()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM \"user\"")
    users = cursor.fetchall()
    
    for user in users:
        user_id = user[0]
        print("USER:", user)
        
        cursor.execute(f"SELECT * FROM user_project WHERE user_id = {user_id}")
        user_projects = cursor.fetchall()
        
        projects = []
        for user_project in user_projects:
            project_id = user_project[1]
            print("USER_PROJECT:", user_project)
            
            cursor.execute(f"SELECT * FROM project WHERE id = {project_id}")
            project = cursor.fetchone()
            print("PROJECT:", project)
            
            project_name = project[1]
            
            cursor.execute(f"SELECT * FROM project_repo WHERE project_id = {project_id}")
            project_repo = cursor.fetchone()
            print("PROJECT_REPO:", project_repo)
            
            repo_id = project_repo[1]
            semester_id = project_repo[2]
            
            cursor.execute(f"SELECT * FROM repo WHERE id = {repo_id}")
            repo = cursor.fetchone()
            print("REPO:", repo)
            
            cursor.execute(f"SELECT * FROM semester WHERE id = {semester_id}")
            semester = cursor.fetchone()
            print("SEMESTER:", semester)
            
            #projects.append({
            #    "project_name": project_name,
            #    "repo": repo[2],
            #    "semester": semester[1]
            #})
            
            result.append({
                "buid": user[1],
                "name": user[2],
                "email": user[3],
                "github": user[4],
                "project_name": project_name,
                "repo": repo[2],
                "semester": semester[1]
            })
            
            
            
        #result[user[1]] = {
        #    "buid": user[1],
        #    "name": user[2],
        #    "email": user[3],
        #    "github": user[4],
        #    "projects": projects
        #}
    
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
            "process_status": row[13]
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
    
    if 'process_status' not in dataframe.columns:
        dataframe['process_status'] = 'unprocessed' 

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
    #for table in ['user', 'repo', 'project', 'semester', 'project_repo', 'user_project', 'csv']:
        #dump(table)
    #ingest()

    information()
