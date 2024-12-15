# =========================================== imports =============================================

import json
from typing import Literal, Optional
import requests
import csv
import os

# ============================================= Github ============================================

class Github:
    GITHUB_PAT = None
    HEADERS = None
    ORG_NAME = None
    perms = Literal['pull', 'triage', 'push', 'maintain', 'admin']
    
    def __init__(self, GITHUB_PAT: str, ORG_NAME: str):
        self.GITHUB_PAT = GITHUB_PAT
        self.ORG_NAME = ORG_NAME
        self.HEADERS = {
            'Accept': 'application/vnd.github+json',
            'Authorization': f'Bearer {GITHUB_PAT}',
            'X-GitHub-Api-Version': '2022-11-28'
        }
        print(f"Github initialized with PAT: {GITHUB_PAT} and {ORG_NAME}")
        
    def extract_user_repo_from_ssh_url(self, ssh_url: str) -> tuple[str, str]:
        """
        Extracts the username and repository name from a given SSH URL.

        Args: ssh_url (str): The SSH URL of the GitHub repository.
        Returns: Tuple[str, str]: A tuple containing the username and repository name.
        Raises: ValueError: If the SSH URL does not start with "git@github.com" or is missing required parts.
        """

        if not ssh_url.startswith("git@github.com:"):
            raise ValueError("Invalid SSH URL format")
        try:
            ssh_url_parts = ssh_url.split(':')[-1].split('/')
            username = ssh_url_parts[0]
            repo_name = ssh_url_parts[1].split('.')[0]
            return username, repo_name
        except Exception as e:
            raise ValueError("Invalid SSH URL format")
        
    def check_user_exists(self, user: str) -> bool:
        """
        Checks if a GitHub user exists.

        Args: user (str): The username of the GitHub user to check.
        Returns: bool: True if the user exists, False otherwise.
        """

        response = requests.get(
            f'https://api.github.com/users/{user}', headers=self.HEADERS, timeout=2)
        if response.status_code == 200: return True
        else: return False
    
    def check_user_is_collaborator(self, repo_url: str, user: str) -> bool:
        """
        Checks if a GitHub user is a collaborator on a given repository.

        Args: 
            repo_url (str): The URL of the GitHub repository.
            user (str): The username of the GitHub user.
        Returns: bool: True if the user is a collaborator, False otherwise.
        """
        
        ssh_url = repo_url.replace("https://github.com/", "git@github.com:")
        username, repo_name = self.extract_user_repo_from_ssh_url(ssh_url)
        
        try:
            response = requests.get(
                f'https://api.github.com/repos/{username}/{repo_name}/collaborators/{user}',
                headers=self.HEADERS,
                timeout=2
            )
            
            if response.status_code == 204: return True
            else: return False
        except Exception as e:
            raise Exception(f"Failed to check if user is a collaborator: {str(e)}")
    
    def add_user_to_repo(self, repo_url: str, user: str, permission: perms) -> tuple[int, str]:
        """
        Adds a GitHub user to a repository with the specified permission level.

        Args: 
            repo_url (str): The URL of the GitHub repository.
            user (str): The username of the GitHub user.
            permission ("pull" | "triage" | "push" | "maintain" | "admin"): The permission level for the user.
        Returns: Tuple[int, str]: A tuple containing the status code and message.
        """
        
        ssh_url = repo_url.replace("https://github.com/", "git@github.com:")
        username, repo_name = self.extract_user_repo_from_ssh_url(ssh_url)
        exists = self.check_user_exists(user)
        
        if not exists: return 404, f"User {user} does not exist"
        
        try:
            response = requests.put(
                f'https://api.github.com/repos/{username}/{repo_name}/collaborators/{user}',
                headers=self.HEADERS,
                json={'permission': permission},
                timeout=2
            )
            
            if response.status_code == 201: return 201, f"Successfully added {user} to the repository with {permission} permission"
            else: return response.status_code, response.json()
        except Exception as e:
            return 500, str(e)
    
    def get_users_on_repo(self, repo_url: str) -> set[str]:
        """
        Retrieves a set of GitHub usernames who are collaborators on a given repository.

        Args: repo_url (str): The URL of the GitHub repository.
        Returns: set[str]: A set of GitHub usernames who are collaborators on the repository.
        Raises: Exception: If an error occurs during the API request or while processing the response.
        """
        
        ssh_url = repo_url.replace("https://github.com/", "git@github.com:")
        username, repo_name = self.extract_user_repo_from_ssh_url(ssh_url)

        try:
            collaborators_response = requests.get(
                f'https://api.github.com/repos/{username}/{repo_name}/collaborators',
                headers=self.HEADERS,
                timeout=10
            )
        except Exception as e:
            raise Exception(f"Failed to fetch collaborators: {str(e)}")

        if collaborators_response.status_code == 200:
            return {collaborator['login'] for collaborator in collaborators_response.json()}
        elif collaborators_response.status_code == 404:
            raise Exception("The repository was not found.")
        elif collaborators_response.status_code == 403:
            raise Exception("Access to the repository is forbidden.")
        else:
            raise Exception(f"Failed to fetch collaborators: {collaborators_response.json().get('message', 'Unknown error')}")
    
    def get_users_invited_on_repo(self, repo_url: str, check_expired: bool = False ) -> set[str]:
        """
        Retrieves a set of GitHub usernames who are invited to collaborate on a given repository.

        Args:
            repo_url (str): The URL of the GitHub repository.
            check_expired (bool): If True, only return the usernames of users with expired invitations.
        Returns: set[str]: A set of GitHub usernames who are invited to collaborate on the repository.
        Raises: Exception: If an error occurs during the API request or while processing the response.
        """
        
        ssh_url = repo_url.replace("https://github.com/", "git@github.com:")
        username, repo_name = self.extract_user_repo_from_ssh_url(ssh_url)
        
        try:
            invitations_response = requests.get(
                f'https://api.github.com/repos/{username}/{repo_name}/invitations',
                headers=self.HEADERS,
                timeout=10
            )
        except Exception as e:
            raise Exception(f"Failed to fetch invitations: {str(e)}")
        
        if invitations_response.status_code == 200:
            if check_expired:
                return {invited_collaborators['invitee']['login'] if invited_collaborators["expired"] else None
                                        for invited_collaborators in invitations_response.json()} - {None}
            else:
                return {invitation['invitee']['login'] for invitation in invitations_response.json()}
        elif invitations_response.status_code == 404:
            raise Exception("The repository was not found.")
        elif invitations_response.status_code == 403:
            raise Exception("Access to the repository is forbidden.")
        else:
            raise Exception(f"Failed to fetch invitations: {invitations_response.json().get('message', 'Unknown error')}")
        
    def revoke_user_invitation_on_repo(self, repo_url: str, user: str) -> tuple[int, str]:
        """
        Revokes an invitation to collaborate on a GitHub repository.

        Args: 
            repo_url (str): The URL of the GitHub repository.
            user (str): The username of the GitHub user.
        Returns: Tuple[int, str]: A tuple containing the status code and message.
        """
        
        ssh_url = repo_url.replace("https://github.com/", "git@github.com:")
        username, repo_name = self.extract_user_repo_from_ssh_url(ssh_url)
        
        try:
            invitations_response = requests.get(
                f'https://api.github.com/repos/{username}/{repo_name}/invitations',
                headers=self.HEADERS,
                timeout=10
            )
            
            if invitations_response.status_code != 200:
                return invitations_response.status_code, 'Failed to fetch invited collaborators'
            
            invitation = next((inv for inv in invitations_response.json() if inv['invitee']['login'] == user), None)
            if invitation:
                response = requests.delete(
                    f'https://api.github.com/repos/{username}/{repo_name}/invitations/{invitation["id"]}',
                    headers=self.HEADERS,
                    timeout=2
                )
                if response.status_code == 204:
                    return 204, f"Successfully revoked invitation for {user}"
                else:
                    return response.status_code, response.json()
            else:
                return invitations_response.status_code, invitations_response.json()
        except Exception as e:
            return 500, str(e)        
        
    def reinvite_expired_users_on_repo(self, repo_url: str) -> list[tuple[int, str]]:
        """
        Re-invites users who have expired invitations on a GitHub repository.
        
        Args: repo_url (str): The HTTPS URL of the GitHub repository.
        Returns: list[tuple[int, str]]: A list of tuples containing the status code and message.
        """
        
        results = []
        try:
            expired_users = self.get_users_invited_on_repo(repo_url, check_expired=True)
            print(f"Expired users: {expired_users}")
            for user in expired_users:
                result = []
                status, msg = self.revoke_user_invitation_on_repo(repo_url, user)
                status, msg = self.add_user_to_repo(repo_url, user, "push")
                result.append((status, msg))
            return results
        except Exception as e:
            return [(500, str(e))]             
                                                
    def change_user_permission_on_repo(self, repo_url: str, user: str, permission: perms) -> tuple[int, str]:
        """
        Changes the permission level of a user on a GitHub repository.
        
        Args: 
            repo_url (str): The HTTPS URL of the GitHub repository.
            user (str): The username of the GitHub user.
            permission ("pull" | "triage" | "push" | "maintain" | "admin"): The new permission level for the user.
        Returns: Tuple[int, str]: A tuple containing the status code and message.
        """
        
        try:
            ssh_url = repo_url.replace("https://github.com/", "git@github.com:")
            username, repo_name = self.extract_user_repo_from_ssh_url(ssh_url)
            exists = self.check_user_exists(user)
            
            if not exists: return 404, f"User {user} does not exist"

            # Check if the user has permissions on the specified repository
            collaborator_response = requests.get(
                f'https://api.github.com/repos/{username}/{repo_name}/collaborators/{user}',
                headers=self.HEADERS
            )
            
            print(f"collaborator_response: {collaborator_response.status_code} for {user} on {repo_name}")
            
            if collaborator_response.status_code == 204:
                # Change the user's permission level
                change_permission_response = requests.put(
                    f'https://api.github.com/repos/{username}/{repo_name}/collaborators/{user}',
                    headers=self.HEADERS,
                    json={'permission': permission},
                    timeout=2
                )
                
                if change_permission_response.status_code == 200 or change_permission_response.status_code == 204:
                    return change_permission_response.status_code, f"Successfully changed {user}'s permission to {permission}"
                else:
                    return change_permission_response.status_code, change_permission_response.json()
                
            else:
                invitations_response = requests.get(
                    f'https://api.github.com/repos/{username}/{repo_name}/invitations',
                    headers=self.HEADERS
                )

                invitations = invitations_response.json()
                invitation = next((inv for inv in invitations if inv['invitee']['login'] == user), None)

                if invitation:
                    # Update the invitation if exists
                    update_invitation_response = requests.patch(
                        f'https://api.github.com/repos/{username}/{repo_name}/invitations/{invitation["id"]}',
                        headers=self.HEADERS,
                        json={'permissions': permission}
                    )
                    if update_invitation_response.status_code == 200:
                        return 200, f"Successfully updated {user}'s invitation to {permission}"
                    else:
                        return update_invitation_response.status_code, update_invitation_response.json()
                else:
                    return collaborator_response.status_code, f'User {user} is not a collaborator or invited on the repository'

        except Exception as e:
            return 500, str(e)

    def change_all_user_permission_on_repo(self, repo_url: str, permission: perms) -> list[tuple[int, str]]:
        """
        Changes the permission level of all users on a GitHub repository.
        
        Args: 
            repo_url (str): The HTTPS URL of the GitHub repository.
            permission ("pull" | "triage" | "push" | "maintain" | "admin"): The new permission level for the users.
        Returns: Tuple[int, str]: A tuple containing the status code and message.
        """
        
        results = []
        try:
            ssh_url = repo_url.replace("https://github.com/", "git@github.com:")
            users = self.get_users_on_repo(repo_url)
            invited_users = self.get_users_invited_on_repo(repo_url)
            
            for user in users.union(invited_users):
                status, msg = self.change_user_permission_on_repo(ssh_url, user, permission)
                results.append((status, msg))
            return results
        except Exception as e:
            return [(500, str(e))]

    def get_all_repos(self) -> list[str]:
        """
        Retrieves a list of all repositories in the organization.
        
        Returns: list[str]: A list of all repositories in the organization.
        """
        
        try:
            response = requests.get(
                f'https://api.github.com/orgs/{self.ORG_NAME}/repos',
                headers=self.HEADERS,
                timeout=10
            )
            #print(response.json())
            if response.status_code == 200:
                return [(repo['name'], repo['ssh_url']) for repo in response.json()]
            else:
                return []
        except Exception as e:
            return []

if __name__ == "__main__":
    #github = Github(GITHUB_PAT, "spark-tests")
    #print(github.change_user_permission_on_repo("https://github.com/spark-tests/initial", "mochiakku", "push"))
    #print(github.change_all_user_permission_on_repo("https://github.com/spark-tests/initial", "push"))
    #print(github.get_all_repos())
    print()