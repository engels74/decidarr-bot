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

# Set up Discord Intents (used to specify which events the bot should receive)
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='?', intents=intents)

    if last_vote_time and (current_time - last_vote_time).seconds < USER_VOTE_COOLDOWN:
        embed = discord.Embed(title="Vote Feedback", description=f"You can vote again after {USER_VOTE_COOLDOWN - (current_time - last_vote_time).seconds} seconds.", color=0xff0000)  
        return embed

    if last_restart_time and (current_time - last_restart_time).seconds < RESTART_COOLDOWN:
        embed = discord.Embed(title="Vote Feedback", description=f"The container was recently restarted. Please wait {RESTART_COOLDOWN - (current_time - last_restart_time).seconds} seconds before voting again.", color=0xff0000)  
        return embed

        if data['votes_count'] >= VOTES_NEEDED:
            embed = discord.Embed(title="Vote Feedback", description="Container will be restarted due to vote threshold!", color=0x00ff00)
            logger.info("[INFO] Votes have been reset due to reaching the threshold.")
        else:
            embed = discord.Embed(title="Vote Feedback", description=f"Thank you for voting! Current Votes: {data['votes_count']}/{VOTES_NEEDED}", color=0x00ff00)

# Define a custom button for users to vote to restart the container
class VoteButton(discord.ui.Button['VoteView']):  
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.success, label="Vote To Restart", custom_id="vote_btn")

    async def callback(self, interaction: discord.Interaction):
        if any(role.id == TRUSTED_ROLE_ID for role in interaction.user.roles):
            embed = await add_vote(interaction.user.id)
            
            # Immediate interaction response
            await interaction.response.send_message(embed=embed, ephemeral=True)

# Define a custom view to display the vote button
class VoteView(discord.ui.View):  
    def __init__(self):
        super().__init__()
        self.add_item(VoteButton())

# Task loop to clean up old messages from the channel at regular intervals
@tasks.loop(seconds=CLEANUP_INTERVAL)
async def cleanup_messages():
    logger.info("[INFO] Running cleanup messages task.")
    channel = bot.get_channel(VOTE_CHANNEL_ID)
    if not channel:
        return

# Task loop to update the main voting post message at regular intervals
@tasks.loop(seconds=parse_time(os.getenv('UPDATE_POST_INTERVAL', '15s')))
async def update_vote_post():
    logger.info("[INFO] Updating the Discord post.")
    global vote_post_msg_id  

    embed = discord.Embed(
        title=VOTE_TITLE,
        description=f"Current Votes: {current_votes}/{VOTES_NEEDED}\n\nVote by pressing the button below or typing `?vote`.{restart_info}"
    )
    view = VoteView()  

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

# Task loop to reset the vote count at regular intervals
@tasks.loop(seconds=parse_time(os.getenv('RESET_VOTE_INTERVAL', '1h')))
async def reset_vote_timer():
    await reset_votes()