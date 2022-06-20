import logging
import os
import typing as t
from pathlib import Path

import hikari
import lavasnek_rs
import lightbulb
from dotenv import load_dotenv

load_dotenv()
env_path = Path("..") / ".env"
load_dotenv(dotenv_path=env_path)

music_plugin = lightbulb.Plugin("Music", "Music plugin for RotiBot")


@music_plugin.command
@lightbulb.command("music", "Music commands for rotibot")
@lightbulb.implements(lightbulb.SlashCommandGroup, lightbulb.PrefixCommandGroup)
async def music_group(ctx: lightbulb.Context) -> None:
    pass


"""
Handles events from the Lavalink server
"""


class EventHandler:
    async def track_start(
        self, _: lavasnek_rs.Lavalink, event: lavasnek_rs.TrackStart
    ) -> None:
        logging.info(f"Track started on guild: {event.guild_id}")

    async def track_finish(
        self, _: lavasnek_rs.Lavalink, event: lavasnek_rs.TrackFinish
    ) -> None:
        logging.info(f"Track finished on guild: {event.guild_id}")

    async def track_exception(
        self, lavalink: lavasnek_rs.Lavalink, event: lavasnek_rs.TrackException
    ) -> None:
        logging.warning(f"Track exception event happened on guild: {event.guild_id}")

        # If a track was not able to be played, skip it
        skip = await lavalink.skip(event.guild_id)
        node = await lavalink.get_guild_node(event.guild_id)

        if not node:
            return

        if skip and not node.queue and not node.now_playing:
            await lavalink.stop(event.guild_id)


"""
Join voice channel function
"""


async def _join(ctx: lightbulb.Context) -> t.Optional[hikari.Snowflake]:
    assert ctx.guild_id is not None

    # Finds voice channel that the command user is currently in
    states = music_plugin.bot.cache.get_voice_states_view_for_guild(ctx.guild_id)
    voice_state = [
        state
        async for state in states.iterator().filter(lambda i: i.user_id == ctx.user.id)
    ]

    if not voice_state:
        await ctx.respond("Connect to a voice channel first.")
        return None

    channel_id = voice_state[0].channel_id

    assert ctx.guild_id is not None

    # Update voice state for this bot, and join a channel deafened
    await music_plugin.bot.update_voice_state(ctx.guild_id, channel_id, self_deaf=True)
    connection_info = (
        await music_plugin.bot.d.lavalink.wait_for_full_connection_info_insert(
            ctx.guild_id
        )
    )

    await music_plugin.bot.d.lavalink.create_session(connection_info)
    return channel_id


"""
Event that is triggered when the Hikari gateway is ready
"""


@music_plugin.listener(hikari.ShardReadyEvent)
async def start_lavalink(event: hikari.ShardReadyEvent) -> None:
    builder = (
        lavasnek_rs.LavalinkBuilder(event.my_user.id, os.getenv("TOKEN"))
        .set_host(os.getenv("LAVALINK_HOST"))
        .set_password(os.getenv("LAVALINK_PASSWORD"))
    )

    builder.set_start_gateway(False)

    # Initialise Lavalink client and provide event handler class
    lava_client = await builder.build(EventHandler())

    music_plugin.bot.d.lavalink = lava_client


"""
Joins the voice channel which the user is in
"""


@music_group.child
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.command("join", "Joins the voice channel you are in.")
@lightbulb.implements(lightbulb.PrefixSubCommand, lightbulb.SlashSubCommand)
async def join(ctx: lightbulb.Context) -> None:
    channel_id = await _join(ctx)

    if channel_id:
        await ctx.respond(f"Joined <#{channel_id}>")


"""
Leaves the voice channel that the bot is in, clearing the queue
"""


@music_group.child
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.command(
    "leave", "Leaves the voice channel the bot is in, clearing the queue."
)
@lightbulb.implements(lightbulb.PrefixSubCommand, lightbulb.SlashSubCommand)
async def leave(ctx: lightbulb.Context) -> None:
    await music_plugin.bot.d.lavalink.destroy(ctx.guild_id)

    if ctx.guild_id is not None:
        await music_plugin.bot.update_voice_state(ctx.guild_id, None)
        await music_plugin.bot.d.lavalink.wait_for_connection_info_remove(ctx.guild_id)

    await music_plugin.bot.d.lavalink.remove_guild_node(ctx.guild_id)
    await music_plugin.bot.d.lavalink.remove_guild_from_loops(ctx.guild_id)

    await ctx.respond("Left voice channel")


"""
Search the query on YouTube, or adds the URL to the queue
"""


@music_group.child
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.option(
    "query",
    "The query to search for.",
    modifier=lightbulb.OptionModifier.CONSUME_REST,
    required=True,
)
@lightbulb.command(
    "play", "Searches the query on YouTube, or adds the URL to the queue."
)
@lightbulb.implements(lightbulb.PrefixSubCommand, lightbulb.SlashSubCommand)
async def play(ctx: lightbulb.Context) -> None:
    query = ctx.options.query

    if not query:
        await ctx.respond("Please specify a query.")
        return

    connection = music_plugin.bot.d.lavalink.get_guild_gateway_connection_info(
        ctx.guild_id
    )

    # Join the users's voice channel if not already in a channel
    if not connection:
        await _join(ctx)

    # Search the query, auto_search will get the track from a URL if possible,
    # otherwise, search the query on YouTube
    query_info = await music_plugin.bot.d.lavalink.auto_search_tracks(query)

    if not query_info.tracks:
        await ctx.respond("Could not find any video of the search query specified.")
        return

    try:
        await music_plugin.bot.d.lavalink.play(
            ctx.guild_id, query_info.tracks[0]
        ).requester(ctx.user.id).queue()
    except lavasnek_rs.NoSessionPresent:
        await ctx.respond(f"Use `!join` first")
        return

    await ctx.respond(f"Added to queue: {query_info.tracks[0].info.title}")


"""
Stops the current song playing
"""


@music_group.child
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.command("stop", "Stops the current song playing.")
@lightbulb.implements(lightbulb.PrefixSubCommand, lightbulb.SlashSubCommand)
async def stop(ctx: lightbulb.Context) -> None:
    await music_plugin.bot.d.lavalink.stop(ctx.guild_id)
    await ctx.respond("Stopped playing")


"""
Skips the current song
"""


@music_group.child
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.command("skip", "Skips the current song.")
@lightbulb.implements(lightbulb.PrefixSubCommand, lightbulb.SlashSubCommand)
async def skip(ctx: lightbulb.Context) -> None:
    """Skips the current song."""

    skip = await music_plugin.bot.d.lavalink.skip(ctx.guild_id)
    node = await music_plugin.bot.d.lavalink.get_guild_node(ctx.guild_id)

    if not skip:
        await ctx.respond("Nothing to skip")
    else:
        # If the queue is empty, the next track won't start playing (because there isn't any),
        # so we stop the player.
        if not node.queue and not node.now_playing:
            await music_plugin.bot.d.lavalink.stop(ctx.guild_id)

        await ctx.respond(f"Skipped: {skip.track.info.title}")


@music_group.child
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.command("pause", "Pauses the current song.")
@lightbulb.implements(lightbulb.PrefixSubCommand, lightbulb.SlashSubCommand)
async def pause(ctx: lightbulb.Context) -> None:
    """Pauses the current song."""

    await music_plugin.bot.d.lavalink.pause(ctx.guild_id)
    await ctx.respond("Paused player")


@music_group.child
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.command("resume", "Resumes playing the current song.")
@lightbulb.implements(lightbulb.PrefixSubCommand, lightbulb.SlashSubCommand)
async def resume(ctx: lightbulb.Context) -> None:
    """Resumes playing the current song."""

    await music_plugin.bot.d.lavalink.resume(ctx.guild_id)
    await ctx.respond("Resumed player")


@music_group.child
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.command(
    "nowplaying", "Gets the song that's currently playing.", aliases=["np"]
)
@lightbulb.implements(lightbulb.PrefixSubCommand, lightbulb.SlashSubCommand)
async def now_playing(ctx: lightbulb.Context) -> None:
    """Gets the song that's currently playing."""

    node = await music_plugin.bot.d.lavalink.get_guild_node(ctx.guild_id)

    if not node or not node.now_playing:
        await ctx.respond("Nothing is playing at the moment.")
        return

    # for queue, iterate over `node.queue`, where index 0 is now_playing.
    await ctx.respond(f"Now Playing: {node.now_playing.track.info.title}")


@music_group.child
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.add_checks(lightbulb.owner_only)  # Optional
@lightbulb.option(
    "args",
    "The arguments to write to the node data.",
    required=False,
    modifier=lightbulb.OptionModifier.CONSUME_REST,
)
@lightbulb.command("data", "Load or read data from the node.")
@lightbulb.implements(lightbulb.PrefixSubCommand, lightbulb.SlashSubCommand)
async def data(ctx: lightbulb.Context) -> None:
    """Load or read data from the node.
    If just `data` is ran, it will show the current data, but if `data <key> <value>` is ran, it
    will insert that data to the node and display it."""

    node = await music_plugin.bot.d.lavalink.get_guild_node(ctx.guild_id)

    if not node:
        await ctx.respond("No node found.")
        return None

    if args := ctx.options.args:
        args = args.split(" ")

        if len(args) == 1:
            node.set_data({args[0]: args[0]})
        else:
            node.set_data({args[0]: args[1]})
    await ctx.respond(node.get_data())


@music_plugin.listener(hikari.VoiceStateUpdateEvent)
async def voice_state_update(event: hikari.VoiceStateUpdateEvent) -> None:
    music_plugin.bot.d.lavalink.raw_handle_event_voice_state_update(
        event.state.guild_id,
        event.state.user_id,
        event.state.session_id,
        event.state.channel_id,
    )


@music_plugin.listener(hikari.VoiceServerUpdateEvent)
async def voice_server_update(event: hikari.VoiceServerUpdateEvent) -> None:
    await music_plugin.bot.d.lavalink.raw_handle_event_voice_server_update(
        event.guild_id, event.endpoint, event.token
    )


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(music_plugin)
