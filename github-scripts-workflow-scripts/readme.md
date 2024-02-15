# Github Scripts Readme

This read me holds all the documentation for this directory.

# Scripts

## `update-workflow.sh` 

This script copies the latest version of the workflow scripts from the template repo to the target repo. 

Usage(on *nix): `sh update-workflows.sh <git repo address>`

It will clone the template repo if you don't have it already, then clone the target repo. Copy the updated workflows and then commit the changes and push. It will finally cleanup files afterwards. Probably only works on *nix systems.

## `add-archive-tag.sh`

Adds an archive tag to the provided repo and pushes tag to remote. 

Provided tag name is pre-pended with `spark-archive-` so all you need is to specify the final part of the tag. For example `fall2021`

Usage: `sh add-archive-tag.sh <tag ending> <github repo url>