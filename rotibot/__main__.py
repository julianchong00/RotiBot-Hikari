import os

import hikari
import lightbulb
import aiohttp

from rotibot import GUILD_ID, STDOUT_CHANNEL_ID

with open("./secrets/token") as f:
    _token = f.read().strip()

bot = lightbulb.BotApp(
    token=_token,
    prefix="!",
    intents=hikari.Intents.ALL,
    default_enabled_guilds=GUILD_ID,
    help_slash_command=True,
)


@bot.listen()
async def on_starting(event: hikari.StartingEvent) -> None:
    channel = await bot.rest.fetch_channel(STDOUT_CHANNEL_ID)
    await channel.send("Rotibot has been started!")
    bot.d.aio_session = aiohttp.ClientSession()


@bot.listen()
async def on_stopping(event: hikari.StoppingEvent) -> None:
    await bot.d.aio_session.close()


bot.load_extensions_from("./rotibot/extensions", must_exist=True)

# @bot.listen(hikari.StartedEvent)
# async def on_started(event: hikari.StartingEvent) -> None:
#     channel = await bot.rest.fetch_channel(STDOUT_CHANNEL_ID)
#     await channel.send("Hikari-Lightbulb bot has been started!")

if __name__ == "__main__":
    if os.name != "nt":
        import uvloop

        uvloop.install()
    bot.run()
