import csv
from collections import defaultdict
from time import sleep

from git import Repo
import os
import sys
import requests
import traceback

# You SHOULD change these
# change this to your local path (this is the directory where the repo will be cloned to, and be deleted afterwards)
LOCAL_PATH = '/Users/saucy/Documents/student-projects/special-github-automation/temp/'
SSH_KEY_PATH = '/Users/saucy/.ssh/sparkeng'  # change this to your ssh key path

# You shouldn't need to change these
ERROR = True
NO_ERROR = False
EXCEPTION_LOG = '=============================================EXCEPTION!============================================='
UPSTREAM = 'origin'


def check_valid_user(username):
    try:
        r = requests.get('https://api.github.com/users/' + username, headers={
                         'Authorization': "Bearer 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"})
        if r.status_code == 200:  # if request returns 200, the user exists
            return True, NO_ERROR
        else:
            print(f'Failed to verify user with status code {r.status_code}')
            return False, NO_ERROR
    except:
        return False, ERROR


def add_collaborators(path, collaborators):
    try:
        # open the file with 'r' to first read the current collaborators
        with open(path + 'COLLABORATORS', 'r') as f:
            # filter empty lines and new line characters, should they exist
            exisiting_collaborators = list(
                filter(lambda x: x != '' and x != '\n', f.readlines()))
            exisiting_collaborators = list(
                map(lambda x: x.replace('\n', ''), exisiting_collaborators))
            valid, invalid, errors = [], [], []
            for user in list(filter(lambda x: x not in exisiting_collaborators,
                                    collaborators)):  # first check if the user is already in the file
                # then check if the user exists through the github api, and filter them based on the result
                if check_valid_user(user)[0]:
                    valid.append(user)
                elif check_valid_user(user)[1] == ERROR:
                    errors.append(user)
                else:
                    invalid.append(user)
            f.close()

        # open the file with 'w' to write the existing + new collaborators from scratch
        with open(path + 'COLLABORATORS', 'w') as f:
            if '\n' in exisiting_collaborators:
                exisiting_collaborators.remove('\n')
            to_add = exisiting_collaborators + valid
            print(to_add)
            print('\n'.join(to_add))
            f.write('\n'.join(to_add))
            f.close()

            return_message = 'Following users will be added as collaborators: ' + str(
                valid) + '\nFollowing users were NOT added because they were invalid users: ' + str(invalid)
            if len(errors) > 0:
                return valid, (return_message + '\nUsers not added due to errors: ' + str(errors), ERROR)
            return valid, (return_message, NO_ERROR)
    except Exception as e:
        return [], ('add_collaborators: ' + traceback.format_exc(), ERROR)


def git_checkout(local_path, branchname):
    try:
        repo = Repo(local_path)
        # check if branch exists
        for remote_ref in repo.remotes.origin.refs:
            upstream, reference = remote_ref.name.split('/')
            if upstream == UPSTREAM and reference == branchname:
                repo.git.checkout(branchname)
                return 'Checked out branch: {}'.format(branchname), NO_ERROR

        # if the branch does not exist, create it
        repo.git.checkout('-b', branchname)
        return 'Created and checked out branch: {}'.format(branchname), NO_ERROR
    except Exception as e:
        return 'git_checkout: ' + traceback.format_exc(), ERROR


def git_push(added_collaborators, branchname):
    try:
        if len(added_collaborators) > 0:
            # initialize the repo and the commit message
            repo = Repo(LOCAL_PATH)
            commit_message = 'Added collaborator(s): ' + \
                ', '.join(added_collaborators)

            # add, commit, and push
            repo.git.add(update=True)
            repo.index.commit(commit_message)
            repo.git.push('--set-upstream', UPSTREAM, branchname)
            return (
                'Pushed to remote ({}/{}) with commit message: "{}"'.format(
                    UPSTREAM, branchname, commit_message),
                NO_ERROR)
        else:
            # no new collaborators to add
            return 'No collaborators added.', NO_ERROR
    except Exception as e:
        return 'git_push: ' + traceback.format_exc(), ERROR


def remove_path(path):
    try:
        if os.path.exists(path):
            os.system('rm -rf "{}"'.format(path))
            return 'Removed path ' + path, NO_ERROR
        else:
            return 'No directory to remove.', NO_ERROR
    except Exception as e:
        return 'remove_path: ' + traceback.format_exc(), ERROR


def git_init(remote, local_path, branchname, collaborators=[]):
    results = []
    try:
        # repo init
        # just to make sure if the previous run was not successful
        results.append(remove_path(local_path))
        print(f'cloning ')
        Repo.clone_from(remote, local_path,
                        env={"GIT_SSH_COMMAND": "ssh -i " + SSH_KEY_PATH})  # change this to your ssh key path
        # checkout to the branch
        results.append(git_checkout(local_path, branchname))

        # modifying the collaborators file
        added, log = add_collaborators(local_path, collaborators)
        results.append(log)

        # git ops
        results.append(git_push(added, branchname))
        results.append(remove_path(local_path))
    except Exception as e:
        results.append(('git_init: ' + traceback.format_exc(), ERROR))
        # in case something goes wrong, remove the directory
        results.append(remove_path(local_path))
    finally:
        for result, status in results:  # debugging purposes
            if status == ERROR:
                print('\n{}\n{}{}\n'.format(
                    EXCEPTION_LOG, result, EXCEPTION_LOG))
            else:
                print(result)


# input: python3 test.py <remote (ssh)> <branchname> <collaborators (separated by space)>
def main():
    EXPECTED_HEADER = ["gh_username", "gh_repo"]
    if len(sys.argv) < 2:
        print("Invalid number of arguments expected: script.py <roaster path>")
        exit(-1)
    roster_path = sys.argv[1]
    roster_dict = defaultdict(list)
    with open(roster_path, 'r', encoding='utf-8-sig') as f:
        csvreader = csv.reader(f)
        count = 0
        for row in csvreader:
            # Verify the header row
            print(row)
            if count == 0:
                for (actual, expected) in zip(row, EXPECTED_HEADER):
                    if actual != expected:
                        print(
                            f'Expected {expected} got {actual} for column name.')
                        exit(-1)
                count = count + 1
                continue
            try:
                roster_dict[row[1]].append(row[0])
            except Exception as e:
                print(f'Error with row {count}, skipping')
            count = count + 1
    print(f'Adding the following users to repos: {roster_dict}')
    for repo, user_list in roster_dict.items():
        print(f'Adding users to {repo}...')
        git_init(repo, LOCAL_PATH, 'main', user_list)
        sleep(10)


if __name__ == "__main__":
    main()
