# About
This script is for automatically adding people to COLLABORATORS file in BU Spark!'s repository.
It works in conjunction with BU Spark!s GitHub workflow.

### To run the script:
`python3 script.py <ssh_remote> <branchname> <collaborators_seperated_by_space>`

### Current features
- Checking if the entered username is a valid GitHub username (via GitHub API).
- Adding username to COLLABORATORS file.
- Specifying the branch to make the edit.

### Todo
- Take input from CSV files.
- Sync with each repo's collaborators list.
- Remove users.
- Change permission levels.