create table cookies (guild_id bigint primary key, cookie text not null);
create table guilds (guild_id bigint primary key references cookies(guild_id) on delete cascade, board_id integer not null);
create table users (discord_id bigint unique not null, aoc_id bigint unique not null);
create table langs (id bigint not null references users(discord_id) on delete cascade, day integer not null, lang text not null, UNIQUE(id, day, lang), url text);
create table reminders (channel_id bigint not null, user_id bigint not null, unique (channel_id, user_id));