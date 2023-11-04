""""
Copyright © Krypton 2019-2023 - https://github.com/kkrypt0nn (https://krypton.ninja)
Description:
🐍 A simple template to start to code your own and personalized discord bot in Python programming language.

Version: 6.1.0
"""

"""
database schema.sql file:

CREATE TABLE IF NOT EXISTS `warns` (
  `id` int(11) NOT NULL,
  `user_id` varchar(20) NOT NULL,
  `server_id` varchar(20) NOT NULL,
  `moderator_id` varchar(20) NOT NULL,
  `reason` varchar(255) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
);

/*Table of last prompt config(not including prompt and negative_prompt text) from each user*/
CREATE TABLE IF NOT EXISTS `configs` (
  `id` INTEGER PRIMARY KEY,
  `user_id` varchar(20) NOT NULL,
  `config` text NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
);

/*table of saved configs*/
CREATE TABLE IF NOT EXISTS `saved_configs` (
  `user_id` varchar(20) NOT NULL,
  `name` varchar(255) NOT NULL,
  `config` text NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (user_id,name)
);

/*table of user files*/
CREATE TABLE IF NOT EXISTS `files` (
  `user_id` varchar(20) PRIMARY KEY,
  `file` text NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
);

/*table of registered servers*/
CREATE TABLE IF NOT EXISTS `servers` (
  `server_id` varchar(20) PRIMARY KEY,
  `allowed` boolean NOT NULL DEFAULT 0,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
);

/*table of registered channels*/
CREATE TABLE IF NOT EXISTS `channels` (
  `channel_id` varchar(20) PRIMARY KEY,
  `allowed` boolean NOT NULL DEFAULT 0,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""


import aiosqlite
import logging

logger = logging.getLogger('discord_bot')
logger.setLevel(logging.INFO)


class DatabaseManager:
    def __init__(self, *, connection: aiosqlite.Connection) -> None:
        self.connection = connection

    #store a filename with a user_id
    async def add_user_file(self, user_id: int, filename: str) -> None:
        """
        This function will store a filename for a user.

        :param user_id: The ID of the user.
        :param filename: The filename of the user.
        """
        await self.connection.execute(
            "INSERT OR REPLACE INTO files(user_id, file) VALUES (?, ?)",
            (
                user_id,
                filename,
            ),
        )
        await self.connection.commit()
        
    #get most recent filename for user
    async def get_user_file(self,user_id: int) -> str:
        """
        This function will get the filename for a user.

        :param user_id: The ID of the user.
        :return: The filename of the user.
        """
        rows = await self.connection.execute(
            "SELECT file FROM files WHERE user_id=? LIMIT 1",
            (
                user_id,
            ),
        )
        async with rows as cursor:
            result = await cursor.fetchone()
            return result[0] if result is not None else ""

    async def store_config(self, user_id: int, config: dict) -> None:
        """
        This function will store the config for a user.

        :param user_id: The ID of the user.
        :param config: The config of the user.
        """
        await self.connection.execute(
            "INSERT INTO configs(user_id, config) VALUES (?, ?)",
            (
                user_id,
                str(config),
            ),
        )
        await self.connection.commit()
        
    #get the last used config for the user, the config will be returned as a python object
    async def get_config(self,user_id: int) -> dict:
        """
        This function will get the config for a user.

        :param user_id: The ID of the user.
        :return: The config of the user.
        """
        rows = await self.connection.execute(
            "SELECT config FROM configs WHERE user_id=? ORDER BY id DESC LIMIT 1",
            (
                user_id,
            ),
        )
        async with rows as cursor:
            result = await cursor.fetchone()
            return eval(result[0]) if result is not None else {}
        
    #save current config to slot in database
    async def save_config(self,user_id: int,name: str,config: dict) -> None:
        """
        This function will save the config for a user.

        :param user_id: The ID of the user.
        :param name: The name of the config.
        :param config: The config of the user.
        """
        await self.connection.execute(
            "INSERT OR REPLACE INTO saved_configs(user_id,name,config) VALUES (?, ?, ?)",
            (
                user_id,
                name,
                str(config),
            ),
        )
        await self.connection.commit()
    
    #get the saved config for the user, the config will be returned as a python object
    async def get_saved_config(self,user_id: int,name: str) -> dict:
        """
        This function will get the saved config for a user.

        :param user_id: The ID of the user.
        :param name: The name of the config.
        :return: The config of the user.
        """
        rows = await self.connection.execute(
            "SELECT config FROM saved_configs WHERE user_id=? AND name=?",
            (
                user_id,
                name,
            ),
        )
        async with rows as cursor:
            result = await cursor.fetchone()
            return eval(result[0]) if result is not None else {}
    
    async def get_config_list(self,user_id: int) -> list:
        """
        This function will get the config list for a user.

        :param user_id: The ID of the user.
        :return: The config list of the user.
        """
        rows = await self.connection.execute(
            "SELECT name,config FROM saved_configs WHERE user_id=?",
            (
                user_id,
            ),
        )
        async with rows as cursor:
            result = await cursor.fetchall()
            result_list = []
            for row in result:
                result_list.append(row)
            return result_list
    
    async def delete_config(self,user_id: int,name: str) -> None:
        """
        This function will delete the config for a user.

        :param user_id: The ID of the user.
        :param name: The name of the config.
        """
        await self.connection.execute(
            "DELETE FROM saved_configs WHERE user_id=? AND name=?",
            (
                user_id,
                name,
            ),
        )
        await self.connection.commit()
    
    async def add_warn(
        self, user_id: int, server_id: int, moderator_id: int, reason: str
    ) -> int:
        """
        This function will add a warn to the database.

        :param user_id: The ID of the user that should be warned.
        :param reason: The reason why the user should be warned.
        """
        rows = await self.connection.execute(
            "SELECT id FROM warns WHERE user_id=? AND server_id=? ORDER BY id DESC LIMIT 1",
            (
                user_id,
                server_id,
            ),
        )
        async with rows as cursor:
            result = await cursor.fetchone()
            warn_id = result[0] + 1 if result is not None else 1
            await self.connection.execute(
                "INSERT INTO warns(id, user_id, server_id, moderator_id, reason) VALUES (?, ?, ?, ?, ?)",
                (
                    warn_id,
                    user_id,
                    server_id,
                    moderator_id,
                    reason,
                ),
            )
            await self.connection.commit()
            return warn_id

    async def remove_warn(self, warn_id: int, user_id: int, server_id: int) -> int:
        """
        This function will remove a warn from the database.

        :param warn_id: The ID of the warn.
        :param user_id: The ID of the user that was warned.
        :param server_id: The ID of the server where the user has been warned
        """
        await self.connection.execute(
            "DELETE FROM warns WHERE id=? AND user_id=? AND server_id=?",
            (
                warn_id,
                user_id,
                server_id,
            ),
        )
        await self.connection.commit()
        rows = await self.connection.execute(
            "SELECT COUNT(*) FROM warns WHERE user_id=? AND server_id=?",
            (
                user_id,
                server_id,
            ),
        )
        async with rows as cursor:
            result = await cursor.fetchone()
            return result[0] if result is not None else 0

    async def get_warnings(self, user_id: int, server_id: int) -> list:
        """
        This function will get all the warnings of a user.

        :param user_id: The ID of the user that should be checked.
        :param server_id: The ID of the server that should be checked.
        :return: A list of all the warnings of the user.
        """
        rows = await self.connection.execute(
            "SELECT user_id, server_id, moderator_id, reason, strftime('%s', created_at), id FROM warns WHERE user_id=? AND server_id=?",
            (
                user_id,
                server_id,
            ),
        )
        async with rows as cursor:
            result = await cursor.fetchall()
            result_list = []
            for row in result:
                result_list.append(row)
            return result_list
        
    async def get_registered_servers(self) -> list:
        #get the list of registered server ids that are allowed
        rows = await self.connection.execute(
            "SELECT server_id FROM servers WHERE allowed=?",
            (
                True,
            ),
        )
        async with rows as cursor:
            result = await cursor.fetchall()
            result_list = []
            for row in result:
                row = int(row[0])
                result_list.append(str(row))
            return result_list
        

    async def register_server(self, server_id: str, allowed: bool) -> None:
        #register a server
        await self.connection.execute(
            "INSERT OR REPLACE INTO servers(server_id, allowed) VALUES (?, ?)",
            (
                server_id,
                allowed,
            ),
        )
        await self.connection.commit()
        
    async def get_registered_channels(self) -> list:
        #get the list of registered channel ids that are allowed
        rows = await self.connection.execute(
            "SELECT channel_id FROM channels WHERE allowed=?",
            (
                True,
            ),
        )
        async with rows as cursor:
            result = await cursor.fetchall()
            result_list = []
            for row in result:
                #format the row to be an int
                row = int(row[0])
                result_list.append(str(row))
            return result_list
        
        
    async def register_channel(self, channel_id: str, allowed: bool) -> None:
        #register a channel
        await self.connection.execute(
            "INSERT OR REPLACE INTO channels(channel_id, allowed) VALUES (?, ?)",
            (
                channel_id,
                allowed,
            ),
        )
        await self.connection.commit()