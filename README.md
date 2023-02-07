# MUDCord

Multi-User Dungeon implemented within Discord

## Dungeon configuration

Everything is still very subject to change, but as of 7 Feb 2023, here's the file layout:

```
/main.py, /dungeon.py - Le code
/config.py - You'll need to create this, and provide it with the following variables:
	`home_server_id`: Numeric ID of the server you want the bot to run in
	`bot_token`: Discord bot token
/dungeon - Folder structure where dungeon data is stored
/dungeon/rooms/*.json - .json files representing rooms in the dungeon
/dungeon/users/*.json - .json files representing user clients
```