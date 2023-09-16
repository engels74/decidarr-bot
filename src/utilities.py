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


# Define a function to retrieve environment variables as integers
def get_env_var_as_int(name, default=None):

# Function to ensure the votes file name is consistent
def check_votes_file_consistency():
    filename = os.path.basename(VOTES_PATH)  
    if filename != "votes.json":
        raise ValueError(f"[ERROR] Inconsistent file reference in VOTE_PATH. Expected 'votes.json', but got {filename}.")

# Function to parse a string into time in seconds
def parse_time(time_str):
    unit = time_str[-1]
    value = int(time_str[:-1])

# Initializes the votes data file
async def initialize_votes_file():
    global last_restart_time

# Define a custom asynchronous file lock class for thread safety
class AsyncVoteFileLock:
    def __init__(self, path):  
        self.path = path
        self.lock = Lock()

    async def __aenter__(self):
        await self.lock.acquire()

    async def __aexit__(self, exc_type, exc, tb):
        await self.file.close()
        self.lock.release()

# Asynchronous function to get the current vote count from the file
async def get_votes():
    async with AsyncVoteFileLock(VOTES_PATH) as f:
        content = await f.read()
        data = json.loads(content)
        return data['votes_count']

# Asynchronous function to add a vote and handle logic related to voting
async def add_vote(user_id):
    global last_restart_time  

# Asynchronous function to reset the vote count
async def reset_votes():
    async with AsyncVoteFileLock(VOTES_PATH) as f:
        content = await f.read()
        data = json.loads(content)
        data['votes_count'] = 0
        await f.seek(0)
        await f.write(json.dumps(data, indent=4))
        logger.info("[INFO] Votes have been reset due to the timer.")

# Function to restart the Docker container
def restart_container():
    container = client.containers.get(CONTAINER_NAME)
    logger.info("[INFO] Restarting the container.")
    container.restart()

    async def handle_container_restart(self):
        # Introduce a slight delay before the restart to ensure the response is sent
        await asyncio.sleep(1)
        restart_container()
        await reset_votes()

# Function to check if the Docker socket proxy connection is successful
def check_docker_connection():
    try:
        containers = client.containers.list()  
        logger.info("[INFO] Successfully connected to Docker socket proxy.")
        return True
    except Exception as e:
        logger.info(f"[ERROR] Failed to connect to Docker socket proxy. Error: {e}")
        return False

# Event handler for when the bot is ready and has started up
@bot.event
async def on_ready():
    await initialize_votes_file()
    global vote_post_msg_id

# Task loop to clean up old messages from the channel at regular intervals
@tasks.loop(seconds=CLEANUP_INTERVAL)
async def cleanup_messages():
    logger.info("[INFO] Running cleanup messages task.")
    channel = bot.get_channel(VOTE_CHANNEL_ID)
    if not channel:
        return

# Command handler for users to manually vote
@bot.command()
async def vote(ctx):
    if any(role.id == TRUSTED_ROLE_ID for role in ctx.author.roles):
        embed = await add_vote(ctx.author.id)
        await ctx.send(embed=embed)
    else:
        await ctx.send("You don't have permission to vote.")

# Task loop to update the main voting post message at regular intervals
@tasks.loop(seconds=parse_time(os.getenv('UPDATE_POST_INTERVAL', '15s')))
async def update_vote_post():
    logger.info("[INFO] Updating the Discord post.")
    global vote_post_msg_id  

# Task loop to reset the vote count at regular intervals
@tasks.loop(seconds=parse_time(os.getenv('RESET_VOTE_INTERVAL', '1h')))
async def reset_vote_timer():
    await reset_votes()