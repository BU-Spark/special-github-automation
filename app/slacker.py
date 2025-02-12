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
        self.channel_cache = {}

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
            self.channel_cache[channel_name] = channel_id
            return channel_id
        except SlackApiError as e:
            print(e)
            if e.response['error'] == 'name_taken':
                self.log.warning(f"channel '{channel_name}' already exists.")
                existing_channel = self.get_channel_id(channel_name)
                return existing_channel
            else:
                self.log.error(f"failed to create channel '{channel_name}': {e.response['error']}")
                raise e

    def get_channel_id(self, channel_name: str) -> str:
        """
        Fetches the ID of an existing channel with the given name using pagination.
        
        Args:
            channel_name (str): The name of the channel.
        
        Returns:
            str: The ID of the channel if found.
        
        Raises:
            SlackApiError: If the API call fails or the channel is not found.
        """
        
        print(f"Fetching channel ID for '{channel_name}'...")
        
        if channel_name in self.channel_cache:
            self.log.info(f"Found channel ID {self.channel_cache[channel_name]} in cache for '{channel_name}'.")
            return self.channel_cache[channel_name]
        else:
            self.log.info(f"Channel ID for '{channel_name}' not found in cache. Fetching from API...")
        
        try:
            cursor = None
            total = 0
            while True:
                time.sleep(1)
                response = self.client.conversations_list(
                    types="public_channel,private_channel,mpim,im",
                    limit=1000, 
                    cursor=cursor,
                    exclude_archived=True
                )
                total += len(response.get("channels", []))
                for channel in response.get("channels", []):
                    if channel.get("name") == channel_name:
                        self.log.info(f"Fetched channel ID {channel['id']} for '{channel_name}'.")
                        return channel["id"]
                    else:
                        potential_cache_name = channel.get("name")
                        if potential_cache_name not in self.channel_cache:
                            self.channel_cache[potential_cache_name] = channel["id"]

                cursor = response.get("response_metadata", {}).get("next_cursor")
                if not cursor: break
            
            print(f"Total channels fetched: {total}")
            self.log.warning(f"Channel '{channel_name}' not found.")
            raise SlackApiError(f"Channel '{channel_name}' not found.", response={})
        except SlackApiError as e:
            self.log.error(f"Failed to fetch channel ID for '{channel_name}': {e}")
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

    def change_channel_name(self, channel_id: str, new_name: str):
        """
        Changes the name of a Slack channel.
        
        Args:
            channel_id (str): The ID of the channel.
            new_name (str): The new name for the channel.
        Raises: SlackApiError: If the API call fails.
        """
        
        try:
            self.client.conversations_rename(
                channel=channel_id,
                name=new_name
            )
            self.log.info(f"changed channel name for ID {channel_id} to '{new_name}'.")
        except SlackApiError as e:
            self.log.error(f"failed to change channel name for ID {channel_id}: {e.response['error']}")
            raise e

    def convert_channel_to_private(self, channel_id: str):
        """
        Converts a Slack channel to a private channel.
        
        Args: channel_id (str): The ID of the channel.
        Raises: SlackApiError: If the API call fails.
        """
        
        try:
            self.client.admin_conversations_convertToPrivate(
                channel_id=channel_id,
            )
        except SlackApiError as e:
            self.log.error(f"failed to convert channel ID {channel_id} to private: {e.response['error']}")
            raise e

if __name__ == "__main__":
    load_dotenv()
    slacker = Slacker(token=os.getenv('SLACK_BOT_TOKEN') or "")
    
    chann_tags = [
        "i-sp25-ds519-488-d4-constituent-app",
        #"i-sp25-ds519-488-social-justice-app",
        "i-sp25-ds519-488-bva",
        "i-sp25-ds519-488-community-service-hours",
        "i-sp25-ds519-488-auto-mech-challenge",
        "i-sp25-ds519-488-mass-courts-v3",
        #"i-sp25-ds519-488-cmovf",
        #"i-sp25-ds519-488-academico-ai",
        #"i-sp25-ds519-488-mola"
    ]
    
    underscore_chan_tags = [
        #"i-sp25-ds519_488-d4-constituent-app",
        "i-sp25-ds519_488-social-justice-app",
        #"i-sp25-ds519_488-bva",
        #"i-sp25-ds519_488-community-service-hours",
        #"i-sp25-ds519_488-auto-mech-challenge",
        #"i-sp25-ds519_488-mass-courts-v3",
        "i-sp25-ds519_488-cmovf",
        "i-sp25-ds519_488-academico-ai",
        "i-sp25-ds519_488-mola"
    ]
    
    #created slack channel C08C1NZK076 for project social-justice-app.
    #created slack channel C08BZD34X2P for project social-justice-app.
    
    #for tag in underscore_chan_tags:  print(slacker.get_channel_id(tag))
    
    #print(slacker.create_channel("i-sp25-ds519_488-social-justice-app", is_private=True))
    
    #print(slacker.get_channel_name("C08BZD34X2P"))
    #print(slacker.get_channel_name("C08C1NZK076"))
    #print(slacker.get_channel_id("i-sp25-ds519-488-social-justice-app"))
    #print(slacker.get_channel_id("i-sp25-ds519_488-social-justice-app"))
    
    #print(slacker.change_channel_name("C08BZD34X2P", "renamed-social-justice-app"))
    
    slacker.convert_channel_to_private(slacker.get_channel_id("i-sp25-ds549-wlfc-archive"))