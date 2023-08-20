<p align="center">
  <img src="https://i.imgur.com/60D4s3Q.png" width="350">
</p>

# Decidarr Bot

## Introduction
Ever been in a situation where something on a server isn't working quite right, and you wish you could just hit a 'restart' button? Well, that's precisely what the Decidarr Bot does, but with a fun twist!

The Decidarr Bot is designed to allow members of a Discord server to vote for the restart of a Docker container. Once a specified number of votes is reached, the bot triggers a restart for the container. This is particularly useful for community-driven server setups where users can democratically decide when a service needs to be restarted.

But wait, there's more to it:

1. **Safety First:** The bot is smart. If it just restarted the system, it will wait for a while before allowing another restart. This ensures that things don't go haywire with continuous restarts.

2. **Taking Turns:** If you just voted, the bot will ask you to wait a little before you can vote again. This prevents one person from spamming votes.

3. **Keeping Things Tidy:** Like a good helper, the bot cleans up after itself. It won't let the chat room get cluttered with old messages.

4. **Trust is Important:** The bot knows who the trusted members of the chat are. Only these trusted members are allowed to cast a vote.

5. **Staying Informed:** The bot keeps everyone updated. It will regularly post messages showing how many votes have been cast and how many are needed for a restart.

In essence, the Decidarr is like a democratic system for tech management, built right into your chat room. It ensures everyone has a say, operates safely, and keeps everyone informed. 

Keep in mind, it's a work in progress :).

## Installation Guide

### Prerequisites:
- Python (3.8 or newer)

### Steps:

1. Clone the repository:
   ```
   git clone https://github.com/engels74/decidarr-bot.git
   cd ./decidarr-bot
   ```

2. Set up a virtual environment:
   ```
   python3 -m venv venv
   source venv/bin/activate  # On Windows, use: .\venv\Scripts\activate
   ```

3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Copy the `.env.example` to `.env` and configure the necessary environment variables:
   ```
   cp .env.example .env
   nano .env  # Use your preferred text editor
   ```

5. Run the bot:
   ```
   python voteBot.py
   ```

## Docker Guide

You can also run the bot inside a Docker container. Here's how:

1. Copy the `docker-compose.yml.example` to `docker-compose.yml`:
   ```
   cp docker-compose.yml.example docker-compose.yml
   ```

2. Edit the `docker-compose.yml` file if necessary and set the environment variables.

3. Run the bot using Docker Compose:
   ```
   docker-compose up -d
   ```

### Example Docker Compose Configuration:

```yaml
version: "3.9"

services:
  decidarr-bot:
    build: https://github.com/engels74/decidarr-bot.git
    container_name: decidarr-bot
    environment:
      - DISCORD_TOKEN=your_discord_token
      - DOCKER_CONTAINER_NAME=your_container_name
      - VOTE_TITLE=Vote to restart the Docker container!
      - VOTE_CHANNEL_ID=your_channel_id
      - VOTES_NEEDED=3
      - VOTES_DATA_PATH=/app/votes_data/votes.json
      - TRUSTED_ROLE_ID=your_trusted_role_id
      - CLEANUP_INTERVAL=30m
      - DOCKER_SOCKET_PROXY_URL=tcp://docker-socket-proxy:2375
      - MESSAGE_HISTORY_LIMIT=25
      - RESET_VOTE_INTERVAL=1h
      - RESTART_COOLDOWN=1h
      - UPDATE_POST_INTERVAL=10s
      - USER_VOTE_COOLDOWN=1m
    volumes:
      - ./votes_data:/app/votes_data
    depends_on:
      - docker-socket-proxy
    restart: unless-stopped

  docker-socket-proxy:
    container_name: docker-socket-proxy
    image: tecnativa/docker-socket-proxy:latest
    environment:
      - CONTAINERS=1
      - ALLOW_RESTARTS=1
      - POST=1
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    restart: unless-stopped

```

## Environment Variables

Here's a description of all the environment variables that you can set:

- `DISCORD_TOKEN`: The token of your Discord bot.
- `DOCKER_CONTAINER_NAME`: The name of the Docker container you want to restart.
- `DOCKER_SOCKET_PROXY_URL`: The Docker socket proxy URL. Default: `tcp://docker-socket-proxy:2375`
- `MESSAGE_HISTORY_LIMIT`: The number of messages to check in the vote channel's history. Default: `25`
- `TRUSTED_ROLE_ID`: The ID of the role that is allowed to vote.
- `VOTE_CHANNEL_ID`: The ID of the Discord channel where votes will be cast.
- `VOTE_TITLE`: The title for the vote message. Default: `Vote to restart the Docker container!`
- `VOTES_NEEDED`: The number of votes required to restart the container. Default: `3`
- `VOTES_DATA_PATH`: Path to the file where votes are stored. Default: `votes_data/votes.json`
- `USER_VOTE_COOLDOWN`: The cooldown period for users to vote again. Format: `[value][s/m/h]`. Default: `1m`
- `RESTART_COOLDOWN`: The cooldown period after a container restart before votes can be cast again. Format: `[value][s/m/h]`. Default: `1h`
- `CLEANUP_INTERVAL`: The interval for cleaning up messages in the vote channel. Format: `[value][s/m/h]`. Default: `30m`
- `UPDATE_POST_INTERVAL`: The interval for updating the Discord post. Format: `[value][s/m/h]`. Default: `15s`
- `RESET_VOTE_INTERVAL`: The interval for resetting the vote count. Format: `[value][s/m/h]`. Default: `1h`

## License

This project is licensed under the GPLv3 License. See the [LICENSE](LICENSE) file for more details.
