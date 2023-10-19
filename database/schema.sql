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
