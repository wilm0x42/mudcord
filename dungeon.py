
import os
import json

import discord


class Room():
	def __init__(self, room_id, name=None, exits=[], description=None):
		self.id = room_id
		self.exits = exits
		
		if description == None:
			self.description = "A distinctly non-descript area."
		else:
			self.description = description
		
		if name == None:
			self.name = room_id
		else:
			self.name = name

class UserClient():
	# How freaking *dare* python not let me make __init__ async
	async def init(self, bot_client, user_id, channel_id, current_room=None):
		self.user = await bot_client.fetch_user(user_id)
		self.channel = await bot_client.fetch_channel(channel_id)
		self.current_room = current_room
		
		print(f"Loaded UserClient for {self.user.name}")

class Dungeon():
	rooms = {}
	
	async def load_rooms(self):
		"""
		Load room data from dungeon/rooms/*.json
		"""
		
		for room_filename in os.listdir("dungeon/rooms/"):
			if not room_filename.endswith(".json"):
				continue
			
			room_data = json.loads(open("dungeon/rooms/" + room_filename).read())
			
			new_room = Room(
				room_data["id"],
				name=room_data.get("name"),
				exits=room_data.get("exits", []),
				description=room_data.get("description")
			)
			
			self.rooms[room_data["id"]] = new_room
			
			print(f"Loaded Room {room_data['id']} from {room_filename}")
	
	async def load_user_clients(self, bot_client):
		"""
		Loads user data from dungeon/users/*.json
		"""
		
		self.user_clients = []
	
		for user_filename in os.listdir("dungeon/users/"):
			try:
				if not user_filename.endswith(".json"):
					continue
				
				user_data = json.loads(open("dungeon/users/" + user_filename).read())
				
				new_user = UserClient()
				
				await new_user.init(
					bot_client,
					user_data["user_id"],
					user_data["channel_id"],
					user_data.get("current_room")
				)
				
				self.user_clients.append(new_user)
			except KeyError as e:
				print(f"Error loading {user_filename}: {e}")
				continue
	
	async def describe_exits_for_user(self, user):
		"""
		Returns a discord embed decribing the exits of the room the user is currently in
		"""
		
		description = ""
		
		for exit, exit_room in self.rooms[user.current_room].exits.items():
			description += f"{exit}: {self.rooms[exit_room].name}\n"
		
		if description == "":
			return "No obvious exits; you appear to be stuck here."
		
		return discord.Embed(title="Obvious exits", description=description)
	
	async def describe_other_users_in_room(self, user):
		"""
		Returns a discord embed describing what other players are in the
		same room as the given user
		"""
		
		description = ""
		
		for other_user in self.user_clients:
			if other_user == user:
				continue
			if other_user.current_room == user.current_room:
				description += other_user.user.name + "\n"
		
		if description == "":
			description = "You seem to be alone."
		
		return discord.Embed(
			title=f"Other users in {self.rooms[user.current_room].name}",
			description=description
		)
	
	async def describe_room_for_user(self, user):
		"""
		Returns a discord embed describing the room the user is currently in
		"""
		
		title = f"Current location: {self.rooms[user.current_room].name}"
		description = self.rooms[user.current_room].description
		
		return discord.Embed(title=title, description=description)
	
	async def user_talk(self, speaking_user, message):
		"""
		Given a message a user has sent, forward it to other
		users in the same room
		"""
		
		if speaking_user.current_room == None:
			return # We don't want to echo messages from users in the void
		
		speech_message = f"{speaking_user.user.name}: {message.content}"
		
		for hearing_user in self.user_clients:
		
			# Don't let user speaking get echoed in their own client channel
			if hearing_user == speaking_user:
				continue
			
			if hearing_user.current_room == speaking_user.current_room:
				await hearing_user.channel.send(speech_message)
	
	async def user_leave_room(self, leaving_user, leaving_from_room, leaving_direction):
		"""
		Announce to users in leaving_from_room that leaving_user is leaving
		"""
		
		if leaving_user.current_room == None:
			return # lol, lmao
		
		leaving_message = (
			f"{leaving_user.user.name} leaves, going `{leaving_direction}` "
			f"toward `{self.rooms[leaving_user.current_room].name}`"
		)
		leaving_embed = discord.Embed(description=leaving_message)
		
		for staying_user in self.user_clients:
			if staying_user == leaving_user: # Shouldn't matter?
				continue
			
			if staying_user.current_room == leaving_from_room:
				await staying_user.channel.send(embed=leaving_embed)
	
	async def user_enter_room(self, entering_user, entering_from_room):
		"""
		Announce to users in the entering_user's current room
		that they have just entered
		"""
		
		if entering_user.current_room == None:
			return # lol, lmao
		
		entering_room_name = "seemingly nowhere"
		
		if entering_from_room in self.rooms:
			entering_room_name = self.rooms[entering_from_room].name
		
		entering_message = (
			f"{entering_user.user.name} enters from "
			f"{entering_room_name}"
		)
		entering_embed = discord.Embed(description=entering_message)
		
		for present_user in self.user_clients:
			if present_user == entering_user:
				continue
			
			if present_user.current_room == entering_user.current_room:
				await present_user.channel.send(embed=entering_embed)
