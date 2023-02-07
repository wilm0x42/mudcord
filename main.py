#!/usr/bin/env python3

import discord
import discord.ext

import config
from dungeon import Dungeon

class MUDClient(discord.Client):
	dungeon = None
	
	def __init__(self, *, intents: discord.Intents):
		super().__init__(intents=intents)
		
		self.tree = discord.app_commands.CommandTree(self)
	
	async def load_dungeon(self):
		self.dungeon = Dungeon()
		
		await self.dungeon.load_rooms()
		await self.dungeon.load_user_clients(self)
		
		print("Finished loading dungeon")
	
	def get_user_client(self, user, channel):
		if self.dungeon == None:
			return None
		
		for user_client in self.dungeon.user_clients:
			if user_client.channel == channel and user_client.user == user:
				return user_client
		
		return None
	
	async def setup_hook(self):
		self.tree.copy_global_to(guild=home_guild)
		await self.tree.sync(guild=home_guild)

intents = discord.Intents.default()
intents.messages = True
intents.emojis = True
intents.members = True
intents.message_content = True

home_guild = discord.Object(config.home_server_id)

client = MUDClient(intents=intents)

@client.event
async def on_ready():
	print(f"Logged in as {client.user} (ID: {client.user.id})")
	
	await client.load_dungeon()

@client.event
async def on_message(message):
	"""
	Determines if this message belongs in the dungeon environment,
	and if so, passes the message along to the dungeon.
	"""
	
	if client.dungeon == None:
		return

	speaking_user = client.get_user_client(message.author, message.channel)
	
	# TODO: It'd be cool if we could let admin users still be able to talk in user channels arbitrarily
	# and have it get echoed to other users
	
	if speaking_user == None:
		return
	
	await client.dungeon.user_talk(speaking_user, message)

@client.tree.command()
async def go(interaction: discord.Interaction, destination: str):
	"""
	Attempts to move user to a connected room
	"""
	
	if client.dungeon == None:
		return
	
	user_client = client.get_user_client(interaction.user, interaction.channel)
	
	if user_client == None:
		await interaction.response.send_message("Error: This isn't your client channel!")
		return
	
	leaving_from_room = user_client.current_room
	
	if destination in client.dungeon.rooms[user_client.current_room].exits:
		user_client.current_room = client.dungeon.rooms[user_client.current_room].exits[destination]
		
		new_room_description = await client.dungeon.describe_room_for_user(user_client)
		new_room_exits = await client.dungeon.describe_exits_for_user(user_client)
		new_room_users = await client.dungeon.describe_other_users_in_room(user_client)
		movement_message = f"You go {destination} and arrive in a new location..."
	
		await interaction.response.send_message(
			movement_message,
			embeds=[
				new_room_description,
				new_room_exits,
				new_room_users
			]
		)
	
		await client.dungeon.user_leave_room(user_client, leaving_from_room, destination)
		await client.dungeon.user_enter_room(user_client, leaving_from_room)
	
	else:
		exits_embed = await client.dungeon.describe_exits_for_user(user_client)
		error_message = f"`{destination}` is not a valid exit in your current location."
		
		await interaction.response.send_message(error_message, embed=exits_embed)

@client.tree.command()
async def look(interaction: discord.Interaction):
	"""
	Recaps to the user information about the room they're in
	"""
	
	if client.dungeon == None:
		return
	
	user_client = client.get_user_client(interaction.user, interaction.channel)
	
	if user_client == None:
		await interaction.response.send_message("Error: This isn't your client channel!")
		return
	
	room_description = await client.dungeon.describe_room_for_user(user_client)
	room_exits = await client.dungeon.describe_exits_for_user(user_client)
	room_users = await client.dungeon.describe_other_users_in_room(user_client)
	
	await interaction.response.send_message(
		embeds=[
			room_description,
			room_exits,
			room_users
		]
	)

client.run(config.bot_token)