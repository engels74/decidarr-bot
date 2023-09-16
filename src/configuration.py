from asyncio import Lock
from datetime import datetime
from discord.ext import commands, tasks
import aiofiles
import asyncio
import discord
import docker
import fcntl
import json
import os
import time
import logging

# Initialize logging
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# Define a function to retrieve environment variables as integers
def get_env_var_as_int(name, default=None):

# Retrieve configuration values from environment variables
CONTAINER_NAME = os.getenv('DOCKER_CONTAINER_NAME')
DOCKER_SOCKET_PROXY_URL = os.getenv('DOCKER_SOCKET_PROXY_URL', 'tcp://docker-socket-proxy:2375')
MESSAGE_HISTORY_LIMIT = get_env_var_as_int('MESSAGE_HISTORY_LIMIT', 25)  
TOKEN = os.getenv('DISCORD_TOKEN')
TRUSTED_ROLE_ID = get_env_var_as_int('TRUSTED_ROLE_ID')
VOTE_CHANNEL_ID = get_env_var_as_int('VOTE_CHANNEL_ID')
VOTE_TITLE = os.getenv('VOTE_TITLE', 'Vote to restart the Docker container!')
VOTES_NEEDED = get_env_var_as_int('VOTES_NEEDED', 3)
VOTES_PATH = os.getenv('VOTES_DATA_PATH', 'votes_data/votes.json')