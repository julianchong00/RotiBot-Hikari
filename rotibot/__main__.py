from code import interact
import os
from pathlib import Path

import aiohttp
import hikari
import lightbulb
from dotenv import load_dotenv
from lightbulb.ext import tasks

import rotibot.database as db

load_dotenv()
env_path = Path("..") / ".env"
load_dotenv(dotenv_path=env_path)

bot = lightbulb.BotApp(
    token=os.getenv("TOKEN"),
    prefix="!",
    intents=hikari.Intents.ALL,
    # default_enabled_guilds=int(os.getenv("GUILD_ID")),
    help_slash_command=True,
)


@bot.listen()
async def on_starting(event: hikari.StartingEvent) -> None:
    channel = await bot.rest.fetch_channel(os.getenv("STDOUT_CHANNEL_ID"))
    db.loadAllUsers()
    await channel.send("Rotibot has been started!")
    bot.d.aio_session = aiohttp.ClientSession()


@bot.listen()
async def on_stopping(event: hikari.StoppingEvent) -> None:
    await bot.d.aio_session.close()


# Global Error Handler
@bot.listen(lightbulb.CommandErrorEvent)
async def on_error(event: lightbulb.CommandErrorEvent) -> None:
    exception = event.exception.__cause__ or event.exception
    if isinstance(exception, lightbulb.CommandIsOnCooldown):
        commandName = await get_command_name(event.context.interaction)

        await event.context.respond(
            f"{event.context.author.mention}, {commandName} command is on cooldown for {exception.retry_after:,.0f} seconds."
        )
    elif isinstance(exception, lightbulb.MissingRequiredPermission):
        commandName = await get_command_name(event.context.interaction)

        await event.context.respond(
            f"{event.context.author.mention}, you do not have the required permissions to run {commandName} command."
        )
    elif isinstance(exception, lightbulb.CommandInvocationError):
        commandName = await get_command_name(event.context.interaction)

        await event.context.respond(
            f"{event.context.author.mention}, something went wrong during invocation of command {commandName}."
        )
    else:
        raise exception


# Function to check for subcommand in interaction
async def get_command_name(interaction: hikari.CommandInteraction) -> str:
    isSubCommand = False
    interaction_options = interaction.options

    if len(interaction_options) > 0:
        for option in interaction_options:
            if option.type == hikari.OptionType.SUB_COMMAND:
                isSubCommand = True
                break

    if isSubCommand:
        return interaction_options[0].name
    else:
        return interaction.command_name


tasks.load(bot)
bot.load_extensions_from("./rotibot/extensions", must_exist=True)


if __name__ == "__main__":
    if os.name != "nt":
        import uvloop

        uvloop.install()
    bot.run()
