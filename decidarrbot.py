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

# Initialize logging
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# Define a function to retrieve environment variables as integers
def get_env_var_as_int(name, default=None):

    value = os.getenv(name, default)
    if value is None:
        raise ValueError(f"[ERROR] Environment variable {name} is not set and no default value provided.")
    try:
        return int(value)
    except ValueError:
        raise ValueError(f"[ERROR] Environment variable {name} has an invalid value: {value}. It must be an integer or not set if a default is provided.")

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

# Function to ensure the votes file name is consistent
def check_votes_file_consistency():
    filename = os.path.basename(VOTES_PATH)  
    if filename != "votes.json":
        raise ValueError(f"[ERROR] Inconsistent file reference in VOTE_PATH. Expected 'votes.json', but got {filename}.")

check_votes_file_consistency()

# Function to parse a string into time in seconds
def parse_time(time_str):
    unit = time_str[-1]
    value = int(time_str[:-1])

    if unit == 's':
        return value
    elif unit == 'm':
        return value * 60
    elif unit == 'h':
        return value * 3600
    else:
        logger.info("[INFO] Reading from the existing votes.json file.")
        raise ValueError("[ERROR] Invalid time format")

# Parse various time-related environment variables
USER_VOTE_COOLDOWN = parse_time(os.getenv('USER_VOTE_COOLDOWN', '1m'))  
RESTART_COOLDOWN = parse_time(os.getenv('RESTART_COOLDOWN', '1h'))  
CLEANUP_INTERVAL = parse_time(os.getenv('CLEANUP_INTERVAL', '30m'))  

last_vote_times = {}  
last_restart_time = None  

# Initializes the votes data file
async def initialize_votes_file():
    global last_restart_time

    directory = os.path.dirname(VOTES_PATH)
    if not os.path.exists(directory):
        os.makedirs(directory)

    if not os.path.exists(VOTES_PATH):
        async with AsyncVoteFileLock(VOTES_PATH) as f:
            data = {
                'votes_count': 0,
                'history': [],
                'last_restart_timestamp': None
            }
            await f.write(json.dumps(data, indent=4))
            logger.info("[INFO] The votes.json file has been initialized.")
    else:
        async with AsyncVoteFileLock(VOTES_PATH) as f:
            content = await f.read()
            data = json.loads(content)
            if data.get('last_restart_timestamp'):
                last_restart_time = datetime.fromisoformat(data['last_restart_timestamp'])
        logger.info("[INFO] The votes.json file exists and has been read.")

# Set up Discord Intents (used to specify which events the bot should receive)
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='?', intents=intents)

# Initialize the Docker client to communicate with the Docker daemon
client = docker.DockerClient(base_url=DOCKER_SOCKET_PROXY_URL)

vote_post_msg_id = None

# Define a custom asynchronous file lock class for thread safety
class AsyncVoteFileLock:
    def __init__(self, path):  
        self.path = path
        self.lock = Lock()

    async def __aenter__(self):
        await self.lock.acquire()

        # If the file doesn't exist, create it
        if not os.path.exists(self.path):
            async with aiofiles.open(self.path, 'w') as f:
                pass

        self.file = await aiofiles.open(self.path, 'r+')
        return self.file

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

    current_time = datetime.now()
    last_vote_time = last_vote_times.get(user_id)

    if last_vote_time and (current_time - last_vote_time).seconds < USER_VOTE_COOLDOWN:
        embed = discord.Embed(title="Vote Feedback", description=f"You can vote again after {USER_VOTE_COOLDOWN - (current_time - last_vote_time).seconds} seconds.", color=0xff0000)  
        return embed

    if last_restart_time and (current_time - last_restart_time).seconds < RESTART_COOLDOWN:
        embed = discord.Embed(title="Vote Feedback", description=f"The container was recently restarted. Please wait {RESTART_COOLDOWN - (current_time - last_restart_time).seconds} seconds before voting again.", color=0xff0000)  
        return embed

    async with AsyncVoteFileLock(VOTES_PATH) as f:
        content = await f.read()
        data = json.loads(content)

        data['votes_count'] += 1
        data['history'].append({"user_id": user_id, "timestamp": datetime.now().isoformat()})

        if data['votes_count'] >= VOTES_NEEDED:
            embed = discord.Embed(title="Vote Feedback", description="Container will be restarted due to vote threshold!", color=0x00ff00)
            logger.info("[INFO] Votes have been reset due to reaching the threshold.")
        else:
            embed = discord.Embed(title="Vote Feedback", description=f"Thank you for voting! Current Votes: {data['votes_count']}/{VOTES_NEEDED}", color=0x00ff00)

        await f.seek(0)
        await f.write(json.dumps(data, indent=4))
        await f.close()

        logger.info(f"[INFO] User {user_id} has voted. Current votes count: {data['votes_count']}.")
        return embed

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

# Define a custom button for users to vote to restart the container
class VoteButton(discord.ui.Button['VoteView']):  
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.success, label="Vote To Restart", custom_id="vote_btn")

    async def callback(self, interaction: discord.Interaction):
        if any(role.id == TRUSTED_ROLE_ID for role in interaction.user.roles):
            embed = await add_vote(interaction.user.id)
            
            # Immediate interaction response
            await interaction.response.send_message(embed=embed, ephemeral=True)

            # If the vote threshold has been reached, restart the container asynchronously
            current_votes = await get_votes()
            if current_votes >= VOTES_NEEDED:
                asyncio.create_task(self.handle_container_restart())
        else:
            await interaction.response.send_message("You don't have permission to vote.", ephemeral=True)

    async def handle_container_restart(self):
        # Introduce a slight delay before the restart to ensure the response is sent
        await asyncio.sleep(1)
        restart_container()
        await reset_votes()

# Define a custom view to display the vote button
class VoteView(discord.ui.View):  
    def __init__(self):
        super().__init__()
        self.add_item(VoteButton())

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

    logger.info(f'[INFO] Bot is logged in as {bot.user}')
    check_docker_connection()  

    channel = bot.get_channel(VOTE_CHANNEL_ID)
    async for message in channel.history(limit=50):
        if message.author == bot.user and "Current Votes:" in message.content:
            vote_post_msg_id = message.id
            break

    update_vote_post.start()  
    reset_vote_timer.start()  
    cleanup_messages.start()  

    await bot.wait_until_ready()

# Task loop to clean up old messages from the channel at regular intervals
@tasks.loop(seconds=CLEANUP_INTERVAL)
async def cleanup_messages():
    logger.info("[INFO] Running cleanup messages task.")
    channel = bot.get_channel(VOTE_CHANNEL_ID)
    if not channel:
        return

    async for message in channel.history(limit=MESSAGE_HISTORY_LIMIT):
        if message.id != vote_post_msg_id:  
            await message.delete()

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

    channel = bot.get_channel(VOTE_CHANNEL_ID)
    if not channel:
        return

    current_votes = await get_votes()

    if last_restart_time:
        restart_timestamp = int(last_restart_time.timestamp())
        restart_info = f"\n\nLast restarted at: <t:{restart_timestamp}:R>"
    else:
        restart_info = ""

    embed = discord.Embed(
        title=VOTE_TITLE,
        description=f"Current Votes: {current_votes}/{VOTES_NEEDED}\n\nVote by pressing the button below or typing `?vote`.{restart_info}"
    )
    view = VoteView()  

    if vote_post_msg_id:
        try:

            message = await channel.fetch_message(vote_post_msg_id)
            await message.edit(embed=embed, view=VoteView())
        except discord.NotFound:

            new_message = await channel.send(embed=embed, view=view)
            vote_post_msg_id = new_message.id  
        except discord.errors.HTTPException as e:
            if e.code == 429:  
                logger.info("[INFO] Rate limited by Discord, delaying next post update.")
                await asyncio.sleep(e.retry_after)  
            else:
                logger.info(f"[ERROR] Encountered HTTPException: {e}")
        except Exception as e:  
            logger.info(f"[ERROR] An unexpected error occurred: {e}")

    else:

        message = await channel.send(embed=embed, view=view)
        vote_post_msg_id = message.id

# Task loop to reset the vote count at regular intervals
@tasks.loop(seconds=parse_time(os.getenv('RESET_VOTE_INTERVAL', '1h')))
async def reset_vote_timer():
    await reset_votes()

# Main execution point of the script
if __name__ == '__main__':
    bot.run(TOKEN)
