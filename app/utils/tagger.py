import pandas as pd
from slugify import slugify

i = 'user_projects_untagged.csv'
o = 'user_projects_tagged.csv'

#i = 'projects_untagged.csv'
#o = 'projects_tagged.csv'

s = 'sp25-'


# Read the CSV file into a DataFrame
df = pd.read_csv(i)

def generate_slug(name): return s+slugify(name)

df['project_tag'] = df.apply(
    lambda row: row['project_tag'] if pd.notnull(row['project_tag']) and str(row['project_tag']).strip() else generate_slug(row['project_name']),
    axis=1
)

df.to_csv(o, index=False)
