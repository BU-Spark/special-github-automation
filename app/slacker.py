import os
import time
import math
from typing import List
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from dotenv import load_dotenv
import log

class Slacker:
    def __init__(self, token: str):
        self.token = token
        self.client = WebClient(token=self.token)
        self.log = log.SparkLogger(name="Slacker", output=True, persist=True)

    def get_user_id(self, email: str) -> str:
        """
        Fetches the user ID associated with the given email address.
        
        Args: email (str): The email address of the user.
        Returns: str: The user ID if found, otherwise an empty string.
        Raises: SlackApiError: If the API call fails.
        """
        
        try:
            response = self.client.users_lookupByEmail(email=email)
            uid = response['user']['id']
            self.log.info(f"fetched slack uid {uid} for email '{email}'.")
            return uid
        except SlackApiError as e:
            self.log.error(f"failed to fetch slack uid for email '{email}': {e.response['error']}")
            raise e

    def create_channel(self, channel_name: str, is_private: bool = False) -> str:
        """
        Creates a Slack channel with the given name.
        
        Args: 
            channel_name (str): The name of the channel.
            is_private (bool, optional): Whether the channel is private. Defaults to False.
        Returns: str: The ID of the created channel if successful, otherwise an empty string.    
        Raises: SlackApiError: If the API call fails.
        """
        
        try:
            response = self.client.conversations_create(
                name=channel_name,
                is_private=is_private
            )
            channel_id = response['channel']['id']
            self.log.info(f"created channel '{channel_name}' with ID: {channel_id}")
            return channel_id
        except SlackApiError as e:
            if e.response['error'] == 'name_taken':
                self.log.warning(f"channel '{channel_name}' already exists.")
                existing_channel = self.get_channel_id(channel_name)
                return existing_channel
            else:
                self.log.error(f"failed to create channel '{channel_name}': {e.response['error']}")
                raise e

    def get_channel_id(self, channel_name: str) -> str:
        """
        Fetches the ID of an existing channel with the given name.
        
        Args: channel_name (str): The name of the channel.
        Returns: str: The ID of the channel if found, otherwise an empty string.
        Raises: SlackApiError: If the API call fails.
        """
        
        try:
            response = self.client.conversations_list(types="public_channel,private_channel", limit=1000)
            channel_id = next((c['id'] for c in response['channels'] if c['name'] == channel_name), "")
            if channel_id:
                self.log.info(f"fetched channel ID {channel_id} for '{channel_name}'.")
                return channel_id
            else:
                self.log.warning(f"channel '{channel_name}' not found.")
                raise SlackApiError(f"Channel '{channel_name}' not found.", response)
        except SlackApiError as e:
            self.log.error(f"failed to fetch channel ID for '{channel_name}': {e.response['error']}")
            raise e

    def get_channel_name(self, channel_id: str) -> str:
        """
        Fetches the name of an existing channel with the given ID.
        
        Args: channel_id (str): The ID of the channel.
        Returns: str: The name of the channel if found, otherwise an empty string.
        Raises: SlackApiError: If the API call fails.
        """
        
        try:
            response = self.client.conversations_info(channel=channel_id)
            channel_name = response['channel']['name']
            self.log.info(f"fetched channel name '{channel_name}' for ID: {channel_id}")
            return channel_name
        except SlackApiError as e:
            self.log.error(f"failed to fetch channel name for ID: {channel_id}: {e.response['error']}")
            raise e

    def invite_users_to_channel(self, channel_id: str, user_ids: List[str] | str, retries: int = 0):
        """
        Invites users to a Slack channel.
        
        Args:
            channel_id (str): The ID of the channel.
            user_ids (List[str] | str): A list of user IDs or a single user ID.
            retries (int, optional): The number of retries. Defaults to 0.
        Raises: SlackApiError: If the API call fails.
        """
        
        try:
            self.client.conversations_invite(
                channel=channel_id,
                users=user_ids 
            )
            self.log.info(f"invited users to channel ID {channel_id}.")
        except SlackApiError as e:
            if e.response['error'] == 'rate_limited' and retries < 5:
                backoff = int(e.response.headers.get('Retry-After', 1)) * math.pow(2, retries)
                self.log.warning(f"inviting users rate limited. retrying in {backoff} seconds.")
                time.sleep(backoff)
                self.invite_users_to_channel(channel_id, user_ids, retries + 1)
            else:
                self.log.error(f"failed to invite users to channel ID {channel_id}: {e.response['error']}")
                raise e

    def create_channels_and_add_users(self, channels_dict: dict, is_private: bool = False) -> list:
        """
        Creates multiple Slack channels and adds specified users to each channel.

        Args:
            channels_dict (dict): A dictionary where keys are channel names and values are lists of user emails.
            is_private (bool, optional): Whether the channels are private. Defaults to False.

        Returns:
            list: A list of dictionaries containing channel names and their corresponding IDs.
        Raises: SlackApiError: If the API call fails.
        """
        try:
            created_channels = []
            email_to_user_id = {
                email: self.get_user_id(email)
                for email in {email for users in channels_dict.values() for email in users}
            }
            self.log.info(f"email to user ID mapping: {email_to_user_id}")
            
            for channel_name, user_emails in channels_dict.items():
                channel_id = self.create_channel(channel_name, is_private)
                user_ids = [email_to_user_id[email] for email in user_emails if email in email_to_user_id]
                self.invite_users_to_channel(channel_id, user_ids)
                created_channels.append({'name': channel_name, 'id': channel_id})

            return created_channels
        
        except SlackApiError as e:
            self.log.error(f"failed to create channels and add users: {e.response['error']}")
            raise e
        except Exception as e:
            self.log.error(f"failed to create channels and add users: {e}")
            raise e

if __name__ == "__main__":
    load_dotenv()
    
    slacker = Slacker(token=os.getenv('SLACK_BOT_TOKEN') or "")
    """ channels_dict = {
        'channel1': ["x@bu.edu"],
        'channel2': ["y@bu.edu"],
        'channel3': ["z@bu.edu"]
    }
    created_channels = slacker.create_channels_and_add_users(channels_dict, is_private=False) """
    print(slacker.get_channel_name("C085LBA78GJ"))