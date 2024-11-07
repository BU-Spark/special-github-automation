import os
import time
import math
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from dotenv import load_dotenv

load_dotenv()

class Slacker:
    def __init__(self, token: str = None):
        self.token = token
        if not self.token: raise ValueError("NO TOKEN PROVIDED")
        self.client = WebClient(token=self.token)

    def get_user_id(self, email: str) -> str:
        try:
            response = self.client.users_lookupByEmail(email=email)
            user_id = response['user']['id']
            print(f"Found user '{email}' with ID: {user_id}")
            return user_id
        except SlackApiError as e:
            if e.response['error'] == 'users_not_found':
                print(f"User with email '{email}' not found.")
            else:
                print(f"Error fetching user '{email}': {e.response['error']}")
            return None

    def create_channel(self, channel_name: str, is_private: bool = False) -> str:
        try:
            response = self.client.conversations_create(
                name=channel_name,
                is_private=is_private
            )
            channel_id = response['channel']['id']
            print(f"Channel '{channel_name}' created with ID: {channel_id}")
            return channel_id
        except SlackApiError as e:
            if e.response['error'] == 'name_taken':
                print(f"Channel '{channel_name}' already exists.")
                existing_channel = self.get_channel_id(channel_name)
                return existing_channel
            else:
                print(f"Failed to create channel '{channel_name}': {e.response['error']}")
                return None

    def get_channel_id(self, channel_name: str) -> str:
        try:
            response = self.client.conversations_list(types="public_channel,private_channel", limit=1000)
            channels = response['channels']
            for channel in channels:
                if channel['name'] == channel_name:
                    print(f"Found existing channel '{channel_name}' with ID: {channel['id']}")
                    return channel['id']
            print(f"Channel '{channel_name}' not found.")
            return None
        except SlackApiError as e:
            print(f"Error fetching channels: {e.response['error']}")
            return None

    def invite_users_to_channel(self, channel_id: str, user_ids: list, retry_count: int = 0):
        MAX_RETRIES = 5
        try:
            response = self.client.conversations_invite(
                channel=channel_id,
                users=user_ids  # Can be a list or comma-separated string
            )
        except SlackApiError as e:
            if e.response['error'] == 'already_in_channel':
                print(f"Some users are already in the channel ID {channel_id}.")
            elif e.response['error'] == 'user_not_found':
                print("One or more users not found.")
            elif e.response['error'] == 'rate_limited' and retry_count < MAX_RETRIES:
                retry_after = int(e.response.headers.get('Retry-After', 1))
                backoff_time = retry_after * math.pow(2, retry_count)
                print(f"Rate limited. Retrying after {backoff_time} seconds.")
                time.sleep(backoff_time)
                self.invite_users_to_channel(channel_id, user_ids, retry_count + 1)
            else:
                print(f"Failed to invite users to channel ID {channel_id}: {e.response['error']}")

    def create_channels_and_add_users(self, channels_dict: dict, is_private: bool = False) -> list:
        """
        Creates multiple Slack channels and adds specified users to each channel.

        Args:
            channels_dict (dict): A dictionary where keys are channel names and values are lists of user emails.
            is_private (bool, optional): Whether the channels are private. Defaults to False.

        Returns:
            list: A list of dictionaries containing channel names and their corresponding IDs.
        """
        created_channels = []
        email_to_user_id = {}

        # Extract unique emails to minimize API calls
        unique_emails = set(email for users in channels_dict.values() for email in users)
        print("Mapping emails to user IDs...")
        for email in unique_emails:
            user_id = self.get_user_id(email)
            if user_id:
                email_to_user_id[email] = user_id

        print("\nCreating channels and inviting users...")
        # Create channels and invite users
        for channel_name, user_emails in channels_dict.items():
            print(f"\nProcessing channel: {channel_name}")
            channel_id = self.create_channel(channel_name, is_private)
            if channel_id:
                # Retrieve user IDs for the current channel
                user_ids = [email_to_user_id[email] for email in user_emails if email in email_to_user_id]
                if user_ids:
                    self.invite_users_to_channel(channel_id, user_ids)
                else:
                    print(f"No valid users to invite for channel '{channel_name}'.")
                created_channels.append({'name': channel_name, 'id': channel_id})

        return created_channels


if __name__ == "__main__":
    slacker =   Slacker(token=os.getenv('SLACK_BOT_TOKEN'))
    channels_dict = {
        'x4': ["x@bu.edu"],
    }
    created_channels = slacker.create_channels_and_add_users(channels_dict, is_private=False)