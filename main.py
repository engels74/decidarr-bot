from src.configuration import *
from src.utilities import *
from src.bot_logic import *
from src.docker_logic import *

    value = os.getenv(name, default)
    if value is None:
        raise ValueError(f"[ERROR] Environment variable {name} is not set and no default value provided.")
    try:
        return int(value)
    except ValueError:
        raise ValueError(f"[ERROR] Environment variable {name} has an invalid value: {value}. It must be an integer or not set if a default is provided.")

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

vote_post_msg_id = None

        # If the file doesn't exist, create it
        if not os.path.exists(self.path):
            async with aiofiles.open(self.path, 'w') as f:
                pass

        self.file = await aiofiles.open(self.path, 'r+')
        return self.file

    current_time = datetime.now()
    last_vote_time = last_vote_times.get(user_id)

        data['votes_count'] += 1
        data['history'].append({"user_id": user_id, "timestamp": datetime.now().isoformat()})

        await f.seek(0)
        await f.write(json.dumps(data, indent=4))
        await f.close()

        logger.info(f"[INFO] User {user_id} has voted. Current votes count: {data['votes_count']}.")
        return embed

            # If the vote threshold has been reached, restart the container asynchronously
            current_votes = await get_votes()
            if current_votes >= VOTES_NEEDED:
                asyncio.create_task(self.handle_container_restart())
        else:
            await interaction.response.send_message("You don't have permission to vote.", ephemeral=True)

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

    async for message in channel.history(limit=MESSAGE_HISTORY_LIMIT):
        if message.id != vote_post_msg_id:  
            await message.delete()

    current_votes = await get_votes()

    if last_restart_time:
        restart_timestamp = int(last_restart_time.timestamp())
        restart_info = f"\n\nLast restarted at: <t:{restart_timestamp}:R>"
    else:
        restart_info = ""

    if vote_post_msg_id:
        try:

        message = await channel.send(embed=embed, view=view)
        vote_post_msg_id = message.id

# Main execution point of the script
if __name__ == '__main__':
    bot.run(TOKEN)
