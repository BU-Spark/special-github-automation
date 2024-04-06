import requests
import csv
import os

from typing import Literal, Optional, Tuple
from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv()
GITHUB_PAT = os.getenv('GITHUB_PAT')
print(f"GitHub PAT: {GITHUB_PAT}")

class Automation:
    GITHUB_PAT = None
    HEADERS = None

    def __init__(self, GITHUB_PAT: str):
        self.GITHUB_PAT = GITHUB_PAT
        self.HEADERS = {
            'Accept': 'application/vnd.github+json',
            'Authorization': f'Bearer {GITHUB_PAT}',
            'X-GitHub-Api-Version': '2022-11-28'
        }
        print(f"GitHub PAT: {GITHUB_PAT}")
    
    def extract_user_repo_from_ssh(self, ssh_url: str) -> Tuple[str, str]:
        """
        Extracts the username and repository name from a given SSH URL.

        Args:
            ssh_url (str): The SSH URL of the GitHub repository.

        Returns:
            Tuple[str, str]: A tuple containing the username and repository name.

        Raises:
            ValueError: If the SSH URL does not start with "git@github.com:" or is missing required parts.
        """

        if not ssh_url.startswith("git@github.com:"):
            raise ValueError("Invalid SSH URL format")
        try:
            ssh_url_parts = ssh_url.split(':')[-1].split('/')
            username = ssh_url_parts[0]
            repo_name = ssh_url_parts[1].split('.')[0]
            print(f"Username: {username}, Repo: {repo_name}")
            return username, repo_name
        except IndexError as e:
            raise ValueError("SSH URL is missing required parts") from e

    def check_user_exists(self, user: str) -> Tuple[int, Optional[str]]:
        """
        Checks if a GitHub user exists.

        Args:
            user (str): The username of the GitHub user to check.

        Returns:
            Tuple[int, Optional[str]]: A tuple containing the HTTP status code and an optional error message.
        """

        response = requests.get(
            f'https://api.github.com/users/{user}', headers=self.HEADERS, timeout=2)
        if response.status_code == 200:
            return 200, None
        elif response.status_code == 404:
            return 404, f'User does not exist: {response.json()}'
        elif response.status_code == 401:
            return 401, f'Unauthorized: Invalid GitHub PAT, {response.json()}'
        elif response.status_code == 403 or response.status_code == 429:
            return 403, f'Forbidden: Rate limit exceeded: {response.json()}'
        else:
            return response.status_code, f'An error occurred: {response.json()}'
        
    def add_user_to_project(self, ssh_url: str, user: str, permission: Literal['pull', 'triage', 'push', 'maintain', 'admin']) -> Tuple[int, Optional[str]]:
        """
        Adds a user to a GitHub project with the specified permission.

        This function first extracts the username and repository name from the provided SSH URL. It then checks if the user exists on GitHub. If the user exists, it attempts to add the user to the specified repository with the given permission level. The function handles various HTTP status codes to provide meaningful feedback on the operation's outcome.

        Args:
            ssh_url (str): The SSH URL of the GitHub repository.
            user (str): The username of the GitHub user to add to the project.
            permission (Literal['pull', 'triage', 'push', 'maintain', 'admin']): The permission level to grant the user.

        Returns:
            Tuple[int, Optional[str]]: A tuple containing the HTTP status code and an optional error message.
        Raises:
            Exception: If an unexpected error occurs.

        """
        try:

            username, repo_name = self.extract_user_repo_from_ssh(ssh_url)

            status_code, error_message = self.check_user_exists(user)
            if error_message:
                return status_code, error_message

            # Add the user to the project with the specified permission
            response = requests.put(f'https://api.github.com/repos/{username}/{repo_name}/collaborators/{user}',
                                    headers=self.HEADERS,

                                    json={'permission': permission}, timeout=2)
            if response.status_code == 201:
                return response.status_code, 'User added to the project with the specified permission'
            elif response.status_code == 204:
                return response.status_code, 'User permission updated'
            else:
                return response.status_code, response.json()
        except Exception as e:
            return -1, str(e)
    
    def remote_from_from_project(self, ssh_url: str, user: str) -> Tuple[int, Optional[str]]:
        """
        Removes a user from a GitHub project.

        This function first extracts the username and repository name from the provided SSH URL. It then checks if the user exists on GitHub. If the user exists and has permissions on the specified repository, it attempts to remove the user from the repository. The function handles various HTTP status codes to provide meaningful feedback on the operation's outcome.

        Args:
            ssh_url (str): The SSH URL of the GitHub repository.
            user (str): The username of the GitHub user to remove from the project.

        Returns:
            Tuple[int, Optional[str]]: A tuple containing the HTTP status code and an optional error message.
        Raises:
            Exception: If an unexpected error occurs.
            Timeout: If the request times out.

        """
        try:
            username, repo_name = self.extract_user_repo_from_ssh(ssh_url)

            status_code, error_message = self.check_user_exists(user)
            if error_message:
                return status_code, error_message
            # Check if the user has permissions on the specified repository
            permissions_response = requests.get(
                f'https://api.github.com/repos/{username}/{repo_name}/collaborators/{user}/permission', headers=self.HEADERS, timeout=2)
            if permissions_response.status_code != 200:
                return permissions_response.status_code, 'Nothing to do - User does not have permissions on the repository.'

            # Remove the user from the repository
            remove_response = requests.delete(
                f'https://api.github.com/repos/{username}/{repo_name}/collaborators/{user}', headers=self.HEADERS, timeout=2)
            if remove_response.status_code == 204:
                return remove_response.status_code, 'User removed from the repository successfully'
            else:
                return remove_response.status_code, remove_response.json()
        except requests.exceptions.Timeout:
            return -1, "Request timed out"
        except Exception as e:
            return -1, str(e)
        
    def get_users_on_repo(self, ssh_url: str) -> set[str]:
        """
        Retrieves a set of GitHub usernames who are collaborators on a given repository.

        This function extracts the username and repository name from the provided SSH URL. It then makes a request to the GitHub API to fetch the list of collaborators on the specified repository. The function returns a set of GitHub usernames who have access to the repository.

        Args:
            ssh_url (str): The SSH URL of the GitHub repository.

        Returns:
            set[str]: A set of GitHub usernames who are collaborators on the repository.

        Raises:
            Exception: If an error occurs during the API request or while processing the response.
        """
        username, repo_name = self.extract_user_repo_from_ssh(ssh_url)

        # Get the list of collaborators on the repository
        try:
            print(f"Fetching collaborators for {username}/{repo_name}")
            print(f'Headers: {self.HEADERS}')
            collaborators_response = requests.get(
                f'https://api.github.com/repos/{username}/{repo_name}/collaborators',
                headers=self.HEADERS,
                timeout=10
            )
        except requests.exceptions.Timeout as e:
            raise TimeoutError(
                "The request to get collaborators timed out.") from e
        except requests.exceptions.ConnectionError as e:
            raise ConnectionError(
                "Failed to establish a connection to the GitHub API.") from e
        except requests.exceptions.RequestException as e:
            raise Exception(
                f"An error occurred while making the request: {e}") from e
        except Exception as e:
            raise Exception(
                f"Failed to fetch collaborators: {collaborators_response.json().get('message', 'Unknown error')}") from e

        if collaborators_response.status_code == 200:
            collaborators = {collaborator['login']
                            for collaborator in collaborators_response.json()}
            return collaborators
        elif collaborators_response.status_code == 404:
            raise FileNotFoundError("The repository was not found.")
        elif collaborators_response.status_code == 403:
            raise PermissionError("Access to the repository is forbidden.")
        else:
            raise Exception(
                f"Failed to fetch collaborators: {collaborators_response.json().get('message', 'Unknown error')}")
        
    def get_users_invited_repo(self, ssh_url: str) -> set[str]:
        """
        Retrieves a set of GitHub usernames who are invited collaborators on a given repository.

        This function extracts the username and repository name from the provided SSH URL. It then makes a request to the GitHub API to fetch the list of invited collaborators on the specified repository. The function returns a set of GitHub usernames who have been invited to collaborate on the repository.

        Args:
            ssh_url (str): The SSH URL of the GitHub repository.

        Returns:
            set[str]: A set of GitHub usernames who are invited collaborators on the repository.

        Raises:
            Exception: If an error occurs during the API request or while processing the response.
        """

        username, repo_name = self.extract_user_repo_from_ssh(ssh_url)
        print(f"Fetching invited collaborators for {username}/{repo_name}")

        try:
            invited_collaborators_response = requests.get(
                f'https://api.github.com/repos/{username}/{repo_name}/invitations',
                headers=self.HEADERS,
                timeout=10
            )
        except requests.exceptions.Timeout as e:
            raise TimeoutError(
                "The request to get invited collaborators timed out.") from e
        except requests.exceptions.ConnectionError as e:
            raise ConnectionError(
                "Failed to establish a connection to the GitHub API.") from e
        except requests.exceptions.RequestException as e:
            raise Exception(
                f"An error occurred while making the request: {e}") from e
        except Exception as e:
            raise Exception(
                f"Failed to fetch invited collaborators: {invited_collaborators_response.json().get('message', 'Unknown error')}") from e
        
        if invited_collaborators_response.status_code == 200:
            print(f"Invited collaborators response: {invited_collaborators_response.json()}")
            invited_collaborators = {invited_collaborators['invitee']['login']
                                    for invited_collaborators in invited_collaborators_response.json()}
            return invited_collaborators
        elif invited_collaborators_response.status_code == 404:
            raise FileNotFoundError("The repository was not found.")
        elif invited_collaborators_response.status_code == 403:
            raise PermissionError("Access to the repository is forbidden.")
        else:
            raise Exception(
                f"Failed to fetch invited collaborators: {invited_collaborators_response.json().get('message', 'Unknown error')}")
        

    def remove_all_users_from_repo(self, ssh_url: str) -> list[tuple[int, str]]:
        """
        Removes all collaborators from a given repository using the get_users_on_repo function to fetch the list of collaborators.

        Args:
            ssh_url (str): The SSH URL of the GitHub repository.

        Returns:
            list[tuple[int, str]]: A list of tuples, each containing the HTTP status code and a message indicating the success or failure of the operation.
        """
        try:
            collaborators = self.get_users_on_repo(ssh_url)
        except Exception as e:
            return -1, str(e)

        username, repo_name = self.extract_user_repo_from_ssh(ssh_url)

        result = []
        # Attempt to remove each collaborator
        for collaborator in collaborators:
            try:
                remove_response = requests.delete(
                    f'https://api.github.com/repos/{username}/{repo_name}/collaborators/{collaborator}',
                    headers=self.HEADERS,
                    timeout=2
                )
                if remove_response.status_code not in [204, 404]:
                    result.append((remove_response.status_code,
                                    f"Failed to remove {collaborator}"))
                result.append((remove_response.status_code,
                                f"{collaborator} removed successfully"))
            except Exception as e:
                result.append((-1, str(e)))

        return result
    
    # set difference, if already in repo instead of remove, change to hide

    def set_repo_users(self, ssh_url: str, desired_users: set[str]) -> list[tuple[int, str]]:
        """
        Sets the repository to only have the specified users. Removes users not in the desired list and adds users missing from the repository.

        Args:
            ssh_url (str): The SSH URL of the GitHub repository.
            desired_users (set[str]): A set of usernames that should have access to the repository.

        Returns:
            list[tuple[int, str]]: A list of tuples, each containing the HTTP status code and a message indicating the success or failure of each operation.
        """
        desired_users = set(desired_users)
        try:
            current_users = self.get_users_on_repo(ssh_url)
        except Exception as e:
            return [(-1, str(e))]

        username, repo_name = self.extract_user_repo_from_ssh(ssh_url)

        result = []

        # Remove users not in the desired list
        for user in current_users:
            if user not in desired_users:
                try:
                    remove_response = requests.delete(
                        f'https://api.github.com/repos/{username}/{repo_name}/collaborators/{user}',
                        headers=self.HEADERS,
                        timeout=2
                    )
                    if remove_response.status_code == 204:
                        result.append((204, f"{user} removed successfully"))
                    else:
                        result.append((remove_response.status_code,
                                    f"Failed to remove {user}"))
                except Exception as e:
                    result.append((-1, str(e)))

        # Add missing users
        for user in desired_users-current_users:
            if user not in current_users:
                try:
                    add_response = requests.put(
                        f'https://api.github.com/repos/{username}/{repo_name}/collaborators/{user}',
                        headers=self.HEADERS,
                        timeout=2
                    )
                    if add_response.status_code in [201, 204]:
                        result.append((add_response.status_code,
                                    f"{user} added successfully"))
                    else:
                        result.append((add_response.status_code,
                                    f"Failed to add {user}"))
                except Exception as e:
                    result.append((-1, str(e)))

        return result


def sheet():

    # path to the CSV file
    csv_file_path = 'rest.csv'
    log_file_path = 'output.txt'

    # Open the log file in append mode
    with open(log_file_path, 'a') as log_file:
        # Open the CSV file
        with open(csv_file_path, newline='') as csvfile:
            # Create a CSV reader object
            csv_reader = csv.reader(csvfile)
            repo_users_map: dict[str, list[str]] = {}
            next(csv_reader)  # Skip the header row
            for row in csv_reader:

                if len(row) < 2:  # Skip incomplete rows
                    continue
                username, repo_ssh_url = row[0], row[1]
                if repo_ssh_url not in repo_users_map:
                    repo_users_map[repo_ssh_url] = [username]
                else:
                    repo_users_map[repo_ssh_url].append(username)

            for repo_ssh_url, users in repo_users_map.items():
                print(f"Repo: {repo_ssh_url} has users: {users}")
                try:
                    automation = Automation(GITHUB_PAT)
                    result = automation.set_repo_users(repo_ssh_url, users)
                    for status, message in result:
                        log_file.write(f"{status}: {message}\n")
                except Exception as e:
                    log_file.write(
                        f"Failed to update repo: {repo_ssh_url} with error: {str(e)}\n")

def main():
    # Open the log file in append mode
    log_file_path = 'output.txt'
    with open(log_file_path, 'a') as log_file:
        usersmap = {
            'git@github.com:spark-tests/initial.git': ['mochiakku', 's-alad']
        }

        for repo_ssh_url, users in usersmap.items():
            print(f"Repo: {repo_ssh_url} has users: {users}")
            try:
                automation = Automation(GITHUB_PAT)
                result = automation.set_repo_users(repo_ssh_url, users)
                for status, message in result:
                    log_file.write(f"{status}: {message}\n")
            except Exception as e:
                log_file.write(
                    f"Failed to update repo: {repo_ssh_url} with error: {str(e)}\n")


if __name__ == "__main__":
    main()
