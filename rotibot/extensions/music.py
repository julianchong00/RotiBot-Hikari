import hikari
import lightbulb

music_plugin = lightbulb.Plugin("Music", "Music plugin of RotiBot")


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(music_plugin)
