# About
A collection scripts for automating the management of the BU Spark! GitHub organization.

There are two main scripts in this repository:
- `script.py` is for automatically adding people to COLLABORATORS file in BU Spark!'s repository.
- `github_rest.py` is a collection of functions for interacting with the GitHub REST API and is now the preferred method for adding users to repositories.
This script is for automatically adding people to COLLABORATORS file in BU Spark!'s repository.
It works in conjunction with BU Spark!s GitHub workflow.

## `github_rest.py` Directions
This script is meant to be integrated somewhere else but for now is just a collection of functions that can be used.

Modify the `main` function as needed to read the correct input file and call the correct functions.

There is basic logging that is in place but it needs some updating to increase the verbosity of the logs. 

The script should also probably be refactored to use a class instead of a bunch of functions.

## `script.py` Directions

### To run the script:
`python3 script.py <ssh_remote> <branchname> <collaborators_seperated_by_space>`

### Current features
- Checking if the entered username is a valid GitHub username (via GitHub API).
- Adding username to COLLABORATORS file.
- Specifying the branch to make the edit.

### Global Variable Setup
Check the top of the Python script for a serious of global variables that should be set for propper function.

### Todo
- Take input from CSV files.
- Sync with each repo's collaborators list.
- Remove users.
- Change permission levels.
