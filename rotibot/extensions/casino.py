import rotibot.storage as store
import typing as t

import hikari
import lightbulb

casino_plugin = lightbulb.Plugin("Casino", "Casino plugin for RotiBot")


@casino_plugin.command
@lightbulb.option(
    "target", "The member's balance to be displayed.", hikari.User, required=False
)
@lightbulb.command("balance", "Display user's current balance")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def balance(ctx: lightbulb.Context) -> None:
    target = ctx.get_guild().get_member(ctx.options.target or ctx.user)

    if not target:
        await ctx.respond("That user is not in the server")
        return

    # Read in user data from CSV file
    users = store.read_csv()
    target_id = str(target.id)

    # Check if target ID is in database, if not, make a new user and print default balance value
    if target_id not in users.keys():
        await make_account(target, users)
        await ctx.respond(f"{target.mention}, you currently have 10,000 points.")
    else:
        # Retrieve balance from users dict
        target_balance = users[target_id]["balance"]
        await ctx.respond(
            f"{target.mention}, you currently have {formatBalance(target_balance)} points."
        )


"""
Function to create a new entry for a new user
"""


async def make_account(user: hikari.Member, users: t.Any):
    # Create new dictionary entry for the new user
    users[user.id] = {"username": user.display_name, "balance": 10000}

    # Write updated dictionary to CSV file
    store.write_csv(users)


"""
Used to format numbers for better readability
"""


def formatBalance(balance):
    formattedBalance = "{:,}".format(balance)
    return formattedBalance


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(casino_plugin)
