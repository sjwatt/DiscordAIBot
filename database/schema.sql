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