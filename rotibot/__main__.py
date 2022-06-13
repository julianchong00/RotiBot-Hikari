import os

import hikari
import lightbulb
from lightbulb.ext import tasks
import aiohttp

import rotibot.database as db

from dotenv import load_dotenv
from pathlib import Path

load_dotenv()
env_path = Path("..") / ".env"
load_dotenv(dotenv_path=env_path)

bot = lightbulb.BotApp(
    token=os.getenv("TOKEN"),
    prefix="!",
    intents=hikari.Intents.ALL,
    default_enabled_guilds=int(os.getenv("GUILD_ID")),
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


tasks.load(bot)
bot.load_extensions_from("./rotibot/extensions", must_exist=True)


if __name__ == "__main__":
    if os.name != "nt":
        import uvloop

        uvloop.install()
    bot.run()
