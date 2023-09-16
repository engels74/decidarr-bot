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

# Initialize the Docker client to communicate with the Docker daemon
client = docker.DockerClient(base_url=DOCKER_SOCKET_PROXY_URL)